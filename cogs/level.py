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
        lvl_data = await self.jbot_db_level.get_from_db("*", f"{ctx.guild.id}_level", "user_id", str(user.id))
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
        lvl_data = await self.jbot_db_level.get_db("*", f"{ctx.guild.id}_level")
        # sorted_list = await self.jbot_db_level.res_sql(f"SELECT * FROM {ctx.guild.id}_level ORDER BY exp DESC;")
        sorted_list = reversed(sorted(lvl_data, key=lambda x: int(x["exp"])))
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

    @commands.command(name="레벨픽스")
    async def lvl_fix(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        lvl_data = await self.jbot_db_level.get_from_db("*", f"{ctx.guild.id}_level", "user_id", str(user.id))
        lvl_data = lvl_data[0]
        curr_exp = int(lvl_data["exp"])
        lvl = int(await lvl_calc.calc_lvl(curr_exp))
        await self.jbot_db_level.update_db(f"{ctx.guild.id}_level", "lvl", lvl, "user_id", str(user.id))
        await ctx.send("완료")

    @commands.command(name="레벨전체픽스")
    async def lvl_all_fix(self, ctx):
        for x in self.bot.guilds:
            print(x)
            for y in x.members:
                print(y)
                user = y
                lvl_data = await self.jbot_db_level.get_from_db("*", f"{x.id}_level", "user_id", str(user.id))
                if str(lvl_data) == "()":
                    continue
                print(lvl_data)
                lvl_data = lvl_data[0]
                curr_exp = int(lvl_data["exp"])
                lvl = int(await lvl_calc.calc_lvl(curr_exp))
                await self.jbot_db_level.update_db(f"{x.id}_level", "lvl", lvl, "user_id", str(user.id))
                await ctx.send("완료")
        await ctx.send("픽스 완료!")

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

        table_name = f"{message.guild.id}_level"
        where = "user_id"
        where_val = message.author.id

        curr_exp_and_lvl = await self.jbot_db_level.get_from_db("*", table_name, where, where_val)

        xp_choice = random.randint(5, 25)
        if str(curr_exp_and_lvl) == "()":
            await self.jbot_db_level.insert_db(table_name, "user_id", message.author.id)
            curr_exp_and_lvl = await self.jbot_db_level.get_from_db("*", table_name, where, where_val)
        curr_exp = int(curr_exp_and_lvl[0]["exp"])
        curr_lvl = int(curr_exp_and_lvl[0]["lvl"])
        curr_exp += xp_choice
        await self.jbot_db_level.update_db(table_name, "exp", curr_exp, where, where_val)

        can_lvl_up = await lvl_calc.can_lvl_up(curr_lvl, curr_exp)
        if not can_lvl_up:
            return
        curr_lvl += 1
        await self.jbot_db_level.update_db(table_name, "lvl", curr_lvl, where, where_val)


def setup(bot):
    bot.add_cog(Level(bot))
