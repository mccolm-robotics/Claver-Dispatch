import asyncio
import pika                 # RabbitMQ driver
import mysql.connector      # MySQL driver

class authenticate_user:
    def __init__(self):
        self.cnx = mysql.connector.connect(host='localhost', user='root', password='', database='claver')
        self.user_credentials = self.cnx.cursor(prepared=True)
        self.id = 0
        self.password = 0

    def selectUser(self, username):
        stmt = "SELECT id, password FROM accounts WHERE username = ?"
        self.user_credentials.execute(stmt, (username,))

        for (id, password) in self.user_credentials:
            print("{}, {}".format(id, password))

    def __del__(self):
        self.user_credentials.close()
        self.cnx.close()

async def publish_message(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')
    channel.basic_publish(exchange='', routing_key='hello', body=message)
    print(f" [x] Sent '{message}'")
    connection.close()

async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')

    print(f"Received {message!r} from {addr!r}")
    await publish_message(message)
    print(f"Send: {message!r}")
    writer.write(data)
    await writer.drain()

    print("Close the connection")
    writer.close()

async def main():
    server = await asyncio.start_server(handle_echo, '127.0.0.1', 8888)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

asyncio.run(main())