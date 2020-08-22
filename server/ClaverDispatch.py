import asyncio
import json
import logging
import ssl
import uuid

from aio_pika import connect, IncomingMessage
import websockets
from typing import Tuple
from collections import deque

from server.database.Accounts import Accounts
from server.messageQueue.MQConnection import MQConnection

logging.basicConfig()




class Client:
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

    def __del__(self):

class ClientManager:

    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.connected_clients = set()
        self.client_dict = {}

    def get_notification(self, websocket: websockets):
        return self.client_dict[websocket].get_notification()

    def authenticate(self, connection: websockets) -> bool:
        # If credentials are good
        self.attach_client(connection)
        return True

    def attach_client(self, connection: websockets):
        self.connected_clients.add(connection)
        self.client_dict[connection] = Client(self.event_loop)

    def detach_client(self, connection: websockets):
        self.connected_clients.remove(connection)
        self.client_dict.pop(connection)

    def get_client_count(self):
        return len(self.connected_clients)

    def get_connected_clients(self):
        return self.connected_clients

class EventManager:
    STATE = {"value": 0}

    def __init__(self, clientManager: ClientManager):
        self.clientManager = clientManager

    def state_event(self) -> str:
        return json.dumps({"type": "state", **self.STATE})

    def users_event(self) -> str:
        return json.dumps({"type": "users", "count": self.clientManager.get_client_count()})

    def decode_event(self, data: str) -> Tuple[str, int]:
        if data["action"] == "minus":
            self.STATE["value"] -= 1
            # await self.__broadcast_message(self.state_event())
            return self.state_event(), -1
        elif data["action"] == "plus":
            self.STATE["value"] += 1
            # await self.__broadcast_message(self.state_event())
            return self.state_event(), -1
        else:
            logging.error("Unsupported event: {}", data)

    def get_state(self):
        return self.state_event()


class Router:

    def __init__(self, clientManager: ClientManager, eventLoop) -> None:
        self.clientManager = clientManager
        self.eventManager = EventManager(clientManager)
        self.messageQueue = MQConnection(eventLoop)

    async def broadcast_connected_users_list(self) -> None:
        await self.__broadcast_to_all_message(self.eventManager.users_event())

    async def __broadcast_to_all_message(self, message):
        await self.messageQueue.publish_message(message)
        connected_clients = self.clientManager.get_connected_clients()
        if connected_clients:  # asyncio.wait doesn't accept an empty list
            await asyncio.wait([user.send(message) for user in connected_clients])

    async def ingest_events(self, websocket: websockets, path: str) -> None:
        """LOOP: Receives event messages from a client"""
        # Asynchronous iteration: iterator yields incoming messages
        async for message in websocket:
            # This is an infinite loop
            data = json.loads(message)
            event, target = self.eventManager.decode_event(data)
            if target == -1: # Send to all clients
                # Add to global Rabbit Queue
                await self.__broadcast_to_all_message(event)
            else: # Send to specific client
                # Add to specific user's Rabbit Queue
                await self.__broadcast_to_all_message(event) # Send message to single client

    async def transmit_events(self, websocket: websockets, path: str) -> None:
        while True:
            message = self.clientManager.get_notification(websocket)
            if message:
                await websocket.send(message)
            else:
                await asyncio.sleep(1)

    async def initialize_client_state(self, websocket: websockets, path: str) -> None:
        """Sets the initial state of the application client"""
        # Initialize client with current state of the app
        await websocket.send(self.eventManager.get_state())


class ClaverDispatch:
    def __init__(self, host: str, port: int, server_key: str=None, server_crt: str=None, client_crt: str=None) -> None:
        if server_key and server_crt and client_crt:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.load_cert_chain(server_crt, server_key)
            ssl_context.load_verify_locations(cafile=client_crt)
        else:
            ssl_context = None

        self.event_loop = asyncio.get_event_loop()
        self.clientManager = ClientManager(self.event_loop)
        self.router = Router(self.clientManager, self.event_loop)
        self.start_server = websockets.serve(self.connection_handler, host, port, ssl=ssl_context) # Creates the server
        self.run()

    def run(self) -> None:
        """Starts the server"""
        server = self.event_loop.run_until_complete(self.start_server)
        try:
            print('Server: Started')
            self.event_loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
            self.event_loop.run_until_complete(server.wait_closed())
            print('Server: Disconnected')
            self.event_loop.close()

    async def incoming_events_handler(self, websocket: websockets, path: str) -> None:
        try:
            await self.router.ingest_events(websocket, path)
        except websockets.ConnectionClosed:
            print("Incoming Event -> Stalled: Client Disconnected")

    async def outgoing_events_handler(self, websocket: websockets, path: str) -> None:
        try:
            await self.router.transmit_events(websocket, path)
        except websockets.ConnectionClosed:
            print("Outgoing Event -> Stalled: Client Disconnected")

    async def update_node_map(self) -> None:
        await self.router.broadcast_connected_users_list()

    async def connection_handler(self, websocket: websockets, path: str) -> None:
        """
        Coroutine: Websockets connection handler.
        This function executes the application logic for a single connection and closes the connection when done.
        Function parameters: it receives a WebSocket protocol instance and the URI path
        """
        # Add websocket to list of connected clients
        if self.clientManager.authenticate(websocket):
            await self.update_node_map()
            try:
                await self.router.initialize_client_state(websocket, path)
                incoming_event = asyncio.create_task(self.incoming_events_handler(websocket, path))
                outgoing_event = asyncio.create_task(self.outgoing_events_handler(websocket, path))
                done, pending = await asyncio.wait(
                    [incoming_event, outgoing_event],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
            except websockets.ConnectionClosed:
                # Exception raised when websockets.open() == False
                # Connection is closed. Exit iterator.
                pass
            finally:
                self.clientManager.detach_client(websocket)
                await self.update_node_map()

if __name__ == "__main__":
    ClaverDispatch("localhost", 6789)







"""
Resources: SSL Self-Signed Certificates

https://www.ibm.com/support/knowledgecenter/SSMNED_5.0.0/com.ibm.apic.cmc.doc/task_apionprem_gernerate_self_signed_openSSL.html
https://jamielinux.com/docs/openssl-certificate-authority/create-the-root-pair.html
https://www.electricmonk.nl/log/2018/06/02/ssl-tls-client-certificate-verification-with-python-v3-4-sslcontext/
https://stackoverflow.com/questions/33504746/doing-ssl-client-authentication-is-python
https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl
https://certbot.eff.org/docs/using.html#standalone
https://aliceh75.github.io/testing-asyncio-with-ssl *** Good ***
https://docs.python.org/3/library/ssl.html#module-ssl


Resources: WebSockets

https://websockets.readthedocs.io/en/stable/cheatsheet.html?highlight=handler#passing-additional-arguments-to-the-connection-handler
"""