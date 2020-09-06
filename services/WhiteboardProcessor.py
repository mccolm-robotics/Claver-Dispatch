import asyncio
import json

from aio_pika import connect, IncomingMessage, DeliveryMode, Message, ExchangeType
from services.events.WhiteBoard import WhiteBoard


class WhiteboardProcessor:
    def __init__(self):
        self.whiteboard = WhiteBoard()
        self.amqp_url = 'amqp://guest:guest@localhost/'
        self.event_loop = asyncio.get_event_loop()
        self.event_loop.create_task(self.mq_connect())
        self.run()

    async def main(self, message: IncomingMessage):
        details = {}
        async with message.process():
            if message.headers:
                for header in message.headers:
                    details[header] = json.loads(message.headers[header])
            details["body"] = json.loads(message.body)

            print(details)
            if "request" in details["body"]:
                print("Request from {}".format(details["client"]["uuid"]))
                state = json.dumps(self.whiteboard.get_state())
                await self.direct_update(message=state, queue_name=details["client"]["uuid"])
            elif "action" in details["body"]:
                response = self.whiteboard.process_event(details["body"])
                await self.broadcast_update(json.dumps(response))

    async def broadcast_update(self, message: str) -> None:
        connection = await connect(self.amqp_url, loop=self.event_loop)
        channel = await connection.channel()
        events_exchange = await channel.declare_exchange("claver.events", auto_delete=False, durable=True)
        message_body = Message(bytes(message, "utf-8"), content_type="text/plain", delivery_mode=DeliveryMode.PERSISTENT)
        await events_exchange.publish(
            message_body,
            routing_key="whiteboard",
        )
        await connection.close()

    async def direct_update(self, message: str, queue_name: str) -> None:
        connection = await connect(self.amqp_url, loop=self.event_loop)
        channel = await connection.channel()
        message_body = Message(bytes(message, "utf-8"), delivery_mode=DeliveryMode.PERSISTENT)
        await channel.default_exchange.publish(
            message_body,
            routing_key=queue_name
        )
        await connection.close()

    async def mq_connect(self):
        connection = await connect(self.amqp_url, loop=self.event_loop)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue("whiteboard_queue", durable=True)
        await queue.consume(self.main)

    def run(self):
        try:
            print("Whiteboard Processor: Started")
            self.event_loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            print('Whiteboard Processor: Disconnected')
            self.event_loop.stop()  # Changing loop.close() to loop.stop() prevents an exception when there are still running tasks.


if __name__ == "__main__":
    WhiteboardProcessor()