import discord
import json
import koreanbots
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
        with open("bot_settings.json", "r") as f:
            bot_settings = json.load(f)
            token = bot_settings["koreanbots_token"]
        self.client = koreanbots.Client(self.bot, token, postCount=False)

    async def cog_before_invoke(self, ctx):
        try:
            res = await self.client.getVote(ctx.author.id)
            if res.response["voted"]:
                return
        except koreanbots.NotFound:
            pass
        embed = discord.Embed(title="잠시만요!",
                              description="아직 코리안봇에서 제이봇에게 하트를 누르지 않으셨네요...\n지금 [여기를 눌러서](https://koreanbots.dev/bots/622710354836717580) 코리안봇에 투표해주세요!",
                              color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.group(name="도움", description="봇의 도움말 명령어를 출력합니다.", aliases=["도움말", "help"])
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
    async def help_by_category(self, ctx, category_name: str):
        base_embed = discord.Embed(title="명령어 리스트", description="카테고리별 명령어 리스트\n필수 항목은 [] 이고 꼭 채워야 합니다. 선택 항목은 () 이고 채우지 않아도 됩니다.", color=discord.Color.from_rgb(225, 225, 225))
        if category_name not in cog_names.values():
            return await ctx.send(f"`{category_name}`은(는) 존재하지 않는 카테고리입니다.")
        selected = None
        for k, v in cog_names.items():
            if v == category_name:
                selected = k
        selected_cmds = [(x, y.get_commands()) for x, y in self.bot.cogs.items() if x == selected][0][1]
        embed_list = []
        curr_embed = base_embed.copy()
        count = 0
        for x in selected_cmds:
            if count != 0 and count % 5 == 0:
                embed_list.append(curr_embed)
                curr_embed = base_embed.copy()
            if x.description is None:
                continue
            curr_embed.add_field(name=x.name, value=str(x.description)+"\n사용법: "+(str(x.usage) if x.usage else f"`{x.name}`")+"\n에일리어스: " + (', '.join(x.aliases) if bool(x.aliases) else "없음"), inline=False)
            count += 1
        embed_list.append(curr_embed)
        await page.start_page(self.bot, ctx=ctx, lists=embed_list, embed=True)

    @help.command(name="검색")
    async def help_search(self, ctx, cmd_name):
        cogs = [(x, y.get_commands()) for x, y in self.bot.cogs.items()]
        for x in cogs:
            for n in x[1]:
                if cmd_name == n.name:
                    embed = discord.Embed(title=f"{cmd_name} 명렁어 정보", description=str(n.description), color=discord.Color.from_rgb(225, 225, 225))
                    embed.add_field(name="사용법", value=str(n.usage) if n.usage else f"`{n.name}`", inline=False)
                    embed.add_field(name="에일리어스", value=', '.join(n.aliases) if bool(n.aliases) else "없음", inline=False)
                    return await ctx.send(embed=embed)
        await ctx.send(f"`{cmd_name}`(은)는 없는 명령어입니다.")


def setup(bot):
    bot.add_cog(Help(bot))
