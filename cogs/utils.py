import discord
import psutil
import datetime
import os
import random
import platform
from discord.ext import commands
from modules import jbot_db, confirm, page


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_global = jbot_db.JBotDB("jbot_db_global")
        self.jbot_db_warns = jbot_db.JBotDB("jbot_db_warns")

    @commands.command(name="안녕", description="Hello, World!")
    async def hello(self, ctx):
        hello_world = ["Hello, World!",
                       "World, Hello!",
                       "hello world",
                       "```py\nprint('Hello, World!')```",
                       "```c\n#include <stdio.h>\n\nvoid main()\n{\n    printf('Hello, World!');\n}\n```",
                       "안녕, 세상!",
                       "hELLO< wORLD1"]
        await ctx.send(random.choice(hello_world))

    @commands.command(name="hellothisisverification", description="KOREANBOTS 인증용 명령어입니다.")
    async def hellothisisverification(self, ctx):
        await ctx.send("eunwoo1104#9600 (ID: 288302173912170497)")

    @commands.command(name="핑", description="봇의 핑을 알려줍니다.")
    async def ping(self, ctx):
        bot_latency = round(self.bot.latency * 1000)
        shard_latency_list = self.bot.latencies
        embed = discord.Embed(title=":ping_pong: 퐁!", description=f"봇 레이턴시: {bot_latency}ms", colour=discord.Color.from_rgb(225, 225, 225))
        for x in shard_latency_list:
            if len(shard_latency_list) == 0:
                break
            embed.add_field(name=f"샤드 {x[0]}", value=f"{int(x[1])}ms")
        await ctx.send(embed=embed)

    @commands.command(name="이모지정보", description="이모지 정보를 보여줍니다.")
    async def emoji_info(self, ctx, emoji: discord.Emoji = None):
        if emoji is None:
            return await ctx.send("이모지를 못 찾았습니다.")
        embed = discord.Embed(title="이모지 정보", description=str(emoji.name), color=discord.Colour.from_rgb(225, 225, 225))
        embed.set_thumbnail(url=str(emoji.url))
        embed.add_field(name="ID", value=str(emoji.id))
        embed.add_field(name="생성일", value=str(emoji.created_at.strftime("%Y-%m-%d %I:%M:%S %p")))
        await ctx.send(embed=embed)

    @commands.command(name="정보", description="봇의 정보를 보여줍니다.")
    async def jbot_info(self, ctx):
        servers = len(self.bot.guilds)
        users = len(list(self.bot.get_all_members()))
        p = psutil.Process(os.getpid())
        uptime_bot = str(datetime.datetime.now() - datetime.datetime.fromtimestamp(p.create_time()))
        uptime_bot = uptime_bot.split(".")[0]
        embed = discord.Embed(title="제이봇 정보", description="Developed by [eunwoo1104](https://discord.gg/nJuW3Xs) (Originally by Team EG)", colour=discord.Color.from_rgb(225, 225, 225))
        embed.add_field(name="파이썬 버전", value=platform.python_version(), inline=False)
        embed.add_field(name="discord.py 버전", value=discord.__version__, inline=False)
        embed.add_field(name="들어와 있는 서버수", value=str(servers) + "개", inline=False)
        embed.add_field(name="같이 있는 유저수", value=str(users) + "명", inline=False)
        embed.add_field(name="업타임", value=uptime_bot, inline=False)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)

    @commands.group(name="서버", description="서버 정보를 보여줍니다.", aliases=["서버정보"])
    async def guild_info(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title='서버 정보 명령어', colour=discord.Color.from_rgb(225, 225, 225))
            embed.add_field(name="서버 정보", value="서버의 정보를 보여줍니다.", inline=False)
            embed.add_field(name="서버 역할", value="서버의 역할 리스트를 보여줍니다.", inline=False)
            embed.add_field(name="서버 이모지", value="서버의 이모지 리스트를 보여줍니다.", inline=False)
            await ctx.send(embed=embed)

    @guild_info.command(name="정보")
    async def guild_info_info(self, ctx):
        guild = ctx.guild
        roles = guild.roles
        embed = discord.Embed(title='서버정보', colour=discord.Color.from_rgb(225, 225, 225))
        embed.set_author(name=f'{guild.name}', icon_url=guild.icon_url)
        embed.set_thumbnail(url=guild.icon_url)
        embed.add_field(name='소유자', value=f'{guild.owner.mention}')
        embed.add_field(name='유저수', value=f'{guild.member_count}명')
        embed.add_field(name='서버가 생성된 날짜', value=f'{guild.created_at.strftime("%Y-%m-%d %I:%M:%S %p")}')
        embed.add_field(name="채널수",
                        value=f"채팅 채널 {str(len(guild.text_channels))}개\n음성 채널 {str(len(ctx.guild.voice_channels))}개\n카테고리 {str(len(ctx.guild.categories))}개")
        embed.add_field(name="서버 부스트 레벨", value=str(guild.premium_tier) + '레벨')
        embed.add_field(name="서버 부스트 수", value=str(guild.premium_subscription_count) + '개')
        embed.add_field(name='역할수', value=str(len(guild.roles)) + '개')
        embed.add_field(name='서버 최고 역할', value=f'{roles[-1].mention}')
        embed.add_field(name='서버 위치', value=f'{guild.region}')
        await ctx.send(embed=embed)

    @guild_info.command(name="역할")
    async def guild_info_roles(self, ctx):
        guild = ctx.guild
        roles = guild.roles
        role_list = [x.mention for x in roles]
        embed = discord.Embed(title='서버 역할들', description=', '.join(role_list), colour=discord.Color.from_rgb(225, 225, 225))
        await ctx.send(embed=embed)

    @guild_info.command(name="이모지")
    async def guild_info_emoji(self, ctx):
        guild = ctx.guild
        emojis = guild.emojis
        emoji_list = [str(x) for x in emojis]
        embed = discord.Embed(title='서버 이모지', description=', '.join(emoji_list),
                              colour=discord.Color.from_rgb(225, 225, 225))
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        emoji = payload.emoji
        if str(emoji) not in ["📌", "⭐"]:
            return
        msg_data = await self.jbot_db_global.res_sql("SELECT * FROM starboard WHERE msg_id=?", (payload.message_id,))
        if not bool(msg_data):
            await self.jbot_db_global.exec_sql("INSERT INTO starboard(msg_id) VALUES (?)", (payload.message_id,))
            msg_data = await self.jbot_db_global.res_sql("SELECT * FROM starboard WHERE msg_id=?", (payload.message_id,))
            count = 1
        else:
            count = msg_data[0]["count"] + 1
        if bool(msg_data[0]["posted"]):
            return
        await self.jbot_db_global.exec_sql("UPDATE starboard SET count=? WHERE msg_id=?", (count, payload.message_id))
        if count == 3 or bool(str(emoji) == "⭐" and payload.member.id == payload.member.guild.owner.id):
            guild = self.bot.get_guild(payload.guild_id)
            await self.jbot_db_global.exec_sql("UPDATE starboard SET posted=? WHERE msg_id=?", (1, payload.message_id))
            guild_setup = await self.jbot_db_global.res_sql("SELECT * FROM guild_setup WHERE guild_id=?", (payload.guild_id,))
            starboard_channel = guild.get_channel(guild_setup[0]["starboard_channel"])
            if starboard_channel is None:
                return
            msg = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
            await msg.add_reaction("✅")
            embed = discord.Embed(title="메시지 박제", description=f"[메시지 바로가기]({msg.jump_url})")
            embed.set_author(name=msg.author.display_name + f" ({msg.author})", icon_url=msg.author.avatar_url)
            embed.add_field(name="메시지 내용", value=msg.content if msg.content else "(내용 없음)", inline=False)
            if bool(msg.attachments):
                to_show = [x.url for x in msg.attachments if (x.filename.split(".")[-1]).lower() in ['png', 'webp', 'jpg', 'jpeg', 'gif', 'bmp']]
                embed.add_field(name="사진", value=f"{len(to_show) if bool(to_show) else 0}개", inline=False)
                if len(to_show) != 0:
                    embed.set_image(url=to_show[0])
            await starboard_channel.send(embed=embed)

    @commands.command(name="건의", description="개발자에게 건의사항을 보냅니다.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def tix(self, ctx, *, ticket):
        msg = await ctx.send("정말로 건의사항을 보낼까요?\n장난으로 보내는 등 불필요하게 건의사항을 보내는 경우 건의사항 기능을 사용할 수 없게 될 수도 있습니다.")
        res = await confirm.confirm(self.bot, ctx, msg)
        if res is True:
            owner = self.bot.get_user(288302173912170497)
            await owner.send(f"`건의사항 ({ctx.author} / {ctx.author.id})`")
            await owner.send(ticket)
            return await ctx.send("성공적으로 건의사항을 보냈습니다!")
        await ctx.send("건의사항 보내기가 취소되었습니다.")

    @commands.command(name="경고리스트", description="자신이 보유한 경고들을 보여줍니다.", aliases=["경고보기"])
    async def warn_list(self, ctx, user: discord.Member = None):
        user = user if user is not None else ctx.author
        warn_list = await self.jbot_db_warns.res_sql(f"""SELECT * FROM "{ctx.guild.id}_warns" WHERE user_id=?""", (user.id,))
        if not bool(warn_list):
            return await ctx.send(f"{user.mention}님은 받은 경고가 없습니다.")
        base_embed = discord.Embed(title=f"{user.name}님의 경고리스트", description=f"총 {len(warn_list)}개", colour=discord.Color.red())
        embed_list = []
        tgt_embed = base_embed.copy()
        count = 0
        for x in warn_list:
            if count != 0 and count % 5 == 0:
                embed_list.append(tgt_embed)
                tgt_embed = base_embed.copy()
            issued_by = ctx.guild.get_member(x['issued_by'])
            issued_by = issued_by.mention if issued_by is not None else f"이미 이 서버에서 나간 유저입니다. (유저 ID: {x['issued_by']})"
            tgt_embed.add_field(name="경고번호: " + str(x["date"]), value=f"경고를 부여한 유저: {issued_by}\n사유: {x['reason']}", inline=False)
            count += 1
        embed_list.append(tgt_embed)
        await page.start_page(bot=self.bot, ctx=ctx, lists=embed_list, embed=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        emoji = payload.emoji
        if str(emoji) not in ["📌", "⭐"]:
            return
        msg_data = await self.jbot_db_global.res_sql("SELECT * FROM starboard WHERE msg_id=?", (payload.message_id,))
        if not bool(msg_data):
            return
        if bool(msg_data[0]["posted"]):
            return
        count = msg_data[0]["count"] - 1
        if count == 0:
            return await self.jbot_db_global.exec_sql("DELETE FROM starboard WHERE msg_id=?", (payload.message_id,))
        await self.jbot_db_global.exec_sql("UPDATE starboard SET count=? WHERE msg_id=?", (count, payload.message_id))


def setup(bot):
    bot.add_cog(Utils(bot))
