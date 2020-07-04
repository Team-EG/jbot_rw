import discord
import json
from discord.ext import commands
from modules import page


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="도움", aliases=["도움말", "help"])
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            embed1 = discord.Embed(title="명령어 리스트", description="도움 명령어")
            with open("help/help.json", "r", encoding="UTF-8") as f:
                help_list = json.load(f)
            count = 0
            for k in list(help_list.keys()):
                v = help_list[k]
                embed1.add_field(name=k, value=f"{v['desc']}\n에일리어스: `{v['aliases']}`", inline=False)
                count += 1
                help_list.pop(k)
                if count == 4:
                    break
            embed2 = discord.Embed(title="명령어 리스트", description="도움 명령어")
            for k, v in help_list.items():
                v = help_list[k]
                embed2.add_field(name=k, value=f"{v['desc']}\n에일리어스: `{v['aliases']}`", inline=False)
            embed_list = [embed1, embed2]
            await page.start_page(self.bot, ctx, embed_list, 30, embed=True)

    @help.command(name="관리")
    async def admin(self, ctx):
        pass

    @help.command(name="뮤직")
    async def music(self, ctx):
        pass

    @help.command(name="기타")
    async def etc(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Help(bot))
