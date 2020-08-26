import websockets
from server.users.User import User


class UserManager:

    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.connected_clients = set()
        self.client_dict = {}

    def get_notification(self, websocket: websockets):
        return self.client_dict[websocket].get_notification()

    def authenticate(self, connection: websockets) -> bool:
        # If credentials are good
        self.attach_client(connection)
        return True

    def attach_client(self, connection: websockets):
        self.connected_clients.add(connection)
        self.client_dict[connection] = User(self.event_loop, connection)

    def detach_client(self, connection: websockets):
        self.connected_clients.remove(connection)
        self.client_dict.pop(connection)

    def get_client_count(self):
        return len(self.connected_clients)

    def get_connected_clients(self):
        return self.connected_clients