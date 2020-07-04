import discord
import random
import asyncio
from discord.ext import commands
from modules import jbot_db

loop = asyncio.get_event_loop()


class EasterEgg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_global = jbot_db.JBotDB("jbot_db_global")

    def cog_unload(self):
        loop.run_until_complete(self.jbot_db_global.close_db())

    @commands.command(name="이스터에그")
    async def easteregg(self, ctx):
        global easteregg_info, easteregg_how_to
        num = 1
        embed = discord.Embed(title="찾은 이스터에그", description=f"{ctx.author.mention}님은 얼마나 찾으셨을까요?")
        easteregg_info = (await self.jbot_db_global.get_from_db("easteregg", "*", "user_id", "NOTUSER"))[0]
        easteregg_how_to = (await self.jbot_db_global.get_from_db("easteregg", "*", "user_id", "NOTUSER2"))[0]
        try:
            got_list = (await self.jbot_db_global.get_from_db("easteregg", "*", "user_id", str(ctx.author.id)))[0]
        except IndexError:
            await self.jbot_db_global.insert_db("easteregg", "user_id", str(ctx.author.id))
            got_list = (await self.jbot_db_global.get_from_db("easteregg", "*", "user_id", str(ctx.author.id)))[0]
        for k, v in got_list.items():
            if not k == "user_id":
                if v == "False":
                    x = "???"
                else:
                    x = easteregg_how_to[k]
                embed.add_field(name=easteregg_info[k], value=x)
                num += 1
        await ctx.send(embed=embed)

    @commands.command(name="굴라크")
    async def gulag(self, ctx, amount: int = 1):
        if amount > 15:
            amount = 15
        if amount < 1:
            amount = 1
        gulag = self.bot.get_emoji(658581939015385129)
        await ctx.send(str(gulag) * amount)
        await self.jbot_db_global.update_db("easteregg", "gulag", "True", "user_id", str(ctx.author.id))

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
        await self.jbot_db_global.update_db("easteregg", "anyhorse", "True", "user_id", str(ctx.author.id))


def setup(bot):
    bot.add_cog(EasterEgg(bot))
