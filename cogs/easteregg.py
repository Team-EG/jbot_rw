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
import asyncio
from discord.ext import commands
from modules.cilent import CustomClient

loop = asyncio.get_event_loop()
easteregg_info = {
    "gulag": "???: 굴라크 가실래요?",
    "anyhorse": "아무말",
    "credit": "핵넷은 OST가 너무 좋군요."
}
easteregg_how_to = {
    "gulag": "굴라크 명령어를 사용하세요.",
    "anyhorse": "아무말 명령어를 사용하세요.",
    "credit": "히든 크레딧을 찾으세요."
}


class EasterEgg(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.jbot_db_global = bot.jbot_db_global

    def cog_unload(self):
        loop.run_until_complete(self.jbot_db_global.close_db())

    async def cog_before_invoke(self, ctx):
        try:
            got_list = (await self.jbot_db_global.res_sql("SELECT * FROM easteregg WHERE user_id=?", (ctx.author.id,)))[0]
        except IndexError:
            await self.jbot_db_global.exec_sql("INSERT INTO easteregg(user_id) VALUES (?)", (ctx.author.id,))

    @commands.command(name="이스터에그")
    async def easteregg(self, ctx):
        num = 1
        embed = discord.Embed(title="찾은 이스터에그", description=f"{ctx.author.mention}님은 얼마나 찾으셨을까요?")
        got_list = (await self.jbot_db_global.res_sql("SELECT * FROM easteregg WHERE user_id=?", (ctx.author.id,)))[0]
        for k, v in got_list.items():
            if k != "user_id":
                if v == 0:
                    x = "???"
                else:
                    x = easteregg_how_to[k]
                embed.add_field(name=easteregg_info[k], value=x)
                num += 1
        await ctx.send(embed=embed)

    @commands.command(name="굴라크")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def gulag(self, ctx, amount: int = 1):
        if amount > 15:
            amount = 15
        if amount < 1:
            amount = 1
        gulag = self.bot.get_emoji(724630497250246709)
        await ctx.send(str(gulag) * amount)
        exist = await self.jbot_db_global.res_sql("SELECT gulag FROM easteregg WHERE user_id=?", (ctx.author.id,))
        if bool(exist[0]["gulag"]):
            return
        await self.jbot_db_global.exec_sql("UPDATE easteregg SET gulag=? WHERE user_id=?", (1, ctx.author.id))

    @commands.command(name="멋진굴라크")
    async def better_gulag(self, ctx):
        await ctx.send("𝕲𝖚𝖑𝖆𝖌")

    @commands.command(name="아무말")
    async def any_horse(self, ctx):
        responses = ['아무말',
                     '아아무말',
                     '아아아무말',
                     '아아아아무말',
                     '말무아',
                     '<:any_horse:714357197227819132>',
                     '<:any_horses:714357346029273148>',
                     'https://cdn.discordapp.com/attachments/568962070230466573/714854748754280582/ddd84f9331954aae.png']
        await ctx.send(f'{random.choice(responses)}')
        exist = await self.jbot_db_global.res_sql("SELECT anyhorse FROM easteregg WHERE user_id=?", (ctx.author.id,))
        if bool(exist[0]["anyhorse"]):
            return
        await self.jbot_db_global.exec_sql("UPDATE easteregg SET anyhorse=? WHERE user_id=?", (1, ctx.author.id))


def setup(bot: CustomClient):
    bot.add_cog(EasterEgg(bot))
