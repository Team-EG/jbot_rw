import discord
import json
import time
import os
import shutil
from discord.ext import commands
from modules import admin, jbot_db


class Spam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_warns = jbot_db.JBotDB("jbot_db_warns")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:  # DM
            return
        if message.author.bot:  # Bot
            return

        if "--NOSPAMCOUNT" in str(message.channel.topic):
            return

        curr_time = time.time()
        time_check_exist = os.path.isfile(f"temp/{message.guild.id}_spam.json")
        if not time_check_exist:
            shutil.copy("json_temp.json", f"temp/{message.guild.id}_spam.json")

        with open(f"temp/{message.guild.id}_spam.json", "r") as f:
            time_data = json.load(f)
        try:
            last_msg = int(time_data[str(message.author.id)]["time"])
            calc_time = curr_time - last_msg
            if calc_time > 20: # 20초에 10번 -> 20번
                time_data[str(message.author.id)]["time"] = curr_time
                time_data[str(message.author.id)]["spam_count"] = 0
                with open(f"temp/{message.guild.id}_spam.json", "w") as f:
                    json.dump(time_data, f, indent=4)
                return
        except KeyError:
            time_data[str(message.author.id)] = {}
            time_data[str(message.author.id)]["time"] = curr_time
            time_data[str(message.author.id)]["spam_count"] = 0
            with open(f"temp/{message.guild.id}_spam.json", "w") as f:
                json.dump(time_data, f, indent=4)
            return
        time_data[str(message.author.id)]["spam_count"] += 1
        with open(f"temp/{message.guild.id}_spam.json", "w") as f:
            json.dump(time_data, f, indent=4)
        if time_data[str(message.author.id)]["spam_count"] == 10:
            await message.channel.send("굴라크")
        elif time_data[str(message.author.id)]["spam_count"] == 15:
            await message.channel.send("경고임 ㅅㄱ")
            await admin.warn(self.jbot_db_warns, message.author, reason="도배 카운트 누적", issued_by=self.bot.user, message=message)


def setup(bot):
    bot.add_cog(Spam(bot))
