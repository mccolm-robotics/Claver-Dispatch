import asyncio
import json
import websockets
from server.users.UserManager import UserManager
from server.events.EventManager import EventManager
from server.messages.MQConnection import MQConnection

class Router:

    def __init__(self, userManager: UserManager, eventLoop) -> None:
        self.userManager = userManager
        self.eventManager = EventManager(userManager)
        self.messageQueue = MQConnection(eventLoop)

    async def broadcast_connected_users_list(self) -> None:
        await self.__broadcast_to_all_message(self.eventManager.users_event())

    async def __broadcast_to_all_message(self, message):
        connected_clients = self.userManager.get_connected_clients()
        if connected_clients:  # asyncio.wait doesn't accept an empty list
            await asyncio.wait([user.send(message) for user in connected_clients])

    async def ingest_events(self, message) -> None:
        data = json.loads(message)
        event, target = self.eventManager.decode_event(data)
        if target == -1:
            # await self.__broadcast_to_all_message(event) # Direct Synchronous message transfer
            await self.messageQueue.publish_message(event)
        else:
            # await self.__broadcast_to_all_message(event) # Direct Synchronous message transfer
            await self.messageQueue.publish_message(event)

    async def initialize_client_state(self, websocket: websockets) -> None:
        """Sets the initial state of the application client"""
        # Initialize client with current state of the app
        await websocket.send(self.eventManager.get_state())

    async def authenticate_client(self, websocket, message):
        if self.userManager.authenticate_user(websocket, message):
            await self.initialize_client_state(websocket)
            await self.broadcast_connected_users_list()
