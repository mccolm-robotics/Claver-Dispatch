import json
import cryptography
import pyotp
import websockets
from cryptography.fernet import Fernet

from server.connections.User import User
from server.connections.Browser import Browser
from server.connections.ConnectionDB import ConnectionDB
from server.connections.MQConnector import MQConnector


class ConnectionManager:

    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.connected_clients = set()  # Unique list (set) of current websockets
        self.client_dict = {}           # Dictionary of user objects
        # self.db_sessions = Sessions()
        self.connection_db = ConnectionDB()
        self.mq_connector = MQConnector(event_loop)

    def get_client(self, websocket: websockets):
        return self.client_dict[websocket]

    def authorized_user(self, websocket):
        return websocket in self.connected_clients

    def attach_user(self, websocket: websockets):
        self.connected_clients.add(websocket)
        self.client_dict[websocket] = User(self.event_loop, websocket, self.mq_connector)

    def attach_browser(self, websocket: websockets, session_data: dict) -> None:
        self.connected_clients.add(websocket)
        self.client_dict[websocket] = Browser(self.event_loop, websocket, session_data, self.mq_connector)

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

    async def authorization_handshake(self, websocket: websockets, data: dict):
        await websocket.send(response)

    async def authenticate_client(self, websocket: websockets, data: dict) -> bool:
        if "agent" in data:
            if data["agent"] == "browser":
                print("\tType: Browser")
                if "bid" in data and "token" in data:
                    # ToDo: Check length and use regex to confirm valid characters for bid
                    session_data = self.connection_db.get_browser_session_data(data["bid"])
                    # print(data["bid"])
                    # ToDo: Check to see if session is already active. Compare request IP to browser IP
                    if session_data:
                        session_data["uuid"] = data["bid"]
                        # print("Browser connected")
                        # ToDo: make sure OTP is valid
                        if data["token"] == "958058":
                            print("\tToken: Valid")
                            self.attach_browser(websocket, session_data)
                            return True
                        else:
                             print("\tToken: Rejected")
            elif data["agent"] == "node":
                if "token" in data and "nid" in data and "qdot" in data:
                    # secret_key = pyotp.random_base32(32)

                    public_key = data["qdot"]
                    encrypted_key = self.connection_db.get_node_seed(data["nid"])

                    try:
                        secret_key = Fernet(public_key).decrypt(encrypted_key.encode())
                    except (cryptography.fernet.InvalidToken, TypeError):
                        print("Bad public key")
                        return False

                    token = pyotp.TOTP(secret_key.decode())

                    if token.verify(data["token"]):
                        new_public_key = Fernet.generate_key()      # Rotate the public key
                        reencrypted_key = Fernet(new_public_key).encrypt(secret_key)
                        status = self.connection_db.update_node_seed(data["nid"], reencrypted_key)
                        response = json.dumps({"qdot": new_public_key.decode()})
                        await websocket.send(response)
                        self.attach_user(websocket)
                        return True
                return False
        return False

'''
Resources: pyOTP 
https://github.com/pyauth/pyotp

Resources: Fernet encryption
https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password
https://stackoverflow.com/questions/60912944/unable-to-except-cryptography-fernet-invalidtoken-error-in-python
'''
