import asyncio
import uuid

import aio_pika
from aio_pika import connect, Message, ExchangeType, DeliveryMode

class MQConnection:
    def __init__(self, loop):
        self.amqp_url = 'amqp://guest:guest@localhost/'
        self.loop = loop

    def fake_header(self):

        return {
            # Information about the sender
            "client": {"UUID": "d977e2ac-1458-4b23-948f-29fa458bcb21", "user-agent": "rpi-4", "session": "242e3704bcfe215adedad3c0508d0a8f979c3e1c3fbde62cedcab888f723bf4e"},
            # Information about how to configure client connection on server
            "config": {"stream": "draw"},
            # Example of message to be sent as body
            "message": {
                "type": "stroke",
                "brush": "20:black",
                "path": "32:67|38:70|"
            }
        }

    async def publish_message(self, message: str) -> None:
        connection = await connect(self.amqp_url, loop=self.loop)

        routing_key = "events"

        # Creating channel
        channel = await connection.channel()

        events_exchange = await channel.declare_exchange("claver-events", ExchangeType.FANOUT, auto_delete=False, durable=True)

        message_body = Message(bytes(message, "utf-8"), content_type="text/plain", headers=self.fake_header(), delivery_mode=DeliveryMode.PERSISTENT)

        await events_exchange.publish(
            message_body,
            routing_key=routing_key,
        )

        await connection.close()


'''
Resources:

https://aio-pika.readthedocs.io/en/latest/rabbitmq-tutorial/2-work-queues.html#work-queues
https://aio-pika.readthedocs.io/en/latest/quick-start.html?highlight=simple%20get#simple-consumer
'''

