import asyncio
import json
import uuid

import websockets
from aio_pika import connect, IncomingMessage, ExchangeType
from server.database.Accounts import Accounts

'''
Need to implement message batching and need to implement an ACK system for reading batched responses
'''

class User:
    def __init__(self, event_loop, websocket):
        self.event_loop = event_loop
        self.websocket = websocket
        self.uuid = uuid.uuid4()
        account = Accounts()         # Connect to MySQL and get user's ID#
        self.id, self.password = account.get_account("tester")
        self.connection = None

        self.amqp_url = "amqp://guest:guest@localhost/"
        event_loop.create_task(self.notifications(self.on_message))


    def get_id(self):
        return self.id

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
        while True:
            if self.connection is None:
                await asyncio.sleep(1)
            else:
                break
        # await self.queue.unbind(self.events_exchange)
        # await self.queue.delete()
        await self.connection.close()
        print("\tClosed Connection to Rabbit")