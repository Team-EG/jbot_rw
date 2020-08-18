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
import asyncio
from discord.ext import commands
from modules import jbot_db

loop = asyncio.get_event_loop()


class Credit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_global = jbot_db.JBotDB("jbot_db_global")

    def cog_unload(self):
        loop.run_until_complete(self.jbot_db_global.close_db())

    @commands.command(name="크레딧", description="제이봇의 크레딧을 보여줍니다.")
    async def credit(self, ctx):
        embed = discord.Embed(title="제이봇 크레딧", description="잠시만 기다려주세요...",
                              color=discord.Colour.from_rgb(225, 225, 225))
        eun = self.bot.get_user(288302173912170497)
        gpm = self.bot.get_user(665450122926096395)
        rainy = self.bot.get_user(558323117802389514)
        msg = await ctx.send(embed=embed)
        user_voice = ctx.message.author.voice
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is None and bool(user_voice) is True:
            is_playing = False
        elif voice is None:
            is_playing = True
        else:
            is_playing = voice.is_playing()
        if user_voice is None or is_playing:
            embed = discord.Embed(title="제이봇 크레딧", description="개발: Team EG",
                                  color=discord.Colour.from_rgb(225, 225, 225))
            embed.add_field(name="메인 개발자", value=str(eun))
            embed.add_field(name="제작 참여", value=str(gpm) + "\n" + str(rainy))
            embed.add_field(name="Special thanks to...", value="Team EG members, KSP 한국 포럼 디스코드, and you!")
            await msg.edit(embed=embed)
            return
        channel = user_voice.channel
        await channel.connect()
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice.play(discord.FFmpegPCMAudio("https://jebserver.iptime.org/discord/jbot_credit.mp3"))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.3
        exist = await self.jbot_db_global.res_sql("SELECT credit FROM easteregg WHERE user_id=?", (ctx.author.id,))
        if bool(exist[0]["credit"]):
            return
        await self.jbot_db_global.exec_sql("UPDATE easteregg SET credit=? WHERE user_id=?", (1, ctx.author.id))
        await asyncio.sleep(1)
        embed = discord.Embed(title="제이봇 크레딧", description="개발: Team EG", color=discord.Colour.from_rgb(225, 225, 225))
        embed.add_field(name="메인 개발자", value=str(eun))
        await msg.edit(embed=embed)
        await asyncio.sleep(5)
        embed.add_field(name="제작 참여", value=str(gpm) + "\n" + str(rainy))
        await msg.edit(embed=embed)
        await asyncio.sleep(5)
        embed.add_field(name="사용한 오픈소스", value="Python, discord.py, youtube_dl, aiomysql, beautifulsoup4, ffmpeg")
        await msg.edit(embed=embed)
        await asyncio.sleep(5)
        embed.add_field(name="히든 크레딧의 원본", value="Hacknet Labyrinths DLC 엔딩 (음악: HOME - Dream Head)")
        await msg.edit(embed=embed)
        await asyncio.sleep(5)
        embed.add_field(name="Special thanks to...", value="Team EG members, KSP 한국 포럼 디스코드, and you!")
        await msg.edit(embed=embed)
        await msg.add_reaction("⏹")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "⏹"

        try:
            await self.bot.wait_for('reaction_add', timeout=180.0, check=check)
            voice.stop()
        except asyncio.TimeoutError:
            pass
        await voice.disconnect()


def setup(bot):
    bot.add_cog(Credit(bot))
