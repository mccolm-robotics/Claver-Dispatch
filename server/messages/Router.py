import json

from server.connections.ConnectionManager import ConnectionManager
from server.messages.Bus import Bus
from server.messages.StateManager import StateManager


class Router:
    def __init__(self, connectionManager: ConnectionManager, eventLoop) -> None:
        self.connectionManager = connectionManager
        self.messageBus = Bus(connectionManager, eventLoop)
        self.connectionManager.set_messageBus(self.messageBus)
        self.stateManager = StateManager(connectionManager, self.messageBus, eventLoop)

    async def adjust_connected_users_list(self, agent) -> None:
        """ Notifies the Claver network of changes to connected clients list. """
        await self.stateManager.notify_claver_clients_of_closed_connection(agent)

    async def ingest_events(self, websocket, message: str) -> None:
        """ All incoming websocket messages are dumped to the 'events queue' for processing """
        data = json.loads(message)
        # More sophisticated control over websocket communication
        if "channel_type" in data:
            if data["channel_type"] == "direct":
                self.connectionManager.get_client(websocket).incoming_message(json.loads(message))
        else:
            if "mode" in data:  # ToDo: This 'check and set' is duplicated in "authenticate_client" per client now. Remove from here
                # Is this needed when a Claver board changes its mode?
                self.connectionManager.get_client(websocket).set_mode(data["mode"]) # This is now passed in with the handshake data
            # The incoming message is sent out for processing with information about the sender stored in the header variable
            await self.messageBus.add_to_events_queue(message, self.connectionManager.get_client(websocket).get_header_id())

    async def authenticate_client(self, websocket, message) -> bool:
        """ Authorization step for new websocket connections. Handshake JSON string is parsed for authentication tokens
            and, if valid, the websocket is passed back initial state data appropriate to its mode value. """
        handshake_data = json.loads(message)    # ToDo: Perform regex to ensure JSON message is safe
        if "mode" in handshake_data:
            print(handshake_data)
            if await self.connectionManager.authenticate_client(websocket, handshake_data):
                await self.stateManager.get_initial_state(websocket)
                return True
            elif handshake_data["mode"] == "handshake":
                await self.connectionManager.authorization_handshake(websocket, handshake_data)
        else:
            print("Router: Authenticating Client - Handshake data does not include 'mode'")
            return False
