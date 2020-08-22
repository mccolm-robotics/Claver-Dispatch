from server.database.DBConnection import DBConnection

class Accounts:
    def __init__(self):
        self.db_connection = DBConnection()

    def get_account(self, username):
        stmt = "SELECT id, password FROM accounts WHERE username = ?"
        query = self.db_connection.get_prepared_cursor()
        query.execute(stmt, (username,))
        for (id, password) in query:
            result_id = id
            result_pw = password
        query.close()
        return result_id, result_pw