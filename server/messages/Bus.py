import asyncio
import json

from aio_pika import connect, Message, ExchangeType, DeliveryMode

class Bus:
    def __init__(self, connectionManager, loop):
        self.amqp_url = 'amqp://guest:guest@localhost/'
        self.loop = loop
        self.connectionManager = connectionManager

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

    async def broadcast_event_update_by_key(self, message: str, key: str) -> None:
        connection = await connect(self.amqp_url, loop=self.loop)
        channel = await connection.channel()
        events_exchange = await channel.declare_exchange("claver.events", auto_delete=False, durable=True)
        message_body = Message(bytes(message, "utf-8"), content_type="text/plain", delivery_mode=DeliveryMode.PERSISTENT)
        await events_exchange.publish(
            message_body,
            routing_key=key,
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

    async def direct_message_broadcast(self, message: str) -> None:
        connected_clients = self.connectionManager.get_connected_clients()
        if connected_clients:  # asyncio.wait doesn't accept an empty list
            await asyncio.wait([user.send(message) for user in connected_clients])

# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#     message_bus = Bus(None, loop)
#     msg = json.dumps({"type": "state", "value": "BOOM!"})
#     loop.run_until_complete(message_bus.broadcast_event_update_by_key(msg, "dashboard"))

'''
Resources:

https://aio-pika.readthedocs.io/en/latest/rabbitmq-tutorial/2-work-queues.html#work-queues
https://aio-pika.readthedocs.io/en/latest/quick-start.html?highlight=simple%20get#simple-consumer
'''

