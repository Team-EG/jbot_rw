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
import koreanbots
import os
import asyncio
from discord.ext import commands
from modules import utils
from modules.cilent import CustomClient

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
    "Tasks": "태스크",
    "Music": "뮤직",
    "GuildSetup": "설정",
    "ServerLog": "서버 로그",
    "Game": "게임",
    "Stock": "주식",
    "PartTime": "알바"
}
prohibited_cogs = ["Dev", "Error", "Tasks", "EasterEgg", "ServerLog", "Spam"]


class Help(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.koreanbots = bot.koreanbots
        self.sent_users = []

    async def cog_after_invoke(self, ctx):
        if ctx.author.id in self.sent_users:
            return
        try:
            res = await self.koreanbots.getVote(ctx.author.id)
            if res.response["voted"]:
                return
        except koreanbots.NotFound:
            pass
        finally:
            self.sent_users.append(ctx.author.id)
            if len(self.sent_users) >= 10:
                self.sent_users = []
        embed = discord.Embed(title="잠시만요!",
                              description="도움말은 잘 보셨나요? 도움말을 보시는 동안 잠깐 확인해봤는데 아직 코리안봇에서 제이봇에게 하트를 누르지 않으셨네요...\n"
                                          "지금 [여기를 눌러서](https://koreanbots.dev/bots/622710354836717580) 제이봇에게 하트를 눌러주세요!\n"
                                          "잠깐만 시간을 내서 눌러주신다면 개발자에게 조금이지만 도움이 됩니다.",
                              color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.group(name="도움", description="봇의 도움말 명령어를 출력합니다.", aliases=["도움말", "help"])
    async def help(self, ctx, tgt=None):
        if ctx.invoked_subcommand is None:
            if tgt:
                if tgt in cog_names.values():
                    return await self.help_by_category.__call__(ctx, tgt)
                return await self.help_search.__call__(ctx, tgt)
            base_embed = discord.Embed(title="명령어 리스트",
                                       description="한눈에 보는 명령어 리스트\n"
                                                   "자세한 명령어 정보는 `도움 카테고리 [카테고리 이름]` 또는 `도움 검색 [명령어 이름]`을 참고해주세요.\n"
                                                   "봇 가이드는 `도움 가이드` 명령어를 참고해주세요.",
                                       color=discord.Color.from_rgb(225, 225, 225))
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
            curr_embed.add_field(name=x.name,
                                 value=str(x.description)+"\n사용법: "+(str(x.usage) if x.usage else f"`{x.name}`")+"\n에일리어스: " + (', '.join(x.aliases) if bool(x.aliases) else "없음"),
                                 inline=False)
            count += 1
        embed_list.append(curr_embed)
        await utils.start_page(self.bot, ctx=ctx, lists=embed_list, embed=True)

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

    @help.command(name="가이드")
    async def help_guide(self, ctx):
        up = "⬆"
        down = "⬇"
        load = "⏺"
        stop = "⏹"
        emoji_list = [up, down, load, stop]
        select_embed = discord.Embed(title="사용 가능한 가이드 리스트", description="보고 싶으신 가이드를 선택해주세요.", color=discord.Color.from_rgb(225, 225, 225))
        msg = await ctx.send("잠시만 기다려주세요...")
        for x in emoji_list:
            await msg.add_reaction(x)
        available_guides = os.listdir("help")
        selected = available_guides[0]
        selected_num = 0

        def check(reaction, user):
            return user == ctx.author and str(reaction) in emoji_list and reaction.message.id == msg.id

        global reaction
        while True:
            tgt_embed = select_embed.copy()
            init_num = 1
            for k in available_guides:
                if k == selected:
                    k = "▶" + k
                tgt_embed.add_field(name=f"가이드 {init_num}", value=k.replace('_', ' '), inline=False)
                init_num += 1
            await msg.edit(content=None, embed=tgt_embed)
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                await msg.edit(content="시간이 만료되었습니다.", embed=None)
                try:
                    await msg.clear_reactions()
                except discord.Forbidden:
                    for e in emoji_list:
                        await msg.remove_reaction(e, msg.author)
                return

            if str(reaction) == down:
                if selected_num + 1 == len(available_guides):
                    selected_num = 0
                    selected = available_guides[0]
                else:
                    selected_num += 1
                    selected = available_guides[selected_num]
            elif str(reaction) == up:
                if selected_num == 0:
                    selected_num = len(available_guides)
                    selected = available_guides[-1][0]
                else:
                    selected_num -= 1
                    selected = available_guides[selected_num]
            elif str(reaction) == stop:
                await msg.clear_reactions()
                return
            elif str(reaction) == load:
                await msg.clear_reactions()
                await msg.edit(content="가이드를 불러오고 있습니다. 잠시만 기다려주세요...", embed=None)
                break

        guide_name = selected
        embed_list = []
        base_embed = discord.Embed(title=f"{guide_name.replace('_', ' ')} 가이드", color=discord.Color.from_rgb(225, 225, 225))
        guide_dir = f"help/{guide_name}"
        count = 0
        guide_pages = [x for x in os.listdir(guide_dir) if x.endswith(".txt")]
        for x in guide_pages:
            count += 1
            with open(guide_dir + "/" + x, "r", encoding="UTF-8") as f:
                content = f.read()
            tgt_embed = base_embed.copy()
            tgt_embed.description = content
            tgt_embed.set_footer(text=f"페이지 {count}/{len(guide_pages)}")
            embed_list.append(tgt_embed)
        await msg.delete()
        await utils.start_page(self.bot, ctx=ctx, lists=embed_list, embed=True)


def setup(bot: CustomClient):
    bot.add_cog(Help(bot))
