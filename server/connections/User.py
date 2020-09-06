import asyncio
import json
import uuid
import time

import websockets
from aio_pika import connect, IncomingMessage, ExchangeType
from server.database.Accounts import Accounts

'''
Need to implement message batching and need to implement an ACK system for reading batched responses
'''

class User:
    def __init__(self, event_loop, websocket, mq_connector):
        self.event_loop = event_loop
        self.websocket = websocket
        self.mq_connector = mq_connector
        self.mode = "whiteboard"
        self.uuid = uuid.uuid4()
        account = Accounts()         # Connect to MySQL and get user's ID#
        self.id, self.password = account.get_account("tester")
        self.connection = None

        self.amqp_url = "amqp://guest:guest@localhost/"
        event_loop.create_task(self.notifications(self.on_message))

    async def set_mode(self, mode: str):
        if mode != self.mode:
            await self.mq_connector.unbind_exchange(self.queue, self.mode)
            self.mode = mode
            await self.mq_connector.bind_exchange(self.queue, mode)


    def get_header_id(self) -> dict:
        return {"client": {"uuid": str(self.uuid), "timestamp": time.time()}}

    async def on_message(self, message: IncomingMessage):
        async with message.process():
            for header in message.headers:
                content = json.loads(message.headers[header])
                print(f"{header}: {content}")
            try:
                await self.websocket.send(message.body.decode())
            except websockets.ConnectionClosed:
                await self.close()
                await asyncio.gather(*asyncio.all_tasks())

    async def notifications(self, callback):
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
        # await self.queue.unbind(self.events_exchange)
        # await self.queue.delete()
        await self.connection.close()
        print("\tClosed Connection to Rabbit")