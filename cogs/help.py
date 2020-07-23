import discord
import json
from discord.ext import commands
from modules import page

cog_names = {
    "Help": "도움",
    "Admin": "관리자",
    "Utils": "유틸리티",
    "Level": "레벨",
    "EasterEgg": "이스터에그",
    "Credit": "크레딧",
    "Dev": "개발자",
    "Error": "오류",
    "Spam": "도배",
    "Presence": "상태",
    "Music": "뮤직",
    "GuildSetup": "설정",
    "ServerLog": "서버 로그"
}
prohibited_cogs = ["Dev", "Error", "Presence", "EasterEgg"]


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="도움", aliases=["도움말", "help"])
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            base_embed = discord.Embed(title="명령어 리스트", description="한눈에 보는 명령어 리스트", color=discord.Color.from_rgb(225, 225, 225))
            cogs = [(x, y.get_commands()) for x, y in self.bot.cogs.items()]
            for x in cogs:
                if x[0] in prohibited_cogs:
                    continue
                if not bool(x[1]):
                    continue
                base_embed.add_field(name=cog_names[x[0]], value='`' + '`, `'.join([c.name for c in x[1]]) + '`', inline=False)
            await ctx.send(embed=base_embed)

    @help.command(name="카테고리")
    async def help_by_category(self, ctx):
        pass

    @help.command(name="검색")
    async def help_search(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Help(bot))
