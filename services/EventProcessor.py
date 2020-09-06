import asyncio
import json

from aio_pika import connect, IncomingMessage, DeliveryMode, Message


class EventProcessor:
    def __init__(self):
        self.amqp_url = 'amqp://guest:guest@localhost/'
        self.event_loop = asyncio.get_event_loop()
        self.event_loop.create_task(self.mq_connect())
        self.run()

    async def main(self, message: IncomingMessage):
        headers = {}
        async with message.process():
            if message.headers:
                for header in message.headers:
                    headers[header] = json.loads(message.headers[header])
            body = json.loads(message.body)

            if body["mode"]:
                if body["mode"].lower() != "system":
                    if body["mode"].lower() == "whiteboard":
                        await self.add_to_queue(json.dumps(body), headers, "whiteboard_queue")

    async def mq_connect(self):
        connection = await connect(self.amqp_url, loop=self.event_loop)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue("event_queue", durable=True)
        await queue.consume(self.main)

    async def add_to_queue(self, body, headers: dict, queue_name: str) -> None:
        connection = await connect(self.amqp_url, loop=self.event_loop)
        channel = await connection.channel()
        message_body = Message(
            bytes(body, "utf-8"),
            delivery_mode=DeliveryMode.PERSISTENT,
            headers=headers
        )
        await channel.default_exchange.publish(
            message_body, routing_key=queue_name
        )
        await connection.close()

    def run(self):
        try:
            print("Event Processor: Started")
            self.event_loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            print('Event Processor: Disconnected')
            self.event_loop.stop()  # Changing loop.close() to loop.stop() prevents an exception when there are still running tasks.

if __name__ == "__main__":
        EventProcessor()