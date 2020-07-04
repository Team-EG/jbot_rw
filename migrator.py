import json
import os
import asyncio
from modules import jbot_db, lvl_calc

jbot_db_migrationtest = jbot_db.JBotDB("jbot_db_migrationtest")


async def migrator():
    files = os.listdir("level")
    for x in files:
        if x.endswith(".json"):
            continue
        with open(f"level/{x}/xp.json", "r") as f:
            xp_data = json.load(f)
        is_exist = await jbot_db_migrationtest.check_if_table_exist(f"{x}_level")
        if not is_exist:
            column_set = jbot_db.set_column(user_id=None, lvl=0, exp=0)
            await jbot_db_migrationtest.create_table(jbot_db_migrationtest.db_name, f"{x}_level", column_set)
        guild_id = x
        user_id_list = xp_data.keys()
        for y in user_id_list:
            user_id = y
            lvl = int(xp_data[y]["lvl"])
            exp = int(xp_data[y]["exp"])
            exp += int(await lvl_calc.calc_old(lvl))
            lvl = int(await lvl_calc.calc_lvl(exp))
            await jbot_db_migrationtest.insert_db(f"{guild_id}_level", "user_id", user_id)
            await jbot_db_migrationtest.update_db(f"{guild_id}_level", "exp", exp, "user_id", user_id)
            await jbot_db_migrationtest.update_db(f"{guild_id}_level", "lvl", lvl, "user_id", user_id)

loop = asyncio.get_event_loop()
loop.run_until_complete(migrator())
