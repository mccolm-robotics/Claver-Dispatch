import asyncio

import aio_pika
from aio_pika import connect, Message, connect_robust

class MQConnection:
    def __init__(self, loop):
        self.amqp_url = 'amqp://guest:guest@localhost/'
        self.loop = loop

    async def publish_message(self, message: str) -> None:
        connection = await connect(self.amqp_url, loop=self.loop)

        queue_name = "global"
        routing_key = "global"

        # Creating channel
        channel = await connection.channel()

        # Declaring exchange
        exchange = await channel.declare_exchange("claver", auto_delete=False, durable=True)

        # Declaring queue
        queue = await channel.declare_queue(queue_name, auto_delete=False)

        # Binding queue
        await queue.bind(exchange, routing_key)

        await exchange.publish(
            Message(
                bytes(message, "utf-8"),
                content_type="text/plain",
                headers={"foo": "bar"},
            ),
            routing_key,
        )

        await connection.close()


'''
Resources:

https://aio-pika.readthedocs.io/en/latest/rabbitmq-tutorial/2-work-queues.html#work-queues
https://aio-pika.readthedocs.io/en/latest/quick-start.html?highlight=simple%20get#simple-consumer
'''

