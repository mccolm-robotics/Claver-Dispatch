from server.database.DBConnection import DBConnection

# https://stackoverflow.com/questions/283645/python-list-in-sql-query-as-parameter?noredirect=1&lq=1

class Sessions:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def get_connection(self):
        return self.db_connection

    async def get_session(self, uuid) -> dict:
        stmt = "SELECT id, user_id, ip_addr, active, created FROM sessions WHERE uuid = %s"
        vals = (uuid,)
        result = await self.db_connection.query_fetch_returns_dict(query=stmt, args=vals)
        return result[0]

    async def get_all_dashboard_sessions(self):
        stmt = "SELECT id, user_id, uuid, ip_addr, active, created FROM sessions WHERE session_type = %s"
        vals = ("dashboard",)
        result = await self.db_connection.query_fetch_returns_dict(query=stmt, args=vals)
        return result

    async def set_session_active(self, id):
        stmt = "UPDATE sessions SET active = %s WHERE id = %s"
        vals = (1, id)
        await self.db_connection.query_push(query=stmt, args=vals)

    async def remove_all_sessions(self):
        stmt = "DELETE FROM sessions"
        await self.db_connection.query_push(query=stmt)

    async def delete_browser_session(self, id):
        stmt = "DELETE FROM sessions WHERE id = %s"
        vals = (id,)
        await self.db_connection.query_push(query=stmt, args=vals)

    async def cleanup(self):
        await self.remove_all_sessions()