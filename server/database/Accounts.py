from server.database.DBConnection import DBConnection

# https://stackoverflow.com/questions/283645/python-list-in-sql-query-as-parameter?noredirect=1&lq=1

# class Accounts_blocking:
#     def __init__(self):
#         self.db_connection = DBConnection()
#
#     def get_account(self, username):
#         stmt = "SELECT id, password FROM accounts WHERE username = ?"
#         query = self.db_connection.get_prepared_cursor()
#         query.execute(stmt, (username,))
#         for (id, password) in query:
#             result_id = id
#             result_pw = password
#         query.close()
#         return result_id, result_pw

from server.database.DBConnection import DBConnection

# https://stackoverflow.com/questions/283645/python-list-in-sql-query-as-parameter?noredirect=1&lq=1

class Accounts:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    async def get_account(self, username):
        stmt = "SELECT id, password FROM accounts WHERE username = %s"
        vals = (username,)
        result = await self.db_connection.query_fetch_returns_dict(query=stmt, args=vals)
        if type(result) is dict:
            return result[0]
        else:
            return result