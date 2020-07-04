import discord
import typing
import asyncio
from discord.ext import commands
from modules import admin, jbot_db, custom_errors

loop = asyncio.get_event_loop()


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_warns = jbot_db.JBotDB("jbot_db_warns")

    def cog_unload(self):
        loop.run_until_complete(self.jbot_db_warns.close_db())

    async def cog_check(self, ctx):
        if ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner:
            return True
        raise custom_errors.NotAdmin

    @commands.command(name="경고")
    async def warn(self, ctx, member: discord.Member, *, reason="없음"):
        await admin.warn(self.jbot_db_warns, member, reason=reason, issued_by=ctx.author, ctx=ctx)

    @commands.group(name="정리")
    async def purge(self, ctx, amount: typing.Optional[int] = None):
        if ctx.invoked_subcommand is None and amount is not None:
            if amount > 100:
                return await ctx.send("오류 방지를 위해 메시지 삭제의 최대 개수는 100개로 제한됩니다.")
            await ctx.channel.purge(limit=amount+1)
            msg = await ctx.send(f"메시지 {amount}개를 정리했습니다.\n`이 메시지는 5초 후 삭제됩니다.`")
            await msg.delete(delay=5)

    @purge.command(name="유저")
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

    @purge.command(name="메시지")
    async def purge_msg(self, ctx, tgt_msg: discord.Message):
        tgt_list = [tgt_msg]
        async for message in ctx.channel.history(after=tgt_msg):
            tgt_list.append(message)
        await ctx.channel.delete_messages(tgt_list)
        msg = await ctx.send(f"`{tgt_msg.id}`부터의 메시지를 정리했습니다.\n`이 메시지는 5초 후 삭제됩니다.`")
        await msg.delete(delay=5)

    """@commands.command(name="역할정리")
    async def clr_roles(self, ctx):
        roles = ctx.guild.roles
        for x in roles:
            if x.name == "new role":
                await x.delete()
        await ctx.send("완료")"""


def setup(bot):
    bot.add_cog(Admin(bot))
