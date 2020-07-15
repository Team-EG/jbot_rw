import asyncio
import aiosqlite

loop = asyncio.get_event_loop()


def set_column(*args: dict) -> str:
    to_return = ""
    first = True
    for x in args:
        column_name = x["name"]
        column_type = x["type"]
        column_default = x["default"]
        if column_default is None:
            column_default = "NULL DEFAULT NULL"
        elif column_default is False:
            column_default = "NOT NULL"
        else:
            column_default = f"NOT NULL DEFAULT {column_default}"
        if first:
            to_return += f'"{column_name}" {column_type} {column_default}'
            to_return += " PRIMARY KEY"
            first = False
            continue
        to_return += f', "{column_name}" {column_type} {column_default}'
    return to_return


class JBotDB:
    def __init__(self, db_name: str):
        self.db = loop.run_until_complete(aiosqlite.connect("database/" + db_name + ".db"))
        self.db.row_factory = aiosqlite.Row
        self.db_name = db_name

    async def exec_sql(self, line, param: iter = None) -> None:
        await self.db.execute(line, param)
        await self.db.commit()
        return

    async def res_sql(self, line, param: iter = None) -> list:
        async with self.db.execute(line, param) as cur:
            rows = await cur.fetchall()
            return [dict(x) for x in rows]

    async def check_if_table_exist(self, table_name) -> bool:
        async with self.db.execute(f"SHOW TABLES LIKE ?", (table_name,)) as cur:
            res = await cur.fetchall()
            return table_name in str(res)

    async def close_db(self) -> None:
        await self.db.close()


if __name__ == "__main__":
    #print(set_column({"name": "guild_id", "type": "INTEGER", "default": False}, {"name": "name", "type": "TEXT", "default": None}))
    jbot_db = JBotDB("jbot_db_global")
    #loop.run_until_complete(jbot_db.exec_sql("""CREATE TABLE ex ("guild_id" INTEGER NOT NULL PRIMARY KEY, "name" TEXT NULL DEFAULT NULL)"""))
    #loop.run_until_complete(jbot_db.exec_sql("INSERT INTO ex VALUES (?, ?)", (123, "gulag")))
    print(loop.run_until_complete(jbot_db.res_sql("SELECT * FROM ex WHERE ?=?", ("guild_id", '123'))))
    loop.run_until_complete(jbot_db.close_db())
