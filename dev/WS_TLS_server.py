import asyncio
import pathlib
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
    return response


def create_temp_self_signed_cert():
    """ Create a self signed SSL certificate in temporary files for host
        'localhost'

    Returns a tuple containing the certificate file name and the key
    file name.

    It is the caller's responsibility to delete the files after use
    """
    # create a key pair
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "UK"
    cert.get_subject().ST = "London"
    cert.get_subject().L = "London"
    cert.get_subject().O = "myapp"
    cert.get_subject().OU = "myapp"
    cert.get_subject().CN = 'localhost'
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha512')

    # Save certificate in temporary file
    (cert_file_fd, cert_file_name) = tempfile.mkstemp(suffix='.crt', prefix='cert')
    cert_file = os.fdopen(cert_file_fd, 'wb')
    cert_file.write(
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    )
    cert_file.close()

    # Save key in temporary file
    (key_file_fd, key_file_name) = tempfile.mkstemp(suffix='.key', prefix='cert')
    key_file = os.fdopen(key_file_fd, 'wb')
    key_file.write(
        crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    )
    key_file.close()

    # Return file names
    return (cert_file_name, key_file_name)

# async def handler(websocket, path):
#     # Register.
#     connected.add(websocket)
#     try:
#         # Implement logic here.
#         await asyncio.wait([ws.send("Hello!") for ws in connected])
#         await asyncio.sleep(10)
#     finally:
#         # Unregister.
#         connected.remove(websocket)

async def consumer(message):
    await publish_message(message)

async def produce_message():
    await asyncio.sleep(1)
    return "Hello World!"

async def consumer_handler(websocket, path):
    # Asynchronous iteration: iterator yields incoming messages
    async for message in websocket:
        await consumer(message)

async def producer_handler(websocket, path):
    while True:
        message = await produce_message()
        await websocket.send(message)

async def handler(websocket, path):
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


async def hello(websocket, path):
    name = await websocket.recv()
    print(f"< {name}")

    greeting = f"Hello {name}!"
    # await publish_message(greeting)

    await websocket.send(greeting)
    print(f"> {greeting}")

event_loop = asyncio.get_event_loop()

# ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# localhost_pem = pathlib.Path(__file__).with_name("server.crt")
# ssl_context.load_cert_chain(localhost_pem)
# ssl_context.load_cert_chain("server.crt", "server.key")



# # Create the certificate file and key
# _cert_file, _cert_key = create_temp_self_signed_cert()
# # Start the mock server, with an SSL context using our certificate
# ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
# ssl_context.load_cert_chain(_cert_file, _cert_key)

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.verify_mode = ssl.CERT_REQUIRED
ssl_context.load_cert_chain("dev/server.crt", "dev/server.key")
ssl_context.load_verify_locations(cafile="dev/client.crt")


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