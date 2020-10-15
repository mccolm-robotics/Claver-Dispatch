import asyncio
import json
import time

import websockets
from aio_pika import connect, IncomingMessage, ExchangeType
from server.database.Accounts import Accounts

'''
Need to implement message batching and need to implement an ACK system for reading batched responses
'''

class Dashboard:
    def __init__(self):
        self.messageBus = None
        self.task_update_state_values = None
        self.refresh_interval = None
        self.connectionManager = None
        self.agent = None
        self.id = None
        self.connection_db = None
        self.event_loop = None
        self.amqp_url = None
        self.mq_connector = None
        self.uuid = None
        self.websocket = None
        self.state = None
        self.connection = None

    @classmethod
    async def initialize(cls, event_loop, websocket, session_data: dict, handshake_data: dict, mq_connector, connection_db, connectionManager):
        """ Constructor that can be called using the class name instead of the object """
        self = Dashboard()
        self.event_loop = event_loop
        self.websocket = websocket
        self.mq_connector = mq_connector
        self.connection_db = connection_db
        self.connectionManager = connectionManager
        self.messageBus = connectionManager.get_messageBus()
        self.uuid = session_data["uuid"]    # Random UUID generated for the browser session
        self.id = session_data["id"]    # Session ID in MySQL sessions table
        self.user_id = session_data["user_id"]      # User id of user who requested the connection
        self.created_timestamp = session_data["created"]    # Timestamp when the browser session was created
        self.ip_addr = session_data["ip_addr"]
        self.mode = handshake_data["mode"].lower()  # Expected values: admin_dashboard, node_dashboard
        self.agent = handshake_data["agent"].lower()
        if "state" in handshake_data:
            self.state = handshake_data["state"]
            if "refresh" in handshake_data["state"]:
                self.refresh_interval = handshake_data["state"]["refresh"]
        self.amqp_url = "amqp://guest:guest@localhost/"
        await self.notifications(self.on_message)
        self.running = True
        self.task_update_state_values = event_loop.create_task(self.update_state_values())
        return self

    def incoming_message(self, data: dict):
        if "action" in data:
            if "update" in data["action"]:
                if "setting" in data["action"]["update"]:
                    self.update_settings(data["action"]["update"]["setting"])

    def update_settings(self, data):
        if "refresh_interval" in data:
            self.refresh_interval = int(data["refresh_interval"])

    async def update_state_values(self):
        while self.running:
            state_values = self.construct_state()["state_values"]
            await self.websocket.send(json.dumps(state_values))
            await asyncio.sleep(self.refresh_interval)

    def get_agent(self) -> str:
        return self.agent

    def get_state(self):
        return self.state

    def get_uuid(self):
        return self.uuid

    def set_mode(self, mode: str):
        self.mode = mode

    def get_mode(self):
        return self.mode

    def get_header_id(self) -> dict:
        """ Used by messages sent to the RabbitMQ Event Processor module """
        return {"client": {"uuid": self.uuid, "timestamp": time.time(), "mode": self.mode}}

    async def on_message(self, message: IncomingMessage):
        """ Coroutine: receives messages sent to this object instance by RabbitMQ """
        with message.process():
            for header in message.headers:
                content = json.loads(message.headers[header])
                print(f"{header}: {content}")
            try:
                await self.websocket.send(message.body.decode())
            except websockets.ConnectionClosed:
                await self.queue.delete()
                await self.close()
                await asyncio.gather(*asyncio.all_tasks())

    async def notifications(self, callback):
        """
        This function establishes a connection with RabbitMQ and creates a message queue
        :param callback: the function that receives messages sent by RabbitMQ
        :return:
        """
        self.connection = await connect(self.amqp_url, loop=self.event_loop)
        channel = await self.connection.channel()
        await channel.set_qos(prefetch_count=1)
        self.queue = await channel.declare_queue(str(self.uuid), exclusive=True)
        await self.mq_connector.bind_queue_to_exchange(queue=self.queue, exchange="system")
        await self.mq_connector.bind_queue_to_exchange(queue=self.queue, exchange=self.mode)
        self.tag = await self.queue.consume(callback)

    def construct_state(self) -> dict:
        """ Provides state information to the Claver Dashboard Web Portal """
        state_values = {}
        if self.mode == "admin_dashboard":
            state_values = {}
            client_dict = self.connectionManager.get_client_dict()
            set_of_connected_nodes = self.connectionManager.get_connected_nodes()
            nodes_online = len(set_of_connected_nodes)
            if nodes_online > 0:
                for websocket in iter(set_of_connected_nodes):
                    state_values[str(client_dict[websocket].get_claver_id())] = client_dict[websocket].get_state_values()
        msg = {"type": "state", "value": state_values}
        return {"external_fulfillment": False, "state_values": msg, "header": None}

    async def close(self):
        """ Part of the closing sequence chain when terminating socket server """
        while True:
            if self.connection is None:
                await asyncio.sleep(1)
            else:
                break
        # await self.queue.delete()
        self.running = False
        self.task_update_state_values.cancel()
        await self.connection.close()
        print("\tClosed Connection to Rabbit")
        await self.connection_db.delete_dashboard_session(self.id)

"""
Resources: awaiting class initialization (asyncio)
https://stackoverflow.com/questions/33128325/how-to-set-class-attribute-with-await-in-init
"""