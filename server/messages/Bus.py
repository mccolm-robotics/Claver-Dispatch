import json

from aio_pika import connect, Message, ExchangeType, DeliveryMode

class Bus:
    def __init__(self, loop):
        self.amqp_url = 'amqp://guest:guest@localhost/'
        self.loop = loop

    async def broadcast_message(self, message: str) -> None:
        connection = await connect(self.amqp_url, loop=self.loop)
        channel = await connection.channel()
        system_exchange = await channel.declare_exchange("claver.system", ExchangeType.FANOUT, auto_delete=False, durable=True)
        message_body = Message(
            bytes(message, "utf-8"),
            content_type="text/plain",
            delivery_mode=DeliveryMode.PERSISTENT
        )
        await system_exchange.publish(
            message_body,
            routing_key="system"
        )
        await connection.close()

    async def add_to_events_queue(self, message: str, header: dict) -> None:
        connection = await connect(self.amqp_url, loop=self.loop)
        channel = await connection.channel()
        message_body = Message(
            bytes(message, "utf-8"),
            delivery_mode=DeliveryMode.PERSISTENT,
            headers=header
        )
        await channel.default_exchange.publish(
            message_body,
            routing_key="event_queue"
        )
        await connection.close()

    async def direct_message(self, message: str, recipient: str) -> None:
        connection = await connect(self.amqp_url, loop=self.loop)
        channel = await connection.channel()
        message_body = Message(
            bytes(message, "utf-8"),
            delivery_mode=DeliveryMode.PERSISTENT
        )
        await channel.default_exchange.publish(
            message_body,
            routing_key=recipient
        )
        await connection.close()

    async def request_state_update(self, mode: str, header: dict):
        message = json.dumps({"request": "state", "mode": mode})
        await self.add_to_events_queue(message, header)

'''
Resources:

https://aio-pika.readthedocs.io/en/latest/rabbitmq-tutorial/2-work-queues.html#work-queues
https://aio-pika.readthedocs.io/en/latest/quick-start.html?highlight=simple%20get#simple-consumer
'''

