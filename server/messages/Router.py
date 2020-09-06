import asyncio
import json
from server.connections.ConnectionManager import ConnectionManager
from services.events import EventManager
from server.messages.Bus import Bus

class Router:

    def __init__(self, connectionManager: ConnectionManager, eventLoop) -> None:
        self.connectionManager = connectionManager
        self.messageBus = Bus(eventLoop)

    async def broadcast_connected_users_list(self) -> None:
        count = {"type": "users", "count": self.connectionManager.get_client_count()}
        await self.__broadcast_to_all_message(json.dumps(count))

    async def __broadcast_to_all_message(self, message: str) -> None:
        connected_clients = self.connectionManager.get_connected_clients()
        if connected_clients:  # asyncio.wait doesn't accept an empty list
            await asyncio.wait([user.send(message) for user in connected_clients])

    async def ingest_events(self, websocket, message: str) -> None:
        data = json.loads(message)
        if "mode" in data:
            self.connectionManager.get_client(websocket).set_mode(data["mode"])

        await self.messageBus.add_to_events_queue(
            message,
            self.connectionManager.get_client(websocket).get_header_id())

    async def authenticate_client(self, websocket, message):
        data = json.loads(message)
        if await self.connectionManager.authenticate_client(websocket, data):
            if "mode" in data:
                # await websocket.send(json.dumps(self.eventManager.get_mode_state(data["mode"])))
                await self.messageBus.request_state_update(data["mode"], self.connectionManager.get_client(websocket).get_header_id())
                await self.broadcast_connected_users_list()
                return True
            else:
                print("\tError: Client did not set initial mode")
        return False
