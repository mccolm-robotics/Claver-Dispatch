class IPWhitelist:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    async def get_id_of_whitelisted_ip(self, ip_address):
        stmt = "SELECT id FROM ip_whitelist WHERE address = %s"
        vals = (ip_address,)
        result = await self.db_connection.query_fetch_returns_dict(query=stmt, args=vals)
        if type(result) is dict:
            return result[0]
        else:
            return result
