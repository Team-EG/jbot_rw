import json
import os
import shutil
from . import jbot_db


async def init_cache(pool: jbot_db.JBotDB, table_name):
    res = await pool.get_db("*", table_name)
    cache_exist = os.path.isfile(f"cache/{table_name}.json")
    if cache_exist:
        os.remove(f"cache/{table_name}.json")
    shutil.copy("json_temp.json", f"cache/{table_name}.json")
    with open(f"cache/{table_name}.json", "r") as f:
        json_cache = json.load(f)
    for x in res:
        global guild_id
        guild_id = None
        for k, v in x.items():
            if k in ["guild_id", "user_id"]:
                guild_id = v
                json_cache[v] = {}
                continue
            if v in ["False", "false"]:
                v = False
            if v in ["None", "null"]:
                v = None
            if v in ["True", "true"]:
                v = True
            json_cache[guild_id][k] = v
    with open(f"cache/{table_name}.json", "w") as f:
        json.dump(json_cache, f, indent=4)


async def load_cache(table_name):
    with open(f"cache/{table_name}.json", "r") as f:
        json_cache = json.load(f)
    return json_cache


async def reload_cache(pool: jbot_db.JBotDB, table_name):
    os.remove(f"cache/{table_name}.json")
    shutil.copy("json_temp.json", f"cache/{table_name}.json")
    await init_cache(pool, table_name)
