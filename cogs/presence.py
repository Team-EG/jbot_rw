import discord
import asyncio
import websockets
from discord.ext import commands
from discord.ext import tasks


class Presence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.presence_cycle.start()

    def cog_unload(self):
        self.presence_cycle.cancel()

    @tasks.loop()
    async def presence_cycle(self):
        while True:
            act_list = ["'제이봇 도움'이라고 말해보세요!",
                        f"{len(self.bot.guilds)}개 서버에서 작동",
                        f"{len(list(self.bot.get_all_members()))} 유저들과 함께"]
            for x in act_list:
                try:
                    await self.bot.change_presence(activity=discord.Game(str(x)))
                    await asyncio.sleep(5)
                except asyncio.streams.IncompleteReadError or discord.ConnectionClosed or websockets.exceptions.ConnectionClosedError:
                    print("Failed Changing. Retrying...")
                    await asyncio.sleep(5)
                    await self.bot.change_presence(activity=discord.Game(str(x)))
                    await asyncio.sleep(5)

    @presence_cycle.before_loop
    async def before_loop_start(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Presence(bot))
