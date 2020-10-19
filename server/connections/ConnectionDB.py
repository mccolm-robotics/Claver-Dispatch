from server.database.Accounts import Accounts
from server.database.DBConnection import DBConnection
from server.database.DeviceInvitations import DeviceInvitations
from server.database.IPWhitelist import IPWhitelist
from server.database.NodeDevices import NodeDevices
from server.database.Sessions import Sessions


class ConnectionDB:
    def __init__(self, event_loop):
        self.db_connection = DBConnection(event_loop)
        self.sessions = Sessions(self.db_connection)
        self.accounts = Accounts(self.db_connection)
        self.node_devices = NodeDevices(self.db_connection)
        self.ip_whitelist = IPWhitelist(self.db_connection)
        self.device_invitations = DeviceInvitations(self.db_connection)

    async def get_dashboard_session_data(self, uuid: str):
        """ Gets the session data for a given uuid """
        return await self.sessions.get_session(uuid)

    async def get_node_seed(self, device_id: str) -> str:
        result = await self.node_devices.get_seed(device_id)
        if not result:
            return result
        else:
            return result["seed"]

    async def get_node_device(self, device_id):
        """ Gets descriptive data about device from node_devices table """
        return await self.node_devices.get_node_device(device_id)

    async def update_node_device_status(self, status, last_reconnect, id):
        await self.node_devices.update_node_device_status(status, last_reconnect, id)

    async def get_device_invitation(self, device_id):
        """ Gets assoc array of values from device_invitations table """
        result = await self.device_invitations.get_device_invitation(device_id)
        if not result:
            return result
        else:
            return result[0]

    async def remove_device_invitation(self, id):
        """ Removes device invitation from device_invitations table """
        await self.device_invitations.remove_device_invitation(id)

    async def get_id_of_whitelisted_ip(self, ip_address):
        """ Gets int of id for ip address in ip_whitelist table """
        result = await self.ip_whitelist.get_id_of_whitelisted_ip(ip_address)
        if not result:
            return result
        else:
            return result[0]

    async def update_node_seed(self, device_id, seed):
        return await self.node_devices.update_seed(device_id, seed)

    async def add_new_device(self, node_id, uuid, device_id, device_name, seed, platform, status, last_reconnect):
        await self.node_devices.add_new_device(node_id, uuid, device_id, device_name, seed, platform, status, last_reconnect)

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