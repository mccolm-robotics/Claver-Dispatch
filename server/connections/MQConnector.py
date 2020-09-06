from aio_pika import connect, ExchangeType

class MQConnector:
    def __init__(self, event_loop):
        self.amqp_url = 'amqp://guest:guest@localhost/'
        self.event_loop = event_loop
        event_loop.create_task(self.initialize_exchanges())
        self.set_of_exchanges = {"system", "whiteboard"}


    async def initialize_exchanges(self):
        connection = await connect(self.amqp_url, loop=self.event_loop)
        channel = await connection.channel()

        self.system_exchange = await channel.declare_exchange("claver.system", ExchangeType.FANOUT, auto_delete=False, durable=True)
        self.events_exchange = await channel.declare_exchange("claver.events", auto_delete=False, durable=True)

        await connection.close()

    def is_valid_exchange(self, event: str) -> bool:
        if event in self.set_of_exchanges:
            return True
        return False


    def __get_exchange(self, name: str):
        if name == "system":
            return self.system_exchange
        else:
            return self.events_exchange

    async def bind_exchange(self, queue, exchange: str):
        if exchange == "system":
            await queue.bind(self.__get_exchange(exchange))
        elif exchange == "whiteboard":
            await queue.bind(self.__get_exchange(exchange), routing_key="whiteboard")
        else:
            print(f"Routing Key {exchange} does not exist for event exchange.")

    async def unbind_exchange(self, queue, exchange: str):
        if self.is_valid_exchange(exchange):
            await queue.unbind(exchange)
        else:
            print(f"Error: Invalid request to unbind queue. Exchange '{exchange}' does not exist.")
