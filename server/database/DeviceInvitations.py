class DeviceInvitations:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    async def get_device_invitation(self, device_id):
        stmt = "SELECT id, user_id, node_id, expires, is_valid, access_code FROM device_invitations WHERE device_id = %s"
        vals = (device_id,)
        result = await self.db_connection.query_fetch_returns_dict(query=stmt, args=vals)
        if type(result) is dict:
            return result[0]
        else:
            return result

    async def remove_device_invitation(self, id):
        stmt = "DELETE FROM device_invitations WHERE id = %s"
        vals = (id,)
        result = await self.db_connection.query_push(query=stmt, args=vals)
        if not result:
            print("Error: Unable to remove device invitation.")