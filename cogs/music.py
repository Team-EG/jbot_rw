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
import lavalink
from discord.ext import commands
from modules import utils
from modules import custom_errors
from modules.cilent import CustomClient


class Music(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot

    def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()

    async def cog_check(self, ctx):
        return ctx.author.id in self.bot.get_bot_settings()["whitelist"]

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.lavalink.add_event_hook(self.no_queue_left)

    @staticmethod
    def check_url(url: str) -> str:
        if url.startswith("https://") or url.startswith("http://"):
            return url
        else:
            return f"ytsearch:{url}"

    async def voice_check(self, ctx: commands.Context, *, check_connected: bool = False, check_playing: bool = False, check_paused: bool = False) -> tuple:
        voice: discord.VoiceState = ctx.author.voice

        if check_playing and check_paused:
            raise custom_errors.IgnoreThis

        if not voice or not voice.channel:
            return 1, "먼저 음성 채널에 들어가주세요."

        lava = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if check_connected and lava is None:
            return 2, "먼저 음악을 재생해주세요."

        if check_playing and not lava.is_playing:
            return 3, "음악이 재생중이 아닙니다. 먼저 음악을 재생해주세요."

        if check_paused and lava.is_playing:
            return 4, "음악이 재생중입니다. 먼저 음악을 일시정지해주세요."

        return 0, None

    async def connect(self, guild: discord.Guild, voice: discord.VoiceState = None):
        ws = self.bot.shards[guild.shard_id]._parent.ws
        await ws.voice_state(str(guild.id), voice.channel.id if voice else None)

    async def no_queue_left(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild: discord.Guild = self.bot.get_guild(int(event.player.guild_id))
            await self.connect(guild)

    @commands.command(name="재생", description="음악을 재생합니다.", usage="`재생 [유튜브 URL 또는 제목]`", aliases=["play", "p", "ㅔ", "대기", "queue", "q", "ㅂ"])
    async def play(self, ctx: commands.Context, *, url: str):
        voice_state = await self.voice_check(ctx)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.create(ctx.guild.id, region="ko")
        await self.connect(ctx.guild, ctx.author.voice)
        url = self.check_url(url)
        resp = await lava.node.get_tracks(url)
        if resp is None or len(resp["tracks"]) == 0:
            return await ctx.send(f"{ctx.author.mention} 영상을 못 찾았어요. URL 또는 검색어를 제대로 입력했는지 확인해주세요.")
        if resp["loadType"] == "PLAYLIST_LOADED":
            conf = await ctx.send(f"{ctx.author.mention} 재생목록이 감지되었어요. 재생목록의 모든 영상을 추가할까요?")
            y_or_n = await utils.confirm(self.bot, ctx=ctx, msg=conf)
            if not y_or_n:
                return await conf.edit(content=f"{ctx.author.mention} 재생을 취소했어요.")
            [lava.add(requester=ctx.author.id, track=x) for x in resp["tracks"]]
        elif resp["loadType"] == "SEARCH_RESULT":
            track_list = []
            count = 0
            for x in resp['tracks']:
                if count >= 5:
                    break
                track_list.append(x)
                count += 1
            list_embed = discord.Embed(title="검색 결과 리스트", description=f"{len(track_list)}개", color=discord.Color.red())
            vid_list = [f"제목: {x['info']['title']}\n업로더: {x['info']['author']}\n[영상 바로가기]({x['info']['uri']})" for x in track_list]
            msg, selected = await utils.start_cursor(self.bot, ctx, vid_list, list_embed)
            await msg.delete()
            if selected is None:
                return await ctx.send(f"{ctx.author.mention} 재생을 취소했어요.")
            lava.add(requester=ctx.author.id, track=track_list[selected])
        else:
            lava.add(requester=ctx.author.id, track=resp['tracks'][0])
        if not lava.is_playing:
            await lava.play()

    @commands.command(name="스킵", description="재생중인 음악을 스킵합니다.", usage="`스킵 (스킵할 번호)`", aliases=["s", "skip", "ㄴ"])
    async def skip(self, ctx: commands.Context):
        voice_state = await self.voice_check(ctx, check_playing=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if lava is None:
            return await ctx.send(f"{ctx.author.mention} 먼저 재생해주세요.")
        await lava.skip()

    @commands.command(name="볼륨", description="음악의 볼륨을 조절합니다.", usage="`볼륨 [1~100]`", aliases=["volume", "vol", "v", "패ㅣㅕㅡㄷ", "ㅍ"])
    async def volume(self, ctx: commands.Context, vol: int = None):
        voice_state = await self.voice_check(ctx, check_connected=True, check_playing=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if vol is None:
            return await ctx.send(f"현재 볼륨은 {lava.volume}% 입니다.")
        if not 0 < vol <= 1000:
            return await ctx.send("볼륨 값은 1에서 1000 사이로만 가능합니다.")
        await lava.set_volume(vol)
        await ctx.send(f"볼륨을 {vol}%로 조정했어요.")


def setup(bot):
    bot.add_cog(Music(bot))
