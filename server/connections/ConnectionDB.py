from server.database.Sessions import Sessions
from server.database.NodeDevices import NodeDevices

class ConnectionDB:
    def __init__(self):
        self.sessions = Sessions()
        self.node_devices = NodeDevices()

    def get_browser_session_data(self, uuid: str) -> dict:
        return self.sessions.get_session(uuid)

    def get_node_seed(self, device_id: str) -> str:
        return self.node_devices.get_seed(device_id)

    def update_node_seed(self, device_id, seed):
        return self.node_devices.update_seed(device_id, seed)