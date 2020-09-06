import discord
from discord.ext import commands
from modules import custom_errors


class PartTime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_global = bot.jbot_db_global

    async def cog_check(self, ctx: commands.Context):
        acc_list = await self.jbot_db_global.res_sql("""SELECT * FROM game WHERE user_id=?""", (ctx.author.id,))
        if not bool(acc_list):
            await ctx.send("계정이 존재하지 않습니다. 먼저 계정을 생성해주세요")
            raise custom_errors.IgnoreThis
        return True

    @commands.group(name="알바", description="알바를 합니다.", usage="`알바 [할 알바]`\n(할 수 있는 알바 리스트는 `알바 도움` 명령어를 참고해주세요.)")
    async def part_time(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.part_time_help.__call__(ctx)

    @part_time.command(name="도움")
    async def part_time_help(self, ctx):
        embed = discord.Embed(title="알바 기능 도움말", color=discord.Color.from_rgb(225, 225, 225))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(PartTime(bot))
