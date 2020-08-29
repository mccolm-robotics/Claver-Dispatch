import asyncio
import json

import websockets
from server.users.User import User
from server.database.Sessions import Sessions


class UserManager:

    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.connected_clients = set()  # Unique list (set) of current websockets
        self.client_dict = {}           # Dictionary of user objects
        self.db_sessions = Sessions()

    def get_notification(self, websocket: websockets):
        return self.client_dict[websocket].get_notification()

    def authorized_user(self, websocket):
        return websocket in self.connected_clients

    def attach_client(self, websocket: websockets):
        self.connected_clients.add(websocket)
        self.client_dict[websocket] = User(self.event_loop, websocket)

    def isClientAttached(self, websocket):
        if websocket in self.connected_clients:
            return True
        return False

    async def detach_client(self, websocket: websockets):
        await self.client_dict[websocket].close()
        self.client_dict.pop(websocket)
        self.connected_clients.remove(websocket)

    def get_client_count(self):
        return len(self.connected_clients)

    def get_connected_clients(self):
        return self.connected_clients

    def authenticate_user(self, websocket, message):
        data = json.loads(message)
        if "agent" in data:
            if data["agent"] == "browser":
                if "cid" in data and "token" in data:
                    # ToDo: Use regex to confirm length and valid characters for cid
                    session_vals = self.db_sessions.get_session(data["cid"])
                    if session_vals:
                        print(session_vals)
                        if data["cid"] == "06904f82-e8bc-11ea-aa8b-7085c2d6de41" and data["token"] == "958058":
                            print("Client authorized")
                            self.attach_client(websocket)
                            return True
        return False


