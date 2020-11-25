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
import typing
import asyncio
import os
import json
from discord.ext import commands
from modules import admin, custom_errors
from modules.cilent import CustomClient

loop = asyncio.get_event_loop()


class Admin(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.jbot_db_global = bot.jbot_db_global
        self.jbot_db_warns = bot.jbot_db_warns

    async def cog_check(self, ctx):
        if ctx.invoked_with in ["도배리셋"]:
            if ctx.author.guild_permissions.manage_messages:
                return True
        if ctx.invoked_with in ["추방", "경고", "경고삭제", "정리", "뮤트", "언뮤트"]:
            if ctx.author.guild_permissions.kick_members:
                return True
        if ctx.invoked_with in ["차단"]:
            if ctx.author.guild_permissions.ban_members:
                return True
        if ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner:
            return True
        raise custom_errors.NotAdmin

    @commands.command(name="도배리셋", description="도배 카운트를 리셋합니다.", usage="`도배리셋 (유저)`")
    async def reset_spam(self, ctx, tgt: discord.Member = None):
        if not os.path.isfile(f"temp/{ctx.guild.id}_spam.json"):
            return await ctx.send("도배 기록이 없거나 도배 기능이 꺼져있습니다.")
        if tgt is None:
            os.remove(f"temp/{ctx.guild.id}_spam.json")
            return await ctx.send("도배 카운트 리셋이 완료되었습니다.")
        with open(f"temp/{ctx.guild.id}_spam.json", "r") as f:
            time_data = json.load(f)
        if str(tgt.id) not in time_data.keys():
            return await ctx.send("선택한 유저는 도배 카운트 기록에 없습니다.")
        del time_data[str(tgt.id)]
        with open(f"temp/{ctx.guild.id}_spam.json", "w") as f:
            json.dump(time_data, f, indent=4)
        await ctx.send("선택한 유저의 도배 카운트 리셋이 완료되었습니다.")

    @commands.command(name="뮤트", description="선택한 유저를 뮤트합니다.", usage="`뮤트 [유저] (사유)`")
    async def mute(self, ctx, member: discord.Member, *, reason="없음"):
        mute_role_id = await self.jbot_db_global.res_sql("SELECT mute_role FROM guild_setup WHERE guild_id=?", (ctx.guild.id,))
        if not bool(mute_role_id[0]["mute_role"]):
            return await ctx.send("먼저 뮤트 역할을 등록해주세요.")
        mute_role = ctx.guild.get_role(mute_role_id[0]["mute_role"])
        await member.add_roles(mute_role, reason=reason)
        await ctx.send(f"{member.mention}을 뮤트했습니다. (사유: {reason})")

    @commands.command(name="언뮤트", description="선택한 유저를 언뮤트합니다.", usage="`언뮤트 [유저]`")
    async def unmute(self, ctx, member: discord.Member):
        mute_role_id = await self.jbot_db_global.res_sql("SELECT mute_role FROM guild_setup WHERE guild_id=?", (ctx.guild.id,))
        if not bool(mute_role_id[0]["mute_role"]):
            return await ctx.send("먼저 뮤트 역할을 등록해주세요.")
        mute_role = ctx.guild.get_role(mute_role_id[0]["mute_role"])
        await member.remove_roles(mute_role)
        await ctx.send(f"{member.mention}을 언뮤트했습니다.")

    @commands.command(name="경고", description="선택한 유저에게 경고를 부여합니다.", usage="`경고 [유저] (사유)`")
    async def warn(self, ctx, member: discord.Member, *, reason="없음"):
        await admin.warn(self.jbot_db_global, self.jbot_db_warns, member, reason=reason, issued_by=ctx.author, ctx=ctx)

    @commands.command(name="경고삭제", description="선택한 경고를 삭제합니다.", usage="`경고삭제 [유저] [경고번호]`")
    async def remove_warn(self, ctx, member: discord.Member, num):
        await admin.remove_warn(self.jbot_db_global, self.jbot_db_warns, member, num, ctx=ctx)

    @commands.command(name="추방", description="선택한 유저를 추방합니다.", usage="`추방 [유저] (사유)`")
    async def kick(self, ctx, member: discord.Member, *, reason="없음"):
        await member.send(f"`{ctx.author.guild.name}`에서 추방되었습니다. (사유: {reason}, {ctx.author}이(가) 추방함)")
        await member.kick(reason=reason+f" ({ctx.author}이(가) 추방함)")
        await ctx.send(f"`{member}`을(를) 추방했습니다. (사유: {reason})")

    @commands.command(name="차단", description="선택한 유저를 차단합니다.", usage="`차단 [유저] (사유)`")
    async def ban(self, ctx, member: discord.Member, *, reason="없음"):
        await member.send(f"`{ctx.author.guild.name}`에서 차단되었습니다. (사유: {reason}, {ctx.author}이(가) 차단함)")
        await member.send("https://www.youtube.com/watch?v=FXPKJUE86d0")
        await member.ban(reason=reason + f" ({ctx.author}이(가) 차단함)")
        await ctx.send(f"`{member}`을(를) 차단했습니다. (사유: {reason})")

    @commands.group(name="정리", description="메시지를 대량으로 삭제합니다.", usage="`정리 도움` 명령어를 참고해주세요.")
    async def purge(self, ctx, amount: typing.Optional[int] = None):
        if ctx.invoked_subcommand is None and amount is not None:
            if amount > 100:
                return await ctx.send("오류 방지를 위해 메시지 삭제의 최대 개수는 100개로 제한됩니다.")
            await ctx.channel.purge(limit=amount+1)
            msg = await ctx.send(f"메시지 {amount}개를 정리했습니다.\n`이 메시지는 5초 후 삭제됩니다.`")
            await msg.delete(delay=5)

    @purge.command(name="도움")
    async def purge_help(self, ctx):
        embed = discord.Embed(title="정리 명령어 도움말", color=discord.Color.from_rgb(225, 225, 225))
        embed.add_field(name="정리 [개수]", value="해당 개수만큼의 메시지를 삭제합니다.", inline=False)
        embed.add_field(name="정리 유저 [대상 유저]", value="선택한 유저가 보낸 메시지들을 삭제합니다.", inline=False)
        embed.add_field(name="정리 메시지 [메시지 ID]", value="선택한 메시지까지의 모든 메시지들을 삭제합니다.", inline=False)
        await ctx.send(embed=embed)

    @purge.command(name="유저", description="선택한 유저가 보낸 메시지들을 삭제합니다.")
    async def purge_user(self, ctx, user: discord.Member, limit: int):
        if limit > 100:
            return await ctx.send("오류 방지를 위해 검색되는 메시지 최대 범위는 100개로 제한됩니다.")
        tgt_list = []
        async for message in ctx.channel.history(limit=limit):
            if message.author == user:
                tgt_list.append(message)
        await ctx.channel.delete_messages(tgt_list)
        msg = await ctx.send(f"{user.mention}(이)가 보낸 메시지 {len(tgt_list)}개를 정리했습니다.\n`이 메시지는 5초 후 삭제됩니다.`")
        await msg.delete(delay=5)

    @purge.command(name="메시지", description="선택한 메시지까지의 모든 메시지들을 삭제합니다.")
    async def purge_msg(self, ctx, tgt_msg: discord.Message):
        tgt_list = [tgt_msg]
        async for message in ctx.channel.history(after=tgt_msg):
            tgt_list.append(message)
        await ctx.channel.delete_messages(tgt_list)
        msg = await ctx.send(f"`{tgt_msg.id}`부터의 메시지를 정리했습니다.\n`이 메시지는 5초 후 삭제됩니다.`")
        await msg.delete(delay=5)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_msgs = await self.jbot_db_global.res_sql("""SELECT welcome_channel, greet, greetpm FROM guild_setup WHERE guild_id=?""", (member.guild.id,))
        if not bool(welcome_msgs):
            return
        if bool(welcome_msgs[0]["greet"]):
            channel = member.guild.get_channel(int(welcome_msgs[0]["welcome_channel"]))
            await channel.send((welcome_msgs[0]["greet"]).replace("{mention}", member.mention))
        if bool(welcome_msgs[0]["greetpm"]):
            await member.send((welcome_msgs[0]["greetpm"]).replace("{name}", member.name))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        bye_msgs = await self.jbot_db_global.res_sql("""SELECT welcome_channel, bye FROM guild_setup WHERE guild_id=?""", (member.guild.id,))
        if not bool(bye_msgs):
            return
        if bool(bye_msgs[0]["bye"]):
            channel = member.guild.get_channel(int(bye_msgs[0]["welcome_channel"]))
            await channel.send((bye_msgs[0]["bye"]).replace("{name}", member.name))

    """@commands.command(name="역할정리")
    async def clr_roles(self, ctx):
        roles = ctx.guild.roles
        for x in roles:
            if x.name == "new role":
                await x.delete()
        await ctx.send("완료")"""


def setup(bot: CustomClient):
    bot.add_cog(Admin(bot))
