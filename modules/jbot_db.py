"""
    jbot_rw
    Copyright (C) 2020 Team EG

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
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

    async def res_sql(self, line, param: iter = None, return_raw=False) -> list:
        async with self.db.execute(line, param) as cur:
            rows = await cur.fetchall()
            if not return_raw:
                return [dict(x) for x in rows]
            return [x for x in rows]

    async def close_db(self) -> None:
        await self.db.close()
