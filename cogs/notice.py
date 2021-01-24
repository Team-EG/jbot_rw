import os
import time
import datetime
import discord
from discord.ext import commands
from modules import utils
from modules.cilent import CustomClient


class Notice(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.bot._before_invoke = self.check_notice
        self.sent = {}

    async def check_notice(self, ctx: commands.Context):
        if ctx.invoked_with in ["알림"]:
            return
        data = await self.bot.jbot_db_global.res_sql("""SELECT last_watch FROM notice WHERE user_id=?""", (ctx.author.id,))
        if not data:
            await self.bot.jbot_db_global.exec_sql("""INSERT INTO notice VALUES (?, 0)""", (ctx.author.id,))
            data = await self.bot.jbot_db_global.res_sql("""SELECT last_watch FROM notice WHERE user_id=?""", (ctx.author.id,))
        last_watch = data[0]["last_watch"]
        last_notice = list(reversed(sorted([int(x.split(".")[0]) for x in os.listdir("notice") if x.endswith(".txt")])))[0]
        if last_notice > last_watch:
            if ctx.author.id in self.sent:
                if self.sent[ctx.author.id] + 60*60 > time.time():
                    return
            embed = discord.Embed(title="새로운 제이봇 알림이 있어요!",
                                  description="아직 읽지 않으신 알림이 있네요. `제이봇 알림` 명령어로 확인해보세요!",
                                  color=discord.Color.from_rgb(225, 225, 225),
                                  timestamp=ctx.message.created_at).\
                set_footer(text="만약에 알림을 1시간 뒤에도 확인하시지 않았다면 다시 알려드릴께요!")
            await ctx.send(embed=embed)
            self.sent[ctx.author.id] = round(time.time())

    @commands.group(name="알림", description="제이봇의 알림을 최신부터 보여드립니다.")
    async def notice(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            notice_list = list(reversed([x for x in os.listdir("notice") if x.endswith(".txt")]))
            base_embed = discord.Embed(title="제이봇 알림", color=discord.Color.from_rgb(225, 225, 225))
            _list = []
            latest = int(notice_list[0].split(".")[0])
            for x in notice_list:
                with open(f"notice/{x}", "r", encoding="UTF-8") as f:
                    text = f.read()
                title, description = [x.strip() for x in text.split("__TITLE-DESCRIPTION__")]
                embed = base_embed.copy()
                embed.add_field(name=title, value=description)
                embed.timestamp = datetime.datetime.fromtimestamp(int(x.split(".")[0]), tz=datetime.timezone(datetime.timedelta(hours=9)))
                _list.append(embed)
            await utils.start_page(self.bot, ctx, _list, embed=True)
            await self.bot.jbot_db_global.exec_sql("""UPDATE notice SET last_watch=? WHERE user_id=?""", (latest, ctx.author.id))

    @notice.command(name="히스토리")
    async def notice_history(self, ctx: commands.Context):
        pass


def setup(bot):
    bot.add_cog(Notice(bot))
