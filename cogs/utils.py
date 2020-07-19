import discord
import psutil
import datetime
import os
from discord.ext import commands
from modules import jbot_db


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.jbot_db_global = jbot_db.JBotDB("jbot_db_global")

    @commands.command(name="안녕", description="그냥 헬로 월드 출력하는거")
    async def hello(self, ctx):
        await ctx.send("Hello World!")

    @commands.command()
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

    @commands.command(name="정보")
    async def jbot_info(self, ctx):
        servers = len(self.bot.guilds)
        users = len(list(self.bot.get_all_members()))
        p = psutil.Process(os.getpid())
        uptime_bot = str(datetime.datetime.now() - datetime.datetime.fromtimestamp(p.create_time()))
        uptime_bot = uptime_bot.split(".")[0]
        embed = discord.Embed(title="제이봇 정보", description="Developed by [Team EG](https://discord.gg/gqJBhar)", colour=discord.Color.from_rgb(225, 225, 225))
        embed.add_field(name="들어와 있는 서버수", value=str(servers) + "개")
        embed.add_field(name="같이 있는 유저수", value=str(users) + "명")
        embed.add_field(name="업타임", value=uptime_bot)
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
