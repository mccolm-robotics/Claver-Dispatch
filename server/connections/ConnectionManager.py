import asyncio
import json

import websockets
from server.connections.User import User
from server.connections.Browser import Browser
from server.database.Sessions import Sessions


class ConnectionManager:

    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.connected_clients = set()  # Unique list (set) of current websockets
        self.client_dict = {}           # Dictionary of user objects
        self.db_sessions = Sessions()

    def get_notification(self, websocket: websockets):
        return self.client_dict[websocket].get_notification()

    def authorized_user(self, websocket):
        return websocket in self.connected_clients

    def attach_user(self, websocket: websockets):
        self.connected_clients.add(websocket)
        self.client_dict[websocket] = User(self.event_loop, websocket)

    def attach_browser(self, websocket: websockets, session_data: dict) -> None:
        self.connected_clients.add(websocket)
        self.client_dict[websocket] = Browser(self.event_loop, websocket, session_data)

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

    async def authenticate_user(self, websocket, message):
        data = json.loads(message)
        if "agent" in data:
            if data["agent"] == "browser":
                # print("browser")
                if "bid" in data and "token" in data:
                    # ToDo: Check length and use regex to confirm valid characters for bid
                    session_data = self.db_sessions.get_session(data["bid"])
                    # print(data["bid"])
                    # ToDo: Check to see if session is already active. Compare request IP to browser IP
                    if session_data:
                        session_data["uuid"] = data["bid"]
                        # print("Browser connected")
                        # ToDo: make sure OTP is valid
                        if data["token"] == "958058":
                            self.attach_browser(websocket, session_data)
                            return True
            elif data["agent"] == "node":
                print("node knocking")
                await websocket.send("granted")
                self.attach_user(websocket)
                return True
        return False


