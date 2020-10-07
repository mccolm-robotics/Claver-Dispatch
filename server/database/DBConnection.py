import aiomysql

class DBConnection:
    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.host = 'localhost'
        self.port = 3306
        self.user = 'root'
        self.password = ''
        self.database = 'claver'

    # Switch over to connection pooling:
    # https://aiomysql.readthedocs.io/en/latest/pool.html
    # https://programtalk.com/vs2/python/5/peewee-async/peewee_async.py/

    async def query_fetch_returns_dict(self, query, args=None):
        conn = await aiomysql.connect(host=self.host, port=self.port,
                                          user=self.user, password=self.password,
                                          db=self.database, loop=self.event_loop)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, args)
            result = await cur.fetchall()
            conn.close()
            return result


    async def query_push(self, query, args=None):
        conn = await aiomysql.connect(host=self.host, port=self.port,
                                      user=self.user, password=self.password,
                                      db=self.database, loop=self.event_loop)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, args)
            await conn.commit()
            conn.close()


"""
Resources: Asyncio initialization
https://stackoverflow.com/questions/33128325/how-to-set-class-attribute-with-await-in-init/33134213

Resources: aiomysql documentation
https://aiomysql.readthedocs.io/en/latest/cursors.html

Resources: Connection pool
https://stackoverflow.com/questions/48247648/i-dont-know-using-python-aiomysql-normally-running-time-when-aiomysql-doesnt
"""

# class DBConnection:
#     def __init__(self, event_loop):
#         self.event_loop = event_loop
#         self.host = 'localhost'
#         self.port = 3306
#         self.user = 'root'
#         self.password = ''
#         self.database = 'claver'
#
#     async def query_fetch_returns_dict(self, query, args=None):
#         conn = await aiomysql.connect(host=self.host, port=self.port,
#                                           user=self.user, password=self.password,
#                                           db=self.database, loop=self.event_loop)
#         async with conn.cursor(aiomysql.DictCursor) as cur:
#             await cur.execute(query, args)
#             result = await cur.fetchall()
#             conn.close()
#             return result
#
#
#     async def query_push(self, query, args=None):
#         conn = await aiomysql.connect(host=self.host, port=self.port,
#                                       user=self.user, password=self.password,
#                                       db=self.database, loop=self.event_loop)
#         async with conn.cursor(aiomysql.DictCursor) as cur:
#             await cur.execute(query, args)
#             await conn.commit()
#             conn.close()