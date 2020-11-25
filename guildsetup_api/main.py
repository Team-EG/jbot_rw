import flask
import flask_restful
import sqlite3
import discord
import threading
import json
import asyncio

app = flask.Flask(__name__)
app.config['JSON_AS_ASCII'] = False
api = flask_restful.Api(app)
discord_client = discord.Client(intents=discord.Intents.all())
loop = asyncio.get_event_loop()

login_clients = {}


def check_if_req_key_exist(req_keys, json_data):
    forgot = [x for x in req_keys if x not in json_data.keys()]
    why_none = [x for x in json_data.keys() if x in req_keys and json_data[x] is None and x != "params"]
    if len(forgot) != 0:
        return flask_restful.abort(400, description=f"Wrong json format. You forgot: {', '.join(forgot)}")
    if len(why_none) != 0:
        return flask_restful.abort(400, description=f"Values of required keys are None(null). Keys with None(null) value: {', '.join(why_none)}")
    return None


@discord_client.event
async def on_ready():
    print(f"Client: {discord_client.user.id}")


@app.route("/api/guild_setup/<int:guild_id>")
def get_guild_setup(guild_id: int):
    jbot_db = sqlite3.connect("../database/jbot_db_global.db")
    jbot_db.row_factory = sqlite3.Row
    cur = jbot_db.cursor()
    cur.execute("SELECT * FROM guild_setup WHERE guild_id=?", (guild_id,))
    resp = cur.fetchone()
    cur.close()
    jbot_db.close()
    if not bool(resp):
        return flask.abort(404, description="Guild Not Found. Check guild_id.")
    return dict(resp)


@app.route("/api/guild/<int:guild_id>")
def get_guild_info(guild_id: int):
    tgt_guild: discord.Guild = discord_client.get_guild(guild_id)
    if not tgt_guild:
        guild_task = loop.create_task(discord_client.fetch_guild(guild_id))
        while not guild_task.done():
            continue
        tgt_guild = guild_task.result()
    #print(tgt_guild)
    if tgt_guild is None:
        return flask.abort(404, description="Guild not found.")
    if not tgt_guild.roles:
        role_task = loop.create_task(tgt_guild.fetch_roles())
        while not role_task.done():
            continue
        roles = role_task.result()
    else:
        roles = tgt_guild.roles
    guild_data = {"name": tgt_guild.name,
                  "channels": [{x.id: x.name} for x in tgt_guild.channels if isinstance(x, discord.TextChannel)],
                  "members": [{x.id: [str(x), x.nick if x.nick else x.name]} for x in tgt_guild.members],
                  "roles": [{x.id: x.name} for x in roles]}
    return guild_data


class JBotAPI(flask_restful.Resource):
    # noinspection PyMethodMayBeStatic
    def post(self, guild_id: int):
        json_data = flask.request.get_json(force=True)


# --------------Discord API--------------
with open("../bot_settings.json", "r", encoding="UTF-8") as f:
    bot_settings = json.load(f)
t = threading.Thread(target=discord_client.run, args=(bot_settings["canary_token"],))
t.start()

# --------------Flask--------------
api.add_resource(JBotAPI, "/api/update/<int:guild_id>")
app.run(host="0.0.0.0", debug=True)
