import discord
import typing
import asyncio
from discord.ext import commands
from modules import admin, jbot_db, custom_errors

loop = asyncio.get_event_loop()


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_global = jbot_db.JBotDB("jbot_db_global")
        self.jbot_db_warns = jbot_db.JBotDB("jbot_db_warns")

    def cog_unload(self):
        loop.run_until_complete(self.jbot_db_warns.close_db())

    async def cog_check(self, ctx):
        if ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner:
            return True
        raise custom_errors.NotAdmin

    @commands.command(name="경고", description="선택한 유저에게 경고를 부여합니다.")
    async def warn(self, ctx, member: discord.Member, *, reason="없음"):
        await admin.warn(self.jbot_db_global, self.jbot_db_warns, member, reason=reason, issued_by=ctx.author, ctx=ctx)

    @commands.command(name="추방", description="선택한 유저를 추방합니다.")
    async def kick(self, ctx, member: discord.Member, *, reason="없음"):
        await member.send(f"`{ctx.author.guild.name}`에서 추방되었습니다. (사유: {reason}, {ctx.author}이(가) 추방함)")
        await member.kick(reason=reason+f" ({ctx.author}이(가) 추방함)")
        await ctx.send(f"`{member}`을(를) 추방했습니다. (사유: {reason})")

    @commands.command(name="차단", description="선택한 유저를 차단합니다.")
    async def ban(self, ctx, member: discord.Member, *, reason="없음"):
        await member.send(f"`{ctx.author.guild.name}`에서 차단되었습니다. (사유: {reason}, {ctx.author}이(가) 차단함)")
        await member.send("https://www.youtube.com/watch?v=FXPKJUE86d0")
        await member.ban(reason=reason + f" ({ctx.author}이(가) 차단함)")
        await ctx.send(f"`{member}`을(를) 차단했습니다. (사유: {reason})")

    @commands.group(name="정리", description="메시지를 대량으로 삭제합니다.")
    async def purge(self, ctx, amount: typing.Optional[int] = None):
        if ctx.invoked_subcommand is None and amount is not None:
            if amount > 100:
                return await ctx.send("오류 방지를 위해 메시지 삭제의 최대 개수는 100개로 제한됩니다.")
            await ctx.channel.purge(limit=amount+1)
            msg = await ctx.send(f"메시지 {amount}개를 정리했습니다.\n`이 메시지는 5초 후 삭제됩니다.`")
            await msg.delete(delay=5)

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


def setup(bot):
    bot.add_cog(Admin(bot))
