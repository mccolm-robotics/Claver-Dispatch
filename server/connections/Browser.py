import asyncio
import json
import uuid

import websockets
from aio_pika import connect, IncomingMessage, ExchangeType
from server.database.Accounts import Accounts

'''
Need to implement message batching and need to implement an ACK system for reading batched responses
'''

class Browser:
    def __init__(self, event_loop, websocket, session_data: dict) -> None:
        self.event_loop = event_loop
        self.websocket = websocket
        self.uuid = session_data["uuid"]    # Random UUID generated for the browser session
        self.id = session_data["id"]    # Session ID in MySQL sessions table
        self.user_id = session_data["user_id"]      # User id of user who requested the connection
        self.created_timestamp = session_data["created"]    # Timestamp when the browser session was created

        self.amqp_url = "amqp://guest:guest@localhost/"
        event_loop.create_task(self.notifications(self.on_message))

    async def on_message(self, message: IncomingMessage):
        with message.process():
            for header in message.headers:
                content = json.loads(message.headers[header])
                print(f"{header}: {content}")

            try:
                await self.websocket.send(message.body.decode())
            except websockets.ConnectionClosed:
                await self.close()
                await asyncio.gather(*asyncio.all_tasks())

    async def notifications(self, callback):
        # Perform connection
        self.connection = await connect(self.amqp_url, loop=self.event_loop)

        # Creating a channel
        channel = await self.connection.channel()

        await channel.set_qos(prefetch_count=1)

        self.events_exchange = await channel.declare_exchange("claver-events", ExchangeType.FANOUT, auto_delete=False, durable=True)

        # Declaring temporary queue with auto delete
        self.queue = await channel.declare_queue(exclusive=True)

        await self.queue.bind(self.events_exchange)

        # Start listening the queue (auto generated name)
        self.tag = await self.queue.consume(callback)

    async def close(self):
        await self.queue.unbind(self.events_exchange)
        # await self.queue.delete()
        await self.connection.close()

    def __del__(self):
        # ToDo delete session from MySQL table
        pass