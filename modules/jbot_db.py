import asyncio
import aiomysql

loop = asyncio.get_event_loop()

host = "jebserver.iptime.org"
port = 11040
user = "jbot_db"
pw = "teamegJBOT4$"


async def connect_db(db_name="jbot_db_global"):
    pool = await aiomysql.create_pool(host=host, port=port,
                                      user=user, password=pw,
                                      db=db_name, loop=loop)
    return pool


def set_column(**kwargs):
    result_list = None
    primary_key = list(kwargs.keys())
    for k, v in kwargs.items():
        if k == primary_key[0]:
            extra_sql = "PRIMARY KEY"
        else:
            extra_sql = None
        if v is None:
            v = "NULL DEFAULT NULL"
        elif v is False:
            v = "NOT NULL"
        else:
            v = f"NOT NULL DEFAULT '{v}'"
        name = k
        init_val = v
        if bool(extra_sql) is True:
            result = f" `{name}` VARCHAR(20) {extra_sql} {init_val} "
        else:
            result = f" `{name}` VARCHAR(20) {init_val} "
        if result_list is None:
            result_list = result
            continue
        result_list += ',' + result
    return result_list


class JBotDB:
    def __init__(self, db_name: str):
        pool = loop.run_until_complete(connect_db(db_name))
        self.pool = pool
        self.db_name = db_name

    async def get_db(self, column, table, ):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"SELECT {column} FROM {table};")
                res = await cur.fetchall()
                await cur.close()
                return res

    async def get_from_db(self, column, table, where, where_val):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"SELECT {column} FROM {table} WHERE `{where}` = '{where_val}';")
                res = await cur.fetchall()
                await cur.close()
                return res

    async def insert_db(self, table, field, value):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"INSERT INTO `{table}`(`{field}`) VALUES ({value});")
                await conn.commit()
                res = await cur.fetchall()
                await cur.close()
                return res

    async def update_db(self, table, field, value, where, where_val):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"UPDATE `{table}` SET `{field}` = '{value}' WHERE `{where}` = '{where_val}';")
                await conn.commit()
                res = await cur.fetchall()
                await cur.close()
                return res

    async def create_table(self, db_name, table_name, column_details=" `placeholder` VARCHAR(20) NULL DEFAULT NULL "):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"CREATE TABLE `{db_name}`.`{table_name}` ({column_details}) ENGINE = InnoDB;")
                await conn.commit()
                await cur.close()
                return True

    async def exec_sql(self, line):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(line)
                await conn.commit()
                await cur.close()
                return True

    async def res_sql(self, line):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(line)
                res = await cur.fetchall()
                await cur.close()
                return res

    async def check_if_table_exist(self, table_name):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"SHOW TABLES LIKE '{table_name}'")
                res = await cur.fetchall()
                await cur.close()
                return table_name in str(res)

    async def delete_table(self, table_name, where, where_val):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"DELETE FROM `{table_name}` WHERE `{table_name}`.`{where}` = '{where_val}'")
                await conn.commit()
                await cur.close()
                return True

    async def close_db(self):
        self.pool.close()
        await self.pool.wait_closed()
        return True


if __name__ == "__main__":
    jbot_db = JBotDB("jbot_db_global")
    # print(loop.run_until_complete(jbot_db.get_from_db("*", "guild_setup", "guild_id", 653865550157578251)))
    loop.run_until_complete(jbot_db.create_table("jbot_db_level", f"_level", set_column(a=None, b=False)))
    loop.run_until_complete(jbot_db.close_db())
