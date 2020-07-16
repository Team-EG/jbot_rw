import discord
import json
import psutil
import os
import datetime
import asyncio
from discord.ext import commands
from modules import custom_errors
from modules import jbot_db
from modules import confirm

loop = asyncio.get_event_loop()


class Dev(commands.Cog):
    def __init__(self, bot):
        with open("bot_settings.json", "r") as f:
            self.bot_settings = json.load(f)
        self.bot = bot
        self.jbot_db_global = jbot_db.JBotDB("jbot_db_global")

    def cog_unload(self):
        loop.run_until_complete(self.jbot_db_global.close_db())

    async def cog_check(self, ctx):
        if ctx.author.id not in self.bot_settings["whitelist"]:
            raise custom_errors.NotWhitelisted
        return True

    @commands.command(name="건의")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def tix(self, ctx, *, gulag):
        msg = await ctx.send("정말로 건의사항을 보낼까요?\n장난으로 보내는 등 불필요하게 건의사항을 보내는 경우 건의사항 기능을 사용할 수 없게 될 수도 있습니다.")
        res = await confirm.confirm(self.bot, ctx, msg)
        if res is True:
            owner = self.bot.get_user(288302173912170497)
            await owner.send(f"`건의사항 ({ctx.author} / {ctx.author.id})`")
            await owner.send(gulag)
            return await ctx.send("성공적으로 건의사항을 보냈습니다!")
        await ctx.send("건의사항 보내기가 취소되었습니다.")

    @commands.command(name="공지")
    async def announcement(self, ctx, t, *, ann):
        if not ctx.author.id == 288302173912170497:
            return
        with open("cache/guild_setup.json", "r") as f:
            data = json.load(f)
        for k in data:
            try:
                if data[k]["announcement"] is not None:
                    v = data[k]["announcement"]
                    target_channel = self.bot.get_guild(int(k)).get_channel(int(v))
                    embed = discord.Embed(title='제이봇 공지', colour=discord.Color.red())
                    embed.set_footer(text=str(ctx.author.name), icon_url=ctx.author.avatar_url)
                    embed.add_field(name=str(t), value=str(ann), inline=False)
                    await target_channel.send(embed=embed)
            except KeyError:
                pass
        await ctx.send("공지를 모두 보냈습니다!")

    @commands.group(name="개발자", aliases=["dev"])
    async def dev(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="개발자 전용 명령어 리스트", description="대충 아무 명령어")
            embed.add_field(name="캐시리셋", value="캐시를 리셋합니다.")
            embed.add_field(name="상태설정", value="봇의 상태를 변경합니다.")
            await ctx.send(embed=embed)

    @dev.command(name="캐시리셋")
    async def cache_reset(self, ctx):
        await db_cache.reload_cache(self.jbot_db_global, "guild_setup")
        await ctx.send("캐시 리셋완료")

    @dev.command(name="상태설정")
    async def set_status(self, ctx, status=None):
        await self.bot.change_presence(activity=discord.Game(str(status)))
        await ctx.send("완료")

    @dev.command(name="길드리스트")
    async def get_guild_list(self, ctx):
        guild_list = self.bot.guilds
        embed = discord.Embed(title="제이봇 길드 리스트", description=str(len(guild_list))+" 개")
        for x in guild_list:
            embed.add_field(name=x.name, value=f"소유자: {x.owner}\n유저수: {len(x.members)}")
        await ctx.send(embed=embed)

    @dev.command(name="서버상태")
    async def check_server(self, ctx):
        embed = discord.Embed(title="제이봇 서버 상태", description="~~서버컴 바꾸고 싶다~~")
        memory_usage_dict = dict(psutil.virtual_memory()._asdict())
        memory_usage_percent = memory_usage_dict['percent']
        uptime_sys = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        cpu_usage = psutil.cpu_percent(interval=None, percpu=True)
        p = psutil.Process(os.getpid())
        uptime_bot = datetime.datetime.now() - datetime.datetime.fromtimestamp(p.create_time())
        #temp = psutil.sensors_temperatures()
        embed.add_field(name="CPU 사용량", value=str(cpu_usage))
        embed.add_field(name="램 사용량", value=str(memory_usage_percent) + "%")
        embed.add_field(name="업타임", value=f"서버: {uptime_sys}\n봇: {uptime_bot}")
        #embed.add_field(name="온도", value=str(temp))
        await ctx.send(embed=embed)

    @dev.command(name="DB테이블확인")
    async def check_table_exist(self, ctx, db_name, table_name):
        res = None # await sdb.check_if_table_exist(db_name, table_name)
        await ctx.send(res)

    @dev.command(name="임시폴더리셋")
    async def temp_reset(self, ctx):
        temp_file_list = os.listdir("temp")
        for x in temp_file_list:
            os.remove("temp/"+x)
        await ctx.send("완료")

    @dev.command(name="eval", aliases=["이발"])
    async def eval(self, ctx, *, line: str):
        res = eval(line)
        await ctx.send(res)

    @dev.command(name="exec", aliases=["이색"])
    async def exec(self, ctx, *, line: str):
        res = eval(line)
        await ctx.send(res)


def setup(bot):
    bot.add_cog(Dev(bot))
