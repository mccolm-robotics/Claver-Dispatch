from server.database.DBConnection import DBConnection
import binascii

class NodeDevices:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    async def get_seed(self, device_id) -> str:
        stmt = "SELECT seed FROM node_devices WHERE device_id = %s"
        vals = (device_id,)
        result = await self.db_connection.query_fetch_returns_dict(query=stmt, args=vals)
        return result[0]

    async def update_seed(self, device_id, seed):
        stmt = "UPDATE node_devices SET seed = %s WHERE device_id = %s"
        vals = (seed, device_id,)
        await self.db_connection.query_push(query=stmt, args=vals)

# https://www.tutorialspoint.com/python_data_access/python_mysql_insert_data.htm