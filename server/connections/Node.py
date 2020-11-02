import asyncio
from asyncio.subprocess import PIPE, STDOUT
import json
import uuid
import time
import re
import subprocess
from datetime import datetime

import websockets
from aio_pika import connect, IncomingMessage, ExchangeType
from server.database.Accounts import Accounts

'''
Need to implement message batching and need to implement an ACK system for reading batched responses
'''

class Node:
    def __init__(self):
        self.id = None
        self.connection_db = None
        self.claver_id = None
        self.init_time = None
        self.state = None
        self.agent = None
        self.task_ping = None
        self.event_loop = None
        self.amqp_url = "amqp://guest:guest@localhost/"
        self.websocket = None
        self.connection = None
        self.mq_connector = None
        self.ping = None

    @classmethod
    async def initialize(cls, event_loop, websocket, handshake_data, mq_connector, connection_db):
        """ Constructor that can be called using the class name instead of the object """
        self = Node()
        self.event_loop = event_loop
        self.websocket = websocket
        self.mq_connector = mq_connector
        self.connection_db = connection_db
        self.running = True
        self.agent = handshake_data["agent"]
        self.mode = handshake_data["mode"]
        self.state = handshake_data["state"]
        self.device_id = handshake_data["nid"]
        device_data = await connection_db.get_node_device(self.device_id)
        self.claver_id = device_data["uuid"]
        self.node_id = device_data["node_id"]
        self.device_name = device_data["device_name"]
        self.platform = device_data["platform"]
        self.id = device_data["id"]
        self.init_time = time.time()
        await connection_db.update_node_device_status(1, self.init_time, self.id)
        self.task_ping = event_loop.create_task(self.calculate_ping())
        await self.notifications(self.on_message)
        return self

    def get_claver_id(self):
        """ Returns the unique ID of this client's instance. """
        return self.claver_id

    def get_agent(self) -> str:
        """ Returns the agent value supplied by the client in its authentication message. """
        return self.agent

    async def set_mode(self, mode: str):
        """ Used to set the mode of a client when switching between microservices. """
        if mode != self.mode:
            await self.mq_connector.unbind_queue_from_events_exchange(self.queue, self.mode)
            self.mode = mode
            await self.mq_connector.bind_queue_to_exchange(self.queue, mode)

    async def calculate_ping(self):
        """ Calculates the ping time for the server to connect with the client. """
        while self.running:
            host = self.websocket.remote_address[0]
            # try:
            cmd = f'ping -c 4 -q {host}'
            process = await asyncio.create_subprocess_shell(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
            await process.wait()
            result = await process.stdout.read()
            output = result.decode()
            if "Name or service not known" in output:
                self.ping = "Unreachable"
            else:
                statistic = re.search(r'(\d+\.\d+/){3}\d+\.\d+', output).group(0)
                avg_time = re.findall(r'\d+\.\d+', statistic)[1]
                response_time = float(avg_time)
                self.ping = response_time
            await asyncio.sleep(15)

    def get_header_id(self) -> dict:
        """ This information is included in the header of a RabbitMQ message. This allows any running microservice to
        respond directly to a client's request for information by using the ID included in the header. """
        return {"client": {"uuid": str(self.claver_id), "timestamp": time.time()}}

    async def on_message(self, message: IncomingMessage):
        """ Coroutine: Receives messages from RabbitMQ """
        async with message.process():
            data = json.loads(message.body.decode())
            if "endpoint" in data:
                if data["endpoint"] == "coupler":
                    for message in data["message"]:
                        if message["type"] == "directive":
                            await self.process_directive(message)
                elif data["endpoint"] == "client":
                    await self.send_message_to_client(message.body.decode())
            else:
                await self.send_message_to_client(message.body.decode())

    async def process_directive(self, directive):
        if directive["value"] == "restart":
            await self.send_message_to_client(json.dumps(directive))

    async def send_message_to_client(self, message):
        if self.running:
            try:
                await self.websocket.send(message)
            except websockets.ConnectionClosed:
                await self.close()
                await asyncio.gather(*asyncio.all_tasks())

    async def notifications(self, callback):
        """ Registers queue with RabbitMQ and sets callback for incoming messages """
        self.connection = await connect(self.amqp_url, loop=self.event_loop)
        channel = await self.connection.channel()
        await channel.set_qos(prefetch_count=1)
        self.queue = await channel.declare_queue(str(self.claver_id), exclusive=True)
        await self.mq_connector.bind_queue_to_exchange(queue=self.queue, exchange="system")
        await self.mq_connector.bind_queue_to_exchange(queue=self.queue, exchange=self.mode)
        self.tag = await self.queue.consume(callback)

    def construct_state(self) -> dict:
        """ Called by the StateManager to gather state/display information for a client's interface. """
        # The state_values for a node will depend on the mode it has been set to.
        # Some modes will receive their state_values from the microservices assigned that specific mode
        # Task: Check the current mode to see if it will be assigned values from the Node object. Otherwise, send request out to events server with header.
        msg = {"request": "state", "mode": self.mode}
        return {"external_fulfillment": True, "state_values": msg, "header": self.get_header_id()}

    def get_state_values(self) -> dict:
        """ Returns a dictionary of state values used by the webportal (dashboard module) """
        return {
            "name": "Test",
            "uptime": self.get_uptime(),
            "launcher_ver": self.get_version_string(self.state["launcher_ver"]) if self.state["launcher_ver"] else "Missing",
            "board_ver": self.get_version_string(self.state["board_ver"]) if self.state["board_ver"] else "Missing",
            "ping": self.ping,
            "launcher_branch": self.state["launcher_branch"],
            "board_branch": self.state["board_branch"]
        }

    def get_uptime(self):
        """ Calculates the duration of client's connection to server """
        delta = time.time() - self.init_time  # returns seconds
        days = delta // 86400
        hours = delta // 3600 % 24
        minutes = delta // 60 % 60
        seconds = delta % 60
        output = f"{int(days)}d, {int(hours)}h:{int(minutes)}m:{int(seconds)}s"
        return output

    def get_version_string(self, ver):
        """ Creates a string representation of dictionary-based version information """
        return ver["MAJOR"] + "." + ver["MINOR"] + "." + ver["PATCH"]

    async def close(self):
        """ Called when the client disconnects from the server.

        Jobs:
            1. Closes down running tasks.
            2. Closes the connection to RabbitMQ.
            3. Updates device status in the DB.
        """

        while True:
            if self.connection is None:
                await asyncio.sleep(1)
            else:
                break
        # await self.queue.unbind(self.events_exchange)
        # await self.queue.delete()
        await self.connection.close()
        self.running = False
        self.task_ping.cancel()
        print("\tClosed Connection to Rabbit")
        await self.connection_db.update_node_device_status(0, self.init_time, self.id)


"""
Resources: Ping latency
https://gist.github.com/rivmar/f218d27da8ec32c34362a5e687df400c

Resources: Async shell subprocesses
https://docs.python.org/3/library/asyncio-subprocess.html
https://stackoverflow.com/questions/60793698/get-stream-from-piped-subprocess-in-async-with-python <- Async chaining of shell commands
"""