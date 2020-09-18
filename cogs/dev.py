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
import json
import psutil
import os
import datetime
import asyncio
from discord.ext import commands
from modules import custom_errors
from modules.cilent import CustomClient

loop = asyncio.get_event_loop()


class Dev(commands.Cog):
    def __init__(self, bot: CustomClient):
        with open("bot_settings.json", "r") as f:
            self.bot_settings = json.load(f)
        self.bot = bot
        self.jbot_db_global = bot.jbot_db_global

    async def cog_check(self, ctx):
        if ctx.author.id not in self.bot_settings["whitelist"]:
            raise custom_errors.NotWhitelisted
        return True

    @commands.command(name="공지")
    async def announcement(self, ctx, t, *, ann):
        if not ctx.author.id == 288302173912170497:
            return
        data = await self.jbot_db_global.res_sql("SELECT guild_id, announcement FROM guild_setup")
        embed = discord.Embed(title='제이봇 공지', colour=discord.Color.red(), timestamp=ctx.message.created_at)
        embed.set_footer(text=str(ctx.author.name), icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.add_field(name=str(t),
                        value=str(ann) + "\n\n도움이 필요하신가요?\n[Team EG 디스코드 서버로 바로 가기](https://discord.gg/gqJBhar)",
                        inline=False)
        for x in data:
            try:
                if x["announcement"] is not None:
                    v = x["announcement"]
                    target_channel = self.bot.get_guild(x["guild_id"]).get_channel(v)
                    await target_channel.send(embed=embed)
                """else:
                    tgt_guild = self.bot.get_guild(x["guild_id"])
                    tgt_guild_channels = tgt_guild.text_channels
                    tgt_guild_channels = [x for x in tgt_guild_channels if x.permissions_for(tgt_guild.get_member(self.bot.user.id)).send_messages]
                    if len(tgt_guild_channels) != 0:
                        embed.add_field(name="공지가 왜 이 채널에 왔나요?", value="공지 채널이 설정돼있지 않아서 랜덤 채널로 공지가 발송되었습니다.\n"
                                             "공지 채널 설정은 `제이봇 설정 공지채널 [설정할 채널]` 명령어로 가능합니다.", inline=False)
                        await (random.choice(tgt_guild_channels)).send(embed=embed)
                    else:
                        await ctx.send(f"공지 보내기 실패 - ID: {x['guild_id']} | 보낼 수 있는 채널이 없음.")"""
            except Exception as ex:
                await ctx.send(f"공지 보내기 실패 - ID: {x['guild_id']} | ex: ```py\n{ex}```")
        await ctx.send("공지를 모두 보냈습니다!")

    @commands.group(name="개발자", aliases=["dev"])
    async def dev(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="개발자 전용 명령어 리스트", description="대충 아무 명령어")
            embed.add_field(name="캐시리셋", value="캐시를 리셋합니다.")
            embed.add_field(name="상태설정", value="봇의 상태를 변경합니다.")
            await ctx.send(embed=embed)

    @dev.command(name="상태설정")
    async def set_status(self, ctx, status=None):
        await self.bot.change_presence(activity=discord.Game(str(status)))
        await ctx.send("완료")

    @dev.command(name="길드리스트")
    async def get_guild_list(self, ctx):
        guild_list = self.bot.guilds
        embed = discord.Embed(title="제이봇 길드 리스트", description=str(len(guild_list))+" 개")
        for x in guild_list:
            embed.add_field(name=x.name, value=f"소유자: {x.owner}\n유저수: {len(x.members)}")
        await ctx.send(embed=embed)

    @dev.command(name="서버상태")
    async def check_server(self, ctx):
        embed = discord.Embed(title="제이봇 서버 상태", description="~~서버컴 바꾸고 싶다~~")
        memory_usage_dict = dict(psutil.virtual_memory()._asdict())
        memory_usage_percent = memory_usage_dict['percent']
        uptime_sys = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        cpu_usage = psutil.cpu_percent(interval=None, percpu=True)
        p = psutil.Process(os.getpid())
        uptime_bot = datetime.datetime.now() - datetime.datetime.fromtimestamp(p.create_time())
        #temp = psutil.sensors_temperatures()
        embed.add_field(name="CPU 사용량", value=str(cpu_usage))
        embed.add_field(name="램 사용량", value=str(memory_usage_percent) + "%")
        embed.add_field(name="업타임", value=f"서버: {uptime_sys}\n봇: {uptime_bot}")
        #embed.add_field(name="온도", value=str(temp))
        await ctx.send(embed=embed)

    @dev.command(name="임시폴더리셋")
    async def temp_reset(self, ctx):
        temp_file_list = os.listdir("temp")
        for x in temp_file_list:
            os.remove("temp/"+x)
        await ctx.send("완료")

    @dev.command(name="eval", aliases=["이발"])
    async def eval(self, ctx, *, line: str):
        if line.startswith("await "):
            res = await eval(line.replace("await ", ""))
        else:
            res = eval(line)
        await ctx.send(res if res else "(결과 없음)")

    @dev.command(name="exec", aliases=["이색"])
    async def exec(self, ctx, *, line: str):
        res = exec(compile(line, "<string>", "exec"))
        await ctx.send(res if res else "(결과 없음)")

    @dev.command(name="주식추가")
    async def add_stock(self, ctx, name, base_price=1000):
        await self.jbot_db_global.exec_sql("""INSERT INTO stock(name, curr_price) VALUES (?,?)""", (name, base_price))
        await ctx.send("추가완료")

    @dev.command(name="임베드테스트")
    async def embed_test(self, ctx, url):
        embed = discord.Embed()
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @dev.command(name="주가조작")
    async def omg_stock_hax(self, ctx, tgt, amount: int):
        to_hax = (await self.jbot_db_global.res_sql("""SELECT * FROM stock WHERE name=?""", (tgt,)))[0]
        haxed = to_hax["curr_price"] + amount
        history = to_hax["history"].split(',')
        history.append(str(haxed))
        await self.jbot_db_global.exec_sql("""UPDATE stock SET curr_price=?, history=? WHERE name=?""", (haxed, ','.join(history), tgt))
        await ctx.send("완료")


def setup(bot: CustomClient):
    bot.add_cog(Dev(bot))
