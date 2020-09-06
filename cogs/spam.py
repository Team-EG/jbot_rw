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
import discord
import json
import time
import os
import shutil
from discord.ext import commands
from modules import admin
from modules.cilent import CustomClient


class Spam(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.jbot_db_global = bot.jbot_db_global
        self.jbot_db_warns = bot.jbot_db_warns

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:  # DM
            return
        if message.author.bot:  # Bot
            return

        if "--NOSPAMCOUNT" in str(message.channel.topic):
            return

        try:
            guild_setting = (await self.jbot_db_global.res_sql("""SELECT use_antispam FROM guild_setup WHERE guild_id=?""", (message.guild.id,)))[0]
        except IndexError:
            return
        if not bool(guild_setting["use_antispam"]):
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
            if calc_time > 20: # 20초에 10번 -> 15번
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
            await message.channel.send(f"{message.author.mention} 도배 카운트가 누적되고 있습니다. 도배 카운트가 더 누적된다면 경고가 자동으로 부여됩니다.")
        elif time_data[str(message.author.id)]["spam_count"] == 15:
            await message.channel.send("도배 카운트 누적으로 자동으로 경고가 부여되었습니다.")
            await admin.warn(jbot_db_global=self.jbot_db_global, jbot_db_warns=self.jbot_db_warns, member=message.author, reason="도배 카운트 누적", issued_by=self.bot.user, message=message)


def setup(bot):
    bot.add_cog(Spam(bot))
