import asyncio
import pathlib
import json
import ssl
import websockets

import os
import tempfile

import pika                 # RabbitMQ driver
import mysql.connector      # MySQL driver

from OpenSSL import crypto

connected = set()

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
    response = f" [x] Sent '{message}'"
    print(response)
    connection.close()



async def consumer(message):
    await publish_message(message)

async def produce_message():
    await asyncio.sleep(1)
    return "Hello World!"

async def consumer_handler(websocket, path):
    # Asynchronous iteration: iterator yields incoming messages
    try:
        async for message in websocket:
            print("Message received")
            await consumer(message)
    except websockets.ConnectionClosed:
        print("Consumer: Client Timed Out")

async def producer_handler(websocket, path):
    try:
        while True:
            message = await produce_message()
            await websocket.send(message)
            print("Message sent")
    except websockets.ConnectionClosed:
        print("Producer: Client Timed Out")



async def handler(websocket, path):

    print("Client Connected")
    # Check that consumer_handler is a coroutine and schedule as task
    # Python 3.7+: replace ensure_future() with create_task()
    consumer_task = asyncio.create_task(consumer_handler(websocket, path))

    # Check that producer_handler is a coroutine and schedule as task
    # Python 3.7+: replace ensure_future() with create_task()
    producer_task = asyncio.create_task(producer_handler(websocket, path))

    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()

event_loop = asyncio.get_event_loop()

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.verify_mode = ssl.CERT_REQUIRED
ssl_context.load_cert_chain("server.crt", "server.key")
ssl_context.load_verify_locations(cafile="client.crt")


start_server = websockets.serve(handler, "localhost", 8765, ssl=ssl_context)

server = event_loop.run_until_complete(start_server)

try:
    event_loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    server.close()
    event_loop.run_until_complete(server.wait_closed())
    print('closing event loop')
    event_loop.close()
    # os.remove(_cert_file)
    # os.remove(_cert_key)