import asyncio
import json
from server.connections.ConnectionManager import ConnectionManager
from server.events.EventManager import EventManager
from server.messages.MQConnection import MQConnection

class Router:

    def __init__(self, connectionManager: ConnectionManager, eventLoop) -> None:
        self.connectionManager = connectionManager
        self.eventManager = EventManager(connectionManager)
        self.messageQueue = MQConnection(eventLoop)

    async def broadcast_connected_users_list(self) -> None:
        await self.__broadcast_to_all_message(json.dumps(self.eventManager.shim_users()))

    async def __broadcast_to_all_message(self, message: str) -> None:
        connected_clients = self.connectionManager.get_connected_clients()
        if connected_clients:  # asyncio.wait doesn't accept an empty list
            await asyncio.wait([user.send(message) for user in connected_clients])

    async def ingest_events(self, message) -> None:
        data = json.loads(message)
        response = self.eventManager.decode_event(data)
        if not response["error"]:
            if response["target"] == "all":
                # await self.__broadcast_to_all_message(event) # Direct Synchronous message transfer
                await self.messageQueue.publish_message(json.dumps(response["event"]))
        else:
            print(response["error"])

    async def authenticate_client(self, websocket, message):
        data = json.loads(message)
        if await self.connectionManager.authenticate_user(websocket, data):
            if "mode" in data:
                await websocket.send(json.dumps(self.eventManager.get_mode_state(data["mode"])))
                await self.broadcast_connected_users_list()
                return True
            else:
                print("\tError: Client did not set initial mode")
        return False
