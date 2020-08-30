from server.database.DBConnection import DBConnection
import binascii

class NodeDevices:
    def __init__(self):
        self.db_connection = DBConnection()

    def get_seed(self, device_id) -> str:
        stmt = "SELECT seed FROM node_devices WHERE device_id = ?"
        query = self.db_connection.get_prepared_cursor()
        query.execute(stmt, (device_id,))
        row = query.fetchone()      # Fetch only on row as there should only be one result
        result = row[0].decode()    # Decode the bytearray into a string
        query.close()
        return result

    def update_seed(self, device_id, seed):
        stmt = "UPDATE node_devices SET seed = ? WHERE device_id = ?"
        query = self.db_connection.get_prepared_cursor()
        status = query.execute(stmt, (seed, device_id,))
        self.db_connection.commit()
        query.close()
        return status


# https://www.tutorialspoint.com/python_data_access/python_mysql_insert_data.htm