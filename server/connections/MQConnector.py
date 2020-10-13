from aio_pika import connect, ExchangeType

class MQConnector:
    def __init__(self):
        self.amqp_url = 'amqp://guest:guest@localhost/'
        self.event_loop = None

    @classmethod
    async def initialize(cls, event_loop):
        """ Constructor that can be called using the class name instead of the object """
        self = MQConnector()
        self.event_loop = event_loop
        await self.initialize_exchanges()
        return self

    async def initialize_exchanges(self):
        """ Creates exchanges used by client queues """
        connection = await connect(self.amqp_url, loop=self.event_loop)
        channel = await connection.channel()
        self.system_exchange = await channel.declare_exchange("claver.system", ExchangeType.FANOUT, auto_delete=False, durable=True)
        self.events_exchange = await channel.declare_exchange("claver.events", auto_delete=False, durable=True)
        await connection.close()

    def __get_exchange(self, name: str):
        """ Private function that abstracts exchange names """
        if name == "system":
            return self.system_exchange
        else:
            return self.events_exchange

    async def bind_queue_to_exchange(self, queue, exchange: str):
        """ Used by clients attach to the events exchange with a specific routing key """
        if exchange == "system":
            await queue.bind(self.__get_exchange(exchange))
        else:
            await queue.bind(self.__get_exchange("events"), routing_key=exchange)

    async def unbind_queue_from_events_exchange(self, queue):
        """ Called when a client needs to change the routing key attached to the 'events exchange' """
        await queue.unbind(self.__get_exchange("events"))

