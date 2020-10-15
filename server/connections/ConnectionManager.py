import asyncio
import json
from datetime import time

import cryptography
import pyotp
import websockets
from cryptography.fernet import Fernet
from server.connections.Node import Node
from server.connections.Dashboard import Dashboard
from server.connections.ConnectionDB import ConnectionDB
from server.connections.MQConnector import MQConnector


class ConnectionManager:
    def __init__(self):
        self.connection_db = None
        self.mq_connector = None
        self.event_loop = None
        self.messageBus = None
        self.connected_clients = set()  # Unique list (set) of current websockets. This facilitates a quick lookup when confirming a connection's authentication status
        self.connected_nodes = set()
        self.connected_dashboards = {}  # This dictionary groups websocket connections with agent == dashboard by mode. Currently only used in StateManager()
        self.client_dict = {}  # Dictionary of user objects. Each websocket object is the key value that identifies its object instance (defined by the 'agent' value in handshake data)

    @classmethod
    async def initialize(cls, event_loop):
        """ Constructor that can be called using the class name instead of the object """
        self = ConnectionManager()
        self.event_loop = event_loop
        self.connection_db = ConnectionDB(event_loop)
        self.mq_connector = await MQConnector.initialize(event_loop)
        return self

    def set_messageBus(self, messageBus):
        self.messageBus = messageBus

    def get_messageBus(self):
        return self.messageBus

    def get_client(self, websocket: websockets):
        """ Returns single client object linked to websocket object """
        return self.client_dict[websocket]

    def get_client_dict(self) -> dict:
        """ Returns dictionary of client objects keyed by websocket object """
        return self.client_dict

    def get_connected_nodes(self) -> set:
        """ Returns set of connected node objects """
        return self.connected_nodes

    def get_connected_dashboards(self) -> dict:
        """ Returns dict of connected dashboard objects """
        return self.connected_dashboards

    def get_client_count(self) -> int:
        """ Returns count of all websocket connections """
        return len(self.connected_clients)

    def get_connected_clients(self) -> set:
        """ Returns set of all websocket connections """
        return self.connected_clients

    def is_authorized_user(self, websocket) -> bool:
        """ Boolean check for websocket in set of connected websockets """
        return websocket in self.connected_clients

    async def attach_node(self, websocket: websockets, handshake_data):
        """ Adds websocket to records of connected websockets. Adds websocket to set of connected Nodes. """
        self.connected_clients.add(websocket)
        self.connected_nodes.add(websocket)
        self.client_dict[websocket] = await Node.initialize(self.event_loop, websocket, handshake_data, self.mq_connector, self.connection_db)

    async def attach_dashboard(self, websocket: websockets, session_data, handshake_data) -> None:
        """ Adds websocket to dynamic dictionary of client sets. Dictionary is keyed to 'mode' value sent during websocket handshake. """
        self.connected_clients.add(websocket)
        # self.connected_dashboards.add(websocket)
        if handshake_data["mode"].lower() not in self.connected_dashboards:
            self.connected_dashboards[handshake_data["mode"].lower()] = set()
        self.connected_dashboards[handshake_data["mode"].lower()].add(websocket)
        self.client_dict[websocket] = await Dashboard.initialize(self.event_loop, websocket, session_data, handshake_data, self.mq_connector, self.connection_db, self)

    async def detach_client(self, websocket: websockets):
        """ Closes client objects and removes websocket from records of connected websockets """
        await self.client_dict[websocket].close()
        if websocket in self.connected_nodes:
            self.connected_nodes.remove(websocket)
        elif self.client_dict[websocket].get_mode() in self.connected_dashboards:
            # print(f"Detach Client: found websocket mode as key in dashboard dict")
            if websocket in self.connected_dashboards[self.client_dict[websocket].get_mode()]:
                # print(f"Detach Client: Found websocket in set of connected devices for mode {self.client_dict[websocket].get_mode()}")
                self.connected_dashboards[self.client_dict[websocket].get_mode()].remove(websocket)
                if len(self.connected_dashboards[self.client_dict[websocket].get_mode()]) == 0:
                    # print("Detach Client: Removing empty set from dictionary")
                    self.connected_dashboards.pop(self.client_dict[websocket].get_mode())
                    # print(f"Current dict of connected dashboards: {self.connected_dashboards}")
        self.client_dict.pop(websocket)
        self.connected_clients.remove(websocket)

    async def authorization_handshake(self, websocket: websockets, data: dict):
        await websocket.send(data)

    async def authenticate_client(self, websocket: websockets, handshake_data: dict) -> bool:
        """ Parses the JSON values sent from client during authentication handshake """
        if "agent" in handshake_data:
            if handshake_data["agent"].lower() == "dashboard":
                print("\tType: Dashboard")
                if "bid" in handshake_data:
                    # ToDo: Check length and use regex to confirm valid characters for bid
                    session_data = await self.connection_db.get_dashboard_session_data(handshake_data["bid"])
                    # ToDo: Check to see if session is already active. Compare request IP to dashboard IP
                    if session_data:
                        session_data["uuid"] = handshake_data["bid"]
                        if not session_data["active"]:
                            await self.connection_db.set_session_active(session_data["id"])
                            await self.attach_dashboard(websocket, session_data, handshake_data)
                            return True
                        else:
                             print("Error: Session already filled")
                    else:
                        print("Error: Unable to read session table values")
            elif handshake_data["agent"] == "node":
                if "token" in handshake_data and "nid" in handshake_data and "qdot" in handshake_data:
                    # secret_key = pyotp.random_base32(32)

                    public_key = handshake_data["qdot"]
                    encrypted_key = await self.connection_db.get_node_seed(handshake_data["nid"])
                    try:
                        secret_key = Fernet(public_key).decrypt(encrypted_key.encode())
                    except (cryptography.fernet.InvalidToken, TypeError):
                        print("Bad public key")
                        return False

                    token = pyotp.TOTP(secret_key.decode())

                    if token.verify(handshake_data["token"]):
                        new_public_key = Fernet.generate_key()      # Rotate the public key
                        reencrypted_key = Fernet(new_public_key).encrypt(secret_key)
                        await self.connection_db.update_node_seed(handshake_data["nid"], reencrypted_key)
                        response = json.dumps({"qdot": new_public_key.decode()})
                        await websocket.send(response)
                        await self.attach_node(websocket, handshake_data)
                        return True
                return False
        return False

    async def cleanup(self):
        """ Cleanup routine called when server is shutting down """
        await self.connection_db.cleanup()

'''
Resources: pyOTP 
https://github.com/pyauth/pyotp

Resources: Fernet encryption
https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password
https://stackoverflow.com/questions/60912944/unable-to-except-cryptography-fernet-invalidtoken-error-in-python
'''
