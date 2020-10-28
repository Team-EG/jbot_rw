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
        self.bot.loop.create_task(self.on_bot_ready())

    def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()

    async def cog_check(self, ctx):
        return ctx.author.id in self.bot.get_bot_settings()["whitelist"]

    async def on_bot_ready(self):
        await self.bot.wait_until_ready()
        self.bot.lavalink.add_event_hook(self.main_event)

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

        if check_playing and lava.paused:
            return 3, "음악이 재생중이 아닙니다. 먼저 음악을 재생해주세요."

        if check_paused and not lava.paused:
            return 4, "음악이 재생중입니다. 먼저 음악을 일시정지해주세요."

        return 0, None

    async def connect(self, guild: discord.Guild, voice: discord.VoiceState = None):
        ws = self.bot.shards[guild.shard_id]._parent.ws
        await ws.voice_state(str(guild.id), voice.channel.id if voice else None)

    async def main_event(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild: discord.Guild = self.bot.get_guild(int(event.player.guild_id))
            channel: discord.TextChannel = event.player.fetch("channel")
            await channel.send(f"대기열이 비어있고 모든 노래를 재생했어요. 음성 채널에서 나갈께요.")
            await self.connect(guild)
            await self.bot.lavalink.player_manager.destroy(guild.id)

    @commands.command(name="재생", description="음악을 재생합니다.", usage="`재생 [유튜브 URL 또는 제목]`", aliases=["play", "p", "ㅔ", "대기", "queue", "q", "ㅂ"])
    async def play(self, ctx: commands.Context, *, url: str):
        voice_state = await self.voice_check(ctx)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        embed = discord.Embed(title="유튜브 음악 재생",
                              color=discord.Color.red(),
                              timestamp=ctx.message.created_at).set_footer(text=str(ctx.author),
                                                                           icon_url=ctx.author.avatar_url)
        embed.description = "잠시만 기다려주세요... (연결중)"
        msg = await ctx.send(embed=embed)
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.create(ctx.guild.id, region="ko")
        await self.connect(ctx.guild, ctx.author.voice)
        url = self.check_url(url)
        resp = await lava.node.get_tracks(url)
        await msg.delete()
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
        embed.title += " - 재생 시작" if not lava.is_playing else " - 재생 대기열에 추가됨"
        if not lava.is_playing:
            lava.store("channel", ctx.channel)
            await lava.play()
        current: lavalink.AudioTrack = lava.current
        playing_vid_url = current.uri
        playing_vid_title = current.title
        playing_vid_author = current.author
        playing_thumb = f"https://img.youtube.com/vi/{current.identifier}/hqdefault.jpg"
        embed.description = f"업로더: `{playing_vid_author}`\n제목: [`{playing_vid_title}`]({playing_vid_url})"
        embed.set_image(url=playing_thumb)
        await ctx.send(embed=embed)

    @commands.command(name="스킵", description="재생중인 음악을 스킵합니다.", usage="`스킵 (스킵할 번호)`", aliases=["s", "skip", "ㄴ"])
    async def skip(self, ctx: commands.Context):
        voice_state = await self.voice_check(ctx, check_connected=True, check_playing=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await lava.skip()

    @commands.command(name="일시정지", description="음악을 일시정지합니다.", aliases=["pause", "ps", "ㅔㄴ"])
    async def pause(self, ctx: commands.Context):
        voice_state = await self.voice_check(ctx, check_connected=True, check_playing=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await lava.set_pause(True)
        await ctx.send(f"{ctx.author.mention} 플레이어를 일시정지했어요.")

    @commands.command(name="계속재생", description="음악 일시정지를 해제합니다.", aliases=["resume", "r", "ㄱ"])
    async def resume(self, ctx: commands.Context):
        voice_state = await self.voice_check(ctx, check_connected=True, check_paused=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        await lava.set_pause(False)
        await ctx.send(f"{ctx.author.mention} 일시정지를 해제했어요.")

    @commands.command(name="볼륨", description="음악의 볼륨을 조절합니다.", usage="`볼륨 [1~100]`", aliases=["volume", "vol", "v", "패ㅣㅕㅡㄷ", "ㅍ"])
    async def volume(self, ctx: commands.Context, vol: int = None):
        voice_state = await self.voice_check(ctx, check_connected=True, check_playing=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if vol is None:
            return await ctx.send(f"{ctx.author.mention} 현재 볼륨은 {lava.volume}% 에요.")
        if not 0 < vol <= 1000:
            return await ctx.send(f"{ctx.author.mention} 볼륨 값은 1에서 1000 사이로만 가능해요.")
        await lava.set_volume(vol)
        await ctx.send(f"{ctx.author.mention} 볼륨을 {vol}%로 조정했어요.")

    @commands.command(name="셔플", description="대기 리스트에서 음악을 무작위로 재생합니다.", aliases=["랜덤", "random", "shuffle", "sf", "ㄶ", "ㄴㅎ"])
    async def shuffle(self, ctx: commands.Context):
        voice_state = await self.voice_check(ctx, check_connected=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        lava.set_shuffle(False if lava.shuffle else True)
        await ctx.send(f"{ctx.author.mention} 랜덤 재생 기능이 {'켜졌어요!' if lava.shuffle else '꺼졌어요.'}")

    @commands.command(name='루프', description="재생중인 음악을 무한 반복하거나 무한 반복을 해제합니다.", aliases=["무한반복", "loop", "repeat"])
    async def music_loop(self, ctx: commands.Context):
        voice_state = await self.voice_check(ctx, check_connected=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        lava.set_repeat(False if lava.repeat else True)
        await ctx.send(f"{ctx.author.mention} 반복 재생 기능이 {'켜졌어요!' if lava.repeat else '꺼졌어요.'}")

    @commands.command(name="대기열", description="현재 음악 대기열을 보여줍니다.", aliases=["재생리스트", "pl", "ql", "queuelist", "playlist", "비", "ㅔㅣ"])
    async def queue_list(self, ctx: commands.Context):
        lava: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if lava is None:
            return await ctx.send("현재 재생중이 아닙니다.")
        temp_ql_embed = discord.Embed(title="뮤직 대기 리스트", color=discord.Colour.from_rgb(225, 225, 225),
                                      timestamp=ctx.message.created_at)
        temp_ql_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        current: lavalink.AudioTrack = lava.current
        playing_vid_url = current.uri
        playing_vid_title = current.title
        playing_vid_author = current.author
        playing_thumb = f"https://img.youtube.com/vi/{current.identifier}/hqdefault.jpg"
        one_embed = discord.Embed(title="현재 재생중", colour=discord.Color.green())
        one_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        one_embed.set_image(url=playing_thumb)
        req_by = ctx.guild.get_member(current.requester)
        one_embed.add_field(name="정보",
                            value=f"업로더: `{playing_vid_author}`\n제목: [`{playing_vid_title}`]({playing_vid_url})",
                            inline=False)
        one_embed.add_field(name="요청자", value=f"{req_by.mention} (`{req_by}`)", inline=False)
        one_embed.add_field(name="현재 볼륨", value=f"{lava.volume}%", inline=False)
        one_embed.add_field(name="대기중인 음악 개수", value=f"{len([x for x in lava.queue])}개")
        if lava.paused:
            one_embed.add_field(name="플레이어 상태", value="현재 일시정지 상태입니다.", inline=False)
        elif lava.repeat:
            one_embed.add_field(name="플레이어 상태", value="반복 재생 기능이 켜져있습니다.", inline=False)
        elif lava.shuffle:
            one_embed.add_field(name="플레이어 상태", value="랜덤 재생 기능이 켜져있습니다.", inline=False)
        if len(lava.queue) == 0:
            return await ctx.send(embed=one_embed)
        ql_num = 1
        embed_list = [one_embed]
        ql_embed = temp_ql_embed.copy()
        for x in lava.queue:
            if ql_num != 1 and (ql_num - 1) % 5 == 0:
                embed_list.append(ql_embed)
                ql_embed = temp_ql_embed.copy()
            queue_vid_url = x.uri
            queue_vid_title = x.title
            queue_req_by = ctx.guild.get_member(x.requester)
            ql_embed.add_field(name="대기리스트" + str(ql_num),
                               value=f"제목: [`{queue_vid_title}`]({queue_vid_url})\n"
                                     f"요청자: {queue_req_by.mention} (`{queue_req_by}`)",
                               inline=False)
            ql_num += 1
        next_song = lava.queue[0]
        next_embed = discord.Embed(title="다음곡", color=discord.Colour.red())
        next_vid_url = next_song.uri
        next_vid_title = next_song.title
        next_vid_author = next_song.author
        next_thumb = f"https://img.youtube.com/vi/{next_song.identifier}/hqdefault.jpg"
        next_req_by = ctx.guild.get_member(next_song.requester)
        next_embed.add_field(name="정보",
                             value=f"업로더: `{next_vid_author}`\n"
                                   f"제목: [`{next_vid_title}`]({next_vid_url})",
                             inline=False)
        next_embed.add_field(name="요청자", value=f"{next_req_by.mention} (`{next_req_by}`)", inline=False)
        next_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        next_embed.set_image(url=next_thumb)
        embed_list.append(ql_embed)
        embed_list.append(next_embed)
        await utils.start_page(self.bot, ctx, embed_list, embed=True)


def setup(bot):
    bot.add_cog(Music(bot))
