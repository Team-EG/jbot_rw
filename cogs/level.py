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

loop = asyncio.get_event_loop()


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_level = jbot_db.JBotDB("jbot_db_level")

    def cog_unload(self):
        loop.run_until_complete(self.jbot_db_level.close_db())

    @commands.command(name="레벨")
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

    @commands.command(name="랭크")
    async def rank(self, ctx):
        sorted_list = await self.jbot_db_level.res_sql(f"""SELECT * FROM "{ctx.guild.id}_level" ORDER BY exp DESC""")
        embed = discord.Embed(title="랭크", description=str(ctx.guild.name), color=discord.Colour.from_rgb(225, 225, 225))
        lvl = 1
        for x in sorted_list:
            if int(x["exp"]) == 0:
                continue
            embed.add_field(name=str(lvl),
                            value=f"{ctx.guild.get_member(int(x['user_id'])).mention}\n레벨: {x['lvl']}\nXP: {x['exp']}",
                            inline=False)
            lvl += 1
        embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:  # DM
            return
        if message.author.bot:  # Bot
            return

        if "--NOLEVEL" in str(message.channel.topic):
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


def setup(bot):
    bot.add_cog(Level(bot))
