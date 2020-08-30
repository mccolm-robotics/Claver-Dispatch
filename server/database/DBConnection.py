import mysql.connector

class DBConnection:
    def __init__(self):
        self.host = 'localhost'
        self.user = 'root'
        self.password = ''
        self.database = 'claver'
        self.connection = mysql.connector.connect(host=self.host,
                                                  user=self.user,
                                                  password=self.password,
                                                  database=self.database)
        # Need to handle error:
        # ConnectionRefusedError: [Errno 111] Connection refused

    def get_prepared_cursor(self):
        return self.connection.cursor(prepared=True)

    def commit(self):
        self.connection.commit()

    def __del__(self):
        self.connection.close()
