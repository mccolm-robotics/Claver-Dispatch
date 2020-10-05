import asyncio
import json
import time

import websockets
from aio_pika import connect, IncomingMessage, ExchangeType
from server.database.Accounts import Accounts

'''
Need to implement message batching and need to implement an ACK system for reading batched responses
'''

class Browser:
    @classmethod
    async def create(cls, event_loop, websocket, session_data: dict, mq_connector):
        self = Browser()
        self.event_loop = event_loop
        self.websocket = websocket
        self.mq_connector = mq_connector
        self.mode = "whiteboard"
        self.uuid = session_data["uuid"]    # Random UUID generated for the browser session
        self.id = session_data["id"]    # Session ID in MySQL sessions table
        self.user_id = session_data["user_id"]      # User id of user who requested the connection
        self.created_timestamp = session_data["created"]    # Timestamp when the browser session was created
        self.connection = None

        self.amqp_url = "amqp://guest:guest@localhost/"
        await self.notifications(self.on_message)
        return self

    def get_uuid(self):
        return self.uuid

    def set_mode(self, mode: str):
        self.mode = mode

    def get_header_id(self) -> dict:
        return {"client": {"uuid": self.uuid, "timestamp": time.time(), "mode": self.mode}}

    async def on_message(self, message: IncomingMessage):
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
        await self.mq_connector.bind_exchange(queue=self.queue, exchange="system")
        await self.mq_connector.bind_exchange(queue=self.queue, exchange=self.mode)
        self.tag = await self.queue.consume(callback)

    async def close(self):
        while True:
            if self.connection is None:
                await asyncio.sleep(1)
            else:
                break
        # await self.queue.delete()
        await self.connection.close()
        print("\tClosed Connection to Rabbit")

"""
Resources: awaiting class initialization (asyncio)
https://stackoverflow.com/questions/33128325/how-to-set-class-attribute-with-await-in-init
"""