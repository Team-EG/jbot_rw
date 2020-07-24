import discord
import asyncio
from discord.ext import commands
from modules import custom_errors
from modules import jbot_db
from modules import admin

loop = asyncio.get_event_loop()
emoji_list = []


class GuildSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_global = jbot_db.JBotDB("jbot_db_global")

    def cog_unload(self):
        loop.run_until_complete(self.jbot_db_global.close_db())

    async def cog_check(self, ctx):
        if not ctx.author == ctx.guild.owner:
            raise custom_errors.NotGuildOwner
        banned = ["True", "False", "None"]
        for x in banned:
            if x in str(ctx.message.content):
                raise custom_errors.IllegalString(banned)
        return True

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if guild is None:
            return
        await self.jbot_db_global.exec_sql("INSERT INTO guild_setup(guild_id) VALUES (?)", (guild.id,))

        """try:
            perms = discord.Permissions(send_messages=False)
            await guild.create_role(name="뮤트", colour=discord.Colour(0xff0000), permissions=perms)
            await asyncio.sleep(1)
            mute_role = discord.utils.get(guild.roles, name='뮤트')
            for i in guild.text_channels:
                await i.set_permissions(mute_role, send_messages=False)
        except commands.errors.BotMissingPermissions:
            pass"""

        await guild.owner.send(f'{guild.name}에 제이봇을 초대해주셔서 감사합니다.\n'
                               f'이 봇은 일부 기능을 위해 서버의 ID, 유저들의 ID를 DB에 저장하고, 서버에서의 이벤트들(메시지 삭제, 수정, 채널 생성, 편집, 삭제 등)을 확인합니다.\n'
                               f'만약에 이를 원하지 않는다면, 즉시 봇을 추방해주세요. 봇 추방 후에는 DB에서 서버 설정 관련 데이터가 즉시 삭제됩니다.\n'
                               f'봇 설정은 `제이봇 도움 관리` 명령어를 참고해주세요.\n'
                               f'혹시라도 제이봇을 사용하다가 문제가 발생하거나 문의할 것이 있다면 Team EG 디스코드 서버로 들어와주세요.\n'
                               f'-제이봇-')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild is None:
            return
        await self.jbot_db_global.exec_sql("DELETE FROM guild_setup WHERE guild_id=?", (guild.id,))

    @commands.group(name="설정", description="봇의 기능과 관련된 부분을 설정합니다.")
    async def settings(self, ctx):
        if ctx.invoked_subcommand is None:
            guild_data = (await self.jbot_db_global.res_sql("SELECT * FROM guild_setup WHERE guild_id=?", (ctx.guild.id,)))[0]
            for x in guild_data.keys():
                if guild_data[x] is None:
                    guild_data[x] = "없음"
                elif len(str(guild_data[x])) != 1:
                    pass
                elif bool(guild_data[x]) is False:
                    guild_data[x] = "아니요"
                elif bool(guild_data[x]) is True:
                    guild_data[x] = "네"
            log_channel = guild_data["log_channel"]
            ann_channel = guild_data["announcement"]
            welcome_channel = guild_data["welcome_channel"]
            mute_role = guild_data["mute_role"]
            if log_channel != "없음":
                log_channel = (ctx.guild.get_channel(int(log_channel))).mention
            if ann_channel != "없음":
                ann_channel = (ctx.guild.get_channel(int(ann_channel))).mention
            if welcome_channel != "없음":
                welcome_channel = (ctx.guild.get_channel(int(welcome_channel))).mention
            if mute_role != "없음":
                mute_role = (ctx.guild.get_role(int(mute_role))).mention
            embed = discord.Embed(title="현재 서버 설정",
                                  description=f"변경을 원하신다면 `{str(guild_data['prefix'])}설정 도움` 명령어를 참고해주세요.")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(name="프리픽스", value=str(guild_data["prefix"]))
            embed.add_field(name="대화 프리픽스", value=str(guild_data["talk_prefix"]))
            embed.add_field(name="서버 로그 채널", value=str(log_channel))
            embed.add_field(name="제이봇 공지 채널", value=str(ann_channel))
            embed.add_field(name="유저 환영 채널", value=str(welcome_channel))
            embed.add_field(name="유저 환영 인사", value=str(guild_data["greet"]))
            embed.add_field(name="유저 작별 인사", value=str(guild_data["bye"]))
            embed.add_field(name="유저 DM 환영 인사", value=str(guild_data["greetpm"]))
            embed.add_field(name="레벨 기능을 사용하나요?", value=str(guild_data["use_level"]))
            embed.add_field(name="도배 방지 기능을 사용하나요?", value=str(guild_data["use_antispam"]))
            embed.add_field(name="모든 서버와 동기화된 대화 데이터베이스를 사용하나요?", value=str(guild_data["use_globaldata"]))
            embed.add_field(name="뮤트 역할", value=str(mute_role))
            await ctx.send(embed=embed)

    @settings.command(name="프리픽스", aliases=["프리픽스교체"])
    async def prefix_change(self, ctx, prefix: str):
        tgt = "프리픽스"
        embed_ok = discord.Embed(title=f"{tgt} 변경", description="변경이 완료되었습니다.")
        embed_no = discord.Embed(title=f"{tgt} 변경", description="변경이 취소되었습니다.")
        embed_cancel = discord.Embed(title=f"{tgt} 변경", description="시간이 만료되었습니다.")
        embed_change = discord.Embed(title=f"{tgt} 변경", description=f"정말로 프리픽스를 `{prefix}`로 변경할까요?")
        msg = await ctx.send(embed=embed_change)
        await admin.update_setup(self.jbot_db_global, self.bot, ctx, msg, [embed_ok, embed_no, embed_cancel],
                                 "prefix", prefix)

    @settings.command(name="대화프픽")
    async def talk_prefix_change(self, ctx, prefix: str):
        tgt = "대화 프리픽스"
        embed_ok = discord.Embed(title=f"{tgt} 변경", description="변경이 완료되었습니다.")
        embed_no = discord.Embed(title=f"{tgt} 변경", description="변경이 취소되었습니다.")
        embed_cancel = discord.Embed(title=f"{tgt} 변경", description="시간이 만료되었습니다.")
        embed_change = discord.Embed(title=f"{tgt} 변경", description=f"정말로 대화 프리픽스를 `{prefix}`로 변경할까요?")
        msg = await ctx.send(embed=embed_change)
        await admin.update_setup(self.jbot_db_global, self.bot, ctx, msg, [embed_ok, embed_no, embed_cancel],
                                 "talk_prefix", prefix)

    @settings.command(name="로그")
    async def log_channel_change(self, ctx, channel: discord.TextChannel = None):
        tgt = "서버 로그 채널"
        embed_ok = discord.Embed(title=f"{tgt} 변경", description="변경이 완료되었습니다.")
        embed_no = discord.Embed(title=f"{tgt} 변경", description="변경이 취소되었습니다.")
        embed_cancel = discord.Embed(title=f"{tgt} 변경", description="시간이 만료되었습니다.")
        if channel is None:
            embed_off = discord.Embed(title=f"{tgt} 변경", description="정말로 서버 로그 기능을 비활성화 할까요?")
            msg = await ctx.send(embed=embed_off)
            channel_id = None
        else:
            embed_change = discord.Embed(title=f"{tgt} 변경", description=f"정말로 서버 로그 채널을 {channel.mention}로 변경할까요?")
            msg = await ctx.send(embed=embed_change)
            channel_id = channel.id
        await admin.update_setup(self.jbot_db_global, self.bot, ctx, msg, [embed_ok, embed_no, embed_cancel], "log_channel", channel_id)

    @settings.command(name="공지채널")
    async def ann_channel_change(self, ctx, channel: discord.TextChannel = None):
        tgt = "제이봇 공지 채널"
        embed_ok = discord.Embed(title=f"{tgt} 변경", description="변경이 완료되었습니다.")
        embed_no = discord.Embed(title=f"{tgt} 변경", description="변경이 취소되었습니다.")
        embed_cancel = discord.Embed(title=f"{tgt} 변경", description="시간이 만료되었습니다.")
        if channel is None:
            embed_off = discord.Embed(title=f"{tgt} 변경", description="정말로 제이봇이 공지를 보내지 않게 설정할까요?")
            msg = await ctx.send(embed=embed_off)
            channel_id = None
        else:
            embed_change = discord.Embed(title=f"{tgt} 변경", description=f"정말로 제이봇 공지 채널을 {channel.mention}로 변경할까요?")
            msg = await ctx.send(embed=embed_change)
            channel_id = channel.id
        await admin.update_setup(self.jbot_db_global, self.bot, ctx, msg, [embed_ok, embed_no, embed_cancel],
                                 "announcement", channel_id)

    @settings.command(name="환영채널")
    async def welcome_channel_change(self, ctx, channel: discord.TextChannel = None):
        tgt = "유저 환영 채널"
        embed_ok = discord.Embed(title=f"{tgt} 변경", description="변경이 완료되었습니다.")
        embed_no = discord.Embed(title=f"{tgt} 변경", description="변경이 취소되었습니다.")
        embed_cancel = discord.Embed(title=f"{tgt} 변경", description="시간이 만료되었습니다.")
        if channel is None:
            embed_off = discord.Embed(title=f"{tgt} 변경", description="정말로 유저 환영 기능을 비활성화 할까요?")
            msg = await ctx.send(embed=embed_off)
            channel_id = None
        else:
            embed_change = discord.Embed(title=f"{tgt} 변경", description=f"정말로 유저 환영 채널을 {channel.mention}로 변경할까요?")
            msg = await ctx.send(embed=embed_change)
            channel_id = channel.id
        await admin.update_setup(self.jbot_db_global, self.bot, ctx, msg, [embed_ok, embed_no, embed_cancel],
                                 "welcome_channel", channel_id)

    @settings.command(name="환영인사")
    async def welcome_word_change(self, ctx, *, words=None):
        tgt = "유저 환영 인사"
        embed_ok = discord.Embed(title=f"{tgt} 변경", description="변경이 완료되었습니다.")
        embed_no = discord.Embed(title=f"{tgt} 변경", description="변경이 취소되었습니다.")
        embed_cancel = discord.Embed(title=f"{tgt} 변경", description="시간이 만료되었습니다.")
        if words is None:
            embed_off = discord.Embed(title=f"{tgt} 변경", description="정말로 유저 환영 인사를 제거할까요?")
            msg = await ctx.send(embed=embed_off)
            words = None
        else:
            embed_change = discord.Embed(title=f"{tgt} 변경", description=f"정말로 유저 환영 인사를 이걸로 변경할까요?\n```{words}```")
            msg = await ctx.send(embed=embed_change)
        await admin.update_setup(self.jbot_db_global, self.bot, ctx, msg, [embed_ok, embed_no, embed_cancel],
                                 "greet", words)

    @settings.command(name="작별인사")
    async def goodbye_word_change(self, ctx, *, words=None):
        tgt = "유저 작별 인사"
        embed_ok = discord.Embed(title=f"{tgt} 변경", description="변경이 완료되었습니다.")
        embed_no = discord.Embed(title=f"{tgt} 변경", description="변경이 취소되었습니다.")
        embed_cancel = discord.Embed(title=f"{tgt} 변경", description="시간이 만료되었습니다.")
        if words is None:
            embed_off = discord.Embed(title=f"{tgt} 변경", description="정말로 유저 작별 인사를 제거할까요?")
            msg = await ctx.send(embed=embed_off)
            words = None
        else:
            embed_change = discord.Embed(title=f"{tgt} 변경", description=f"정말로 유저 작별 인사를 이걸로 변경할까요?\n```{words}```")
            msg = await ctx.send(embed=embed_change)
        await admin.update_setup(self.jbot_db_global, self.bot, ctx, msg, [embed_ok, embed_no, embed_cancel],
                                 "bye", words)

    @settings.command(name="DM인사")
    async def welcome_dm_change(self, ctx, *, words=None):
        tgt = "유저 DM 환영 인사"
        embed_ok = discord.Embed(title=f"{tgt} 변경", description="변경이 완료되었습니다.")
        embed_no = discord.Embed(title=f"{tgt} 변경", description="변경이 취소되었습니다.")
        embed_cancel = discord.Embed(title=f"{tgt} 변경", description="시간이 만료되었습니다.")
        if words is None:
            embed_off = discord.Embed(title=f"{tgt} 변경", description="정말로 유저 DM 환영 인사를 제거할까요?")
            msg = await ctx.send(embed=embed_off)
            words = None
        else:
            embed_change = discord.Embed(title=f"{tgt} 변경", description=f"정말로 유저 DM 환영 인사를 이걸로 변경할까요?\n```{words}```")
            msg = await ctx.send(embed=embed_change)
        await admin.update_setup(self.jbot_db_global, self.bot, ctx, msg, [embed_ok, embed_no, embed_cancel],
                                 "greetpm", words)

    @settings.command(name="토글", aliases=["온오프", "변경"])
    async def toggle_feature(self, ctx, to_change, on_off):
        changeable = {"레벨": "use_level", "도배방지": "use_antispam", "글로벌DB": "use_globaldata"}
        tgt = "기타 기능"
        embed_ok = discord.Embed(title=f"{tgt} 변경", description="변경이 완료되었습니다.")
        embed_no = discord.Embed(title=f"{tgt} 변경", description="변경이 취소되었습니다.")
        embed_cancel = discord.Embed(title=f"{tgt} 변경", description="시간이 만료되었습니다.")
        if to_change not in changeable.keys():
            return await ctx.send(f"`{to_change}`는 변경할 수 없습니다.")
        if on_off == "활성화":
            value = 1
        elif on_off == "비활성화":
            value = 0
        else:
            return await ctx.send("잘못된 값이 감지되었습니다. (`활성화`, `비활성화` 중 하나를 사용해주세요.)")
        embed_change = discord.Embed(title=f"{tgt} 변경", description=f"정말로 이 기능을 {'활성화 할까요' if bool(value) else '비활성화 할까요'}?")
        msg = await ctx.send(embed=embed_change)
        await admin.update_setup(self.jbot_db_global, self.bot, ctx, msg, [embed_ok, embed_no, embed_cancel], changeable[to_change], value)


def setup(bot):
    bot.add_cog(GuildSetup(bot))
