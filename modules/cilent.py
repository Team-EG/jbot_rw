import koreanbots
import json
import lavalink
import datetime
from discord.ext import commands
from . import jbot_db


class CustomClient(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        with open("bot_settings.json", "r") as f:
            bot_settings = json.load(f)
            token = bot_settings["koreanbots_token"]
            debug = bot_settings["debug"]
        super().__init__(*args, **kwargs)
        self.koreanbots = koreanbots.Client(self, token, postCount=False if debug else True)
        self.lavalink: lavalink.Client
        self.jbot_db_global = jbot_db.JBotDB("jbot_db_global")
        self.jbot_db_warns = jbot_db.JBotDB("jbot_db_warns")
        self.jbot_db_level = jbot_db.JBotDB("jbot_db_level")
        self.jbot_db_memory = jbot_db.JBotDB(":memory:")
        self.__stable_token = bot_settings["stable_token"]
        self.__canary_token = bot_settings["canary_token"]
        self.last_stock_change = 0
        self.loop.create_task(self.init_lava())

    def run_bot(self, canary=False):
        if canary:
            self.run(self.__canary_token)
        else:
            self.run(self.__stable_token)

    async def init_lava(self):
        await self.wait_until_ready()
        self.lavalink = lavalink.Client(self.user.id, shard_count=len(self.shards) if bool(self.shards) else 1)
        self.lavalink.add_node(host=self.get_bot_settings()["lavahost"],
                               port=self.get_bot_settings()["lavaport"],
                               password=self.get_bot_settings()["lavapw"],
                               region="ko")
        self.add_listener(self.lavalink.voice_update_handler, 'on_socket_response')

    @staticmethod
    def get_bot_settings() -> dict:
        with open('bot_settings.json', 'r') as f:
            return json.load(f)

    @staticmethod
    def get_kst():
        return datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))
