from server.database.DBConnection import DBConnection
import binascii

class NodeDevices:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    async def get_seed(self, device_id) -> str:
        stmt = "SELECT seed FROM node_devices WHERE device_id = %s"
        vals = (device_id,)
        result = await self.db_connection.query_fetch_returns_dict(query=stmt, args=vals)
        if not result:
            return result
        else:
            return result[0]

    async def update_seed(self, device_id, seed):
        stmt = "UPDATE node_devices SET seed = %s WHERE device_id = %s"
        vals = (seed, device_id,)
        await self.db_connection.query_push(query=stmt, args=vals)

    async def add_new_device(self, node_id, uuid, device_id, device_name, seed, platform, status, last_reconnect):
        stmt = "INSERT INTO node_devices(node_id, uuid, device_id, device_name, seed, platform, status, last_reconnect) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        vals = (node_id, uuid, device_id, device_name, seed, platform, status, last_reconnect,)
        result = await self.db_connection.query_push(query=stmt, args=vals)
        if not result:
            print("Error: Unable to insert new device into DB")

    async def get_node_device(self, device_id):
        stmt = "SELECT id, node_id, uuid, device_name, platform FROM node_devices WHERE device_id = %s"
        vals = (device_id,)
        result = await self.db_connection.query_fetch_returns_dict(query=stmt, args=vals)
        if not result:
            print("Error: Unable get retrieve node device from DB")
            return result
        else:
            return result[0]

    async def update_node_device_status(self, status, last_reconnect, id):
        stmt = "UPDATE node_devices SET status = %s, last_reconnect = %s WHERE id = %s"
        vals = (status, last_reconnect, id,)
        result = await self.db_connection.query_push(query=stmt, args=vals)
        if not result:
            print("Error: Unable to update node device status.")

# https://www.tutorialspoint.com/python_data_access/python_mysql_insert_data.htm