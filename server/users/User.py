import uuid
from collections import deque
from aio_pika import connect, IncomingMessage
from server.database.Accounts import Accounts

class User:
    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.uuid = uuid.uuid4()
        # Connect to MySQL and get user's ID#
        account = Accounts()
        self.id, self.password = account.get_account("wasmccolm")
        # print("Client connected. ID: {}".format(self.id))
        self.notification_queue = deque()
        event_loop.create_task(self.notifications(self.on_message))

    def get_id(self):
        return self.id

    def get_notification(self):
        try:
            event = self.notification_queue.popleft()
        except IndexError:
            event = ""
        return event

    def on_message(self, message: IncomingMessage):
        with message.process():
            print("Message: {}".format(message.body))


    async def notifications(self, function):
        # Perform connection
        connection = await connect("amqp://guest:guest@localhost/", loop=self.event_loop)

        # Creating a channel
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Declaring queue
        queue = await channel.declare_queue("global")

        # Start listening the queue with name 'task_queue'
        await queue.consume(function)