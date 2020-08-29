from server.database.DBConnection import DBConnection

# https://stackoverflow.com/questions/283645/python-list-in-sql-query-as-parameter?noredirect=1&lq=1

class Sessions:
    def __init__(self):
        self.db_connection = DBConnection()

    def get_session(self, uuid) -> dict:
        stmt = "SELECT id, user_id, active, created, otp, ip_addr FROM sessions WHERE uuid = ?"
        query = self.db_connection.get_prepared_cursor()
        query.execute(stmt, (uuid,))
        result = {}
        for (id, user_id, active, created, otp, ip_addr) in query:
            result["id"] = id
            result["user_id"] = user_id
            result["active"] = active
            result["created"] = created
            result["otp"] = otp.decode()
            result["ip_addr"] = ip_addr.decode()
        query.close()
        return result