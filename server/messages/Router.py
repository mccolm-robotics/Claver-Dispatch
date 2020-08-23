import asyncio
import json
import websockets
from server.users.UserManager import UserManager
from server.events.EventManager import EventManager
from server.messages.MQConnection import MQConnection

class Router:

    def __init__(self, clientManager: UserManager, eventLoop) -> None:
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