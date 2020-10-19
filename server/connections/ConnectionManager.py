import asyncio
import json
import uuid
from datetime import time

import cryptography
import pyotp
import websockets
from cryptography.fernet import Fernet
from server.connections.Node import Node
from server.connections.Dashboard import Dashboard
from server.connections.ConnectionDB import ConnectionDB
from server.connections.MQConnector import MQConnector
import time


class ConnectionManager:
    def __init__(self):
        self.connection_db = None
        self.mq_connector = None
        self.event_loop = None
        self.messageBus = None
        self.connected_clients = set()  # Unique list (set) of current websockets. This facilitates a quick lookup when confirming a connection's authentication status
        self.connected_nodes = set()
        self.connected_dashboard_modes = {}  # This dictionary tracks the number of connected dashboards. Dictionary is keyed by dashboard mode values.
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

    def get_connected_dashboard_modes(self) -> dict:
        """ Returns dict of connected dashboard modes """
        return self.connected_dashboard_modes

    def get_client_count(self) -> int:
        """ Returns count of all websocket connections """
        return len(self.connected_clients)

    def get_connected_clients(self) -> set:
        """ Returns set of all websocket connections """
        return self.connected_clients

    def is_authorized_user(self, websocket) -> bool:
        """ Boolean check for websocket in set of connected websockets """
        return websocket in self.connected_clients

    async def is_ip_whitelisted(self, ip_address):
        if await self.connection_db.get_id_of_whitelisted_ip(ip_address):
            return True
        else:
            return False

    async def create_chain_of_trust(self, websocket):
        request = {"request": "access_code"}
        await websocket.send(json.dumps(request))
        result = await websocket.recv()
        handshake_data = json.loads(result)
        if "mode" in handshake_data and "agent" in handshake_data:
            if handshake_data["agent"] == "node" and handshake_data["mode"] == "handshake":
                device_id = handshake_data["nid"]
                access_code = handshake_data["access_code"]
                invitation_data = await self.connection_db.get_device_invitation(device_id)
                if type(invitation_data) is dict:
                    if invitation_data["access_code"] == access_code and invitation_data["is_valid"] > 0:
                        if invitation_data['expires'] > time.time():
                            print(f"Invitation accepted by device {device_id}")
                            secret_key = pyotp.random_base32(32)
                            public_key = Fernet.generate_key()  # Rotate the public key
                            seed = Fernet(public_key).encrypt(secret_key.encode())
                            claver_id = uuid.uuid4()
                            # Have we checked to make sure the device doesn't already exist in the DB?
                            await self.connection_db.add_new_device(invitation_data["node_id"], str(claver_id), device_id, handshake_data["device_name"], seed.decode(), handshake_data["platform"], 1, int(time.time()))
                            await websocket.send(json.dumps({"secret_key": secret_key, "public_key": public_key.decode()}))
                            await self.connection_db.remove_device_invitation(invitation_data["id"])
                        else:
                            print("Invitation expired. Removing.")
                            await self.connection_db.remove_device_invitation(invitation_data["id"])

    async def attach_node(self, websocket: websockets, handshake_data):
        """ Adds websocket to records of connected websockets. Adds websocket to set of connected Nodes. """
        self.connected_clients.add(websocket)
        self.connected_nodes.add(websocket)
        self.client_dict[websocket] = await Node.initialize(self.event_loop, websocket, handshake_data, self.mq_connector, self.connection_db)

    async def attach_dashboard(self, websocket: websockets, session_data, handshake_data) -> None:
        """ Adds websocket to dynamic dictionary of client sets. Dictionary is keyed to 'mode' value sent during websocket handshake. """
        self.connected_clients.add(websocket)
        # self.connected_dashboards.add(websocket)
        if handshake_data["mode"].lower() not in self.connected_dashboard_modes:    # Track the number of dashboards of this type (mode) connected
            self.connected_dashboard_modes[handshake_data["mode"].lower()] = 1
        else:
            self.connected_dashboard_modes[handshake_data["mode"].lower()] += 1
        self.client_dict[websocket] = await Dashboard.initialize(self.event_loop, websocket, session_data, handshake_data, self.mq_connector, self.connection_db, self)

    async def detach_client(self, websocket: websockets):
        """ Closes client objects and removes websocket from records of connected websockets """
        await self.client_dict[websocket].close()
        if websocket in self.connected_nodes:
            self.connected_nodes.remove(websocket)
        elif self.client_dict[websocket].get_mode() in self.connected_dashboard_modes:
            self.connected_dashboard_modes[self.client_dict[websocket].get_mode().lower()] -= 1
            if self.connected_dashboard_modes[self.client_dict[websocket].get_mode().lower()] == 0:
                self.connected_dashboard_modes.pop(self.client_dict[websocket].get_mode().lower())
        self.client_dict.pop(websocket)
        self.connected_clients.remove(websocket)

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
            elif handshake_data["agent"].lower() == "node":
                if "token" in handshake_data and "nid" in handshake_data and "qdot" in handshake_data:

                    public_key = handshake_data["qdot"]
                    encrypted_key = await self.connection_db.get_node_seed(handshake_data["nid"])
                    if not encrypted_key:
                        print("Device has not been registered!")
                        return False
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
