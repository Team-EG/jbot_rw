import koreanbots
import json
from discord.ext import commands
from . import jbot_db


class CustomClient(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        with open("bot_settings.json", "r") as f:
            bot_settings = json.load(f)
            token = bot_settings["koreanbots_token"]
        super().__init__(*args, **kwargs)
        self.koreanbots = koreanbots.Client(self, token, postCount=True)
        self.jbot_db_global = jbot_db.JBotDB("jbot_db_global")
        self.jbot_db_warns = jbot_db.JBotDB("jbot_db_warns")
        self.jbot_db_level = jbot_db.JBotDB("jbot_db_level")
        self.stable_token = bot_settings["stable_token"]
        self.canary_token = bot_settings["canary_token"]
        self.last_stock_change = 0

    def run_bot(self, canary=False):
        if canary is True:
            self.run(self.canary_token)
        else:
            self.run(self.stable_token)
