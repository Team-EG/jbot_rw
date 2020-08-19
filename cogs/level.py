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
import random
import os
import shutil
import time
import json
import asyncio
from discord.ext import commands
from modules import lvl_calc
from modules import jbot_db
from modules import page
from modules import custom_errors

loop = asyncio.get_event_loop()


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_global = jbot_db.JBotDB("jbot_db_global")
        self.jbot_db_level = jbot_db.JBotDB("jbot_db_level")

    def cog_unload(self):
        loop.run_until_complete(self.jbot_db_level.close_db())

    async def cog_before_invoke(self, ctx):
        try:
            guild_setting = (await self.jbot_db_global.res_sql("""SELECT use_level FROM guild_setup WHERE guild_id=?""", (ctx.guild.id,)))[0]
        except IndexError:
            return
        if not bool(guild_setting["use_level"]):
            raise custom_errors.NotEnabled("레벨")

    @commands.command(name="레벨", description="자신의 레벨을 출력합니다.", usage="`레벨 (유저)`")
    async def level(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        lvl_data = await self.jbot_db_level.res_sql(f"""SELECT * FROM "{ctx.guild.id}_level" WHERE user_id=?""", (user.id,))
        lvl_data = lvl_data[0]
        lvl = lvl_data["lvl"]
        exp = lvl_data["exp"]
        embed = discord.Embed(title="레벨", description=str(user.mention), color=user.color)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="레벨", value=str(lvl))
        embed.add_field(name="XP", value=str(exp))
        await ctx.send(embed=embed)

    @commands.command(name="랭크", description="이 서버의 레벨 리더보드를 출력합니다.")
    async def rank(self, ctx):
        sorted_list = await self.jbot_db_level.res_sql(f"""SELECT * FROM "{ctx.guild.id}_level" ORDER BY exp DESC""")
        base_embed = discord.Embed(title="랭크", description=str(ctx.guild.name), color=discord.Colour.from_rgb(225, 225, 225))
        base_embed.set_thumbnail(url=ctx.guild.icon_url)
        base_embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar_url)
        lvl = 1
        embed = base_embed.copy()
        embed_list = []
        count = 0
        for x in sorted_list:
            if int(x["exp"]) == 0:
                break
            if count != 0 and count % 5 == 0:
                embed_list.append(embed)
                embed = base_embed.copy()
            embed.add_field(name=str(lvl),
                            value=f"{ctx.guild.get_member(int(x['user_id'])).mention}\n레벨: {x['lvl']}\nXP: {x['exp']}",
                            inline=False)
            lvl += 1
            count += 1
        embed_list.append(embed)
        if len(embed_list) == 1:
            return await ctx.send(embed=embed)
        await page.start_page(self.bot, ctx=ctx, lists=embed_list, embed=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:  # DM
            return
        if message.author.bot:  # Bot
            return

        if "--NOLEVEL" in str(message.channel.topic):
            return

        try:
            guild_setting = (await self.jbot_db_global.res_sql("""SELECT use_level FROM guild_setup WHERE guild_id=?""", (message.guild.id,)))[0]
        except IndexError:
            return
        if not bool(guild_setting["use_level"]):
            return

        curr_time = time.time()
        time_check_exist = os.path.isfile(f"temp/{message.guild.id}_time.json")
        if not time_check_exist:
            shutil.copy("json_temp.json", f"temp/{message.guild.id}_time.json")

        with open(f"temp/{message.guild.id}_time.json", "r") as f:
            time_data = json.load(f)
        try:
            last_msg = int(time_data[str(message.author.id)])
            calc_time = curr_time - last_msg
            if calc_time < 60:
                return
        except KeyError:
            pass
        time_data[str(message.author.id)] = curr_time
        with open(f"temp/{message.guild.id}_time.json", "w") as f:
            json.dump(time_data, f, indent=4)

        column_set = jbot_db.set_column({"name": "user_id", "type": "INTEGER", "default": False},
                                        {"name": "exp", "type": "INTEGER", "default": 0},
                                        {"name": "lvl", "type": "INTEGER", "default": 1})
        lvl_exist = await self.jbot_db_level.res_sql("SELECT name FROM sqlite_master WHERE type='table'")
        if f"{message.guild.id}_level" not in [x["name"] for x in lvl_exist]:
            await self.jbot_db_level.exec_sql(f"""CREATE TABLE "{message.guild.id}_level" ( {column_set} )""")

        curr_exp_and_lvl = await self.jbot_db_level.res_sql(f"""SELECT * FROM "{message.guild.id}_level" WHERE user_id=?""", (message.author.id,))

        xp_choice = random.randint(5, 25)
        if not bool(curr_exp_and_lvl):
            await self.jbot_db_level.exec_sql(f"""INSERT INTO "{message.guild.id}_level"(user_id) VALUES (?)""", (message.author.id,))
            curr_exp_and_lvl = await self.jbot_db_level.res_sql(f"""SELECT * FROM "{message.guild.id}_level" WHERE user_id=?""", (message.author.id,))
        curr_exp = int(curr_exp_and_lvl[0]["exp"])
        curr_lvl = int(curr_exp_and_lvl[0]["lvl"])
        curr_exp += xp_choice
        await self.jbot_db_level.exec_sql(f"""UPDATE "{message.guild.id}_level" SET exp=? WHERE user_id=?""", (curr_exp, message.author.id))

        can_lvl_up = await lvl_calc.can_lvl_up(curr_lvl, curr_exp)
        if not can_lvl_up:
            return
        curr_lvl += 1
        await self.jbot_db_level.exec_sql(f"""UPDATE "{message.guild.id}_level" SET lvl=? WHERE user_id=?""", (curr_lvl, message.author.id))
        to_give_roles = json.loads((await self.jbot_db_global.res_sql("""SELECT "to_give_roles" FROM guild_setup WHERE guild_id=?""", (message.guild.id,)))[0]["to_give_roles"])
        if str(curr_lvl) in to_give_roles.keys():
            tgt_role = message.guild.get_role(int(to_give_roles[str(curr_lvl)]))
            if tgt_role is None:
                return
            await message.author.add_roles(tgt_role)


def setup(bot):
    bot.add_cog(Level(bot))
