from server.database.Accounts import Accounts
from server.database.DBConnection import DBConnection
from server.database.NodeDevices import NodeDevices
from server.database.Sessions import Sessions


class ConnectionDB:
    def __init__(self, event_loop):
        self.db_connection = DBConnection(event_loop)
        self.sessions = Sessions(self.db_connection)
        self.accounts = Accounts(self.db_connection)
        self.node_devices = NodeDevices(self.db_connection)

    async def get_dashboard_session_data(self, uuid: str):
        """ Gets the session data for a given uuid """
        return await self.sessions.get_session(uuid)

    async def get_node_seed(self, device_id: str) -> str:
        result = await self.node_devices.get_seed(device_id)
        return result["seed"]

    async def update_node_seed(self, device_id, seed):
        return await self.node_devices.update_seed(device_id, seed)

    async def get_all_dashboard_sessions(self):
        return await self.sessions.get_all_dashboard_sessions()

    async def set_session_active(self, id):
        """ Sets the dashboard session to active using session id """
        await self.sessions.set_session_active(id)

    async def delete_dashboard_session(self, id):
        await self.sessions.delete_browser_session(id)

    async def get_account(self, username):
        result = await self.accounts.get_account(username)
        return result["id"], result["password"]

    async def cleanup(self):
        """ Housekeeping jobs before program terminates """
        await self.sessions.cleanup()