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
import time
import random
from discord.ext import commands
from modules import utils
from modules import get_youtube
from modules import custom_errors
from modules.cilent import CustomClient

loop = asyncio.get_event_loop()


class Music(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.queues = {}

    async def queue_task(self, ctx: commands.Context, voice_client: discord.VoiceClient):
        # 왜인지는 모르겠는데 매우 불안정하네요.
        while voice_client.is_connected():
            if ctx.guild.id not in self.queues.keys():
                if voice_client.is_playing():
                    voice_client.stop()
                break
            try:
                is_loop = bool(self.queues[ctx.guild.id]["playing"]["loop"])
                is_shuffle = bool(self.queues[ctx.guild.id]["playing"]["random"])
            except KeyError:
                is_loop = False
                is_shuffle = False
            if not voice_client.is_playing() and not voice_client.is_paused() and (not is_loop and len(self.queues[ctx.guild.id]) <= 1):
                break
            if voice_client.is_playing() or voice_client.is_paused():
                await asyncio.sleep(1)
                continue
            print(self.queues)
            song_id_list = [x for x in self.queues[ctx.guild.id].keys() if x != "playing"]
            next_song_id = (sorted(song_id_list)[0] if not is_shuffle else random.choice(song_id_list)) if not is_loop else "playing"
            print(next_song_id)
            next_song = self.queues[ctx.guild.id][next_song_id].copy()
            embed = discord.Embed(title="유튜브 음악 재생 - 재생 시작",
                                  description=f"업로더: [`{next_song['vid_author']}`]({next_song['vid_channel_url']})\n"
                                              f"제목: [`{next_song['vid_title']}`]({next_song['vid_url']})",
                                  color=discord.Color.red(),
                                  timestamp=ctx.message.created_at)
            embed.set_footer(text=str(next_song['req_by']), icon_url=next_song['req_by'].avatar_url)
            embed.set_image(url=next_song['thumb'])
            voice_client.play(discord.FFmpegPCMAudio(next_song["tgt_url"], before_options=get_youtube.before_args))
            voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
            voice_client.source.volume = self.queues[ctx.guild.id]["playing"]["vol"]

            await ctx.send(embed=embed)

            if not is_loop:
                for k, v in next_song.items():
                    self.queues[ctx.guild.id]["playing"][k] = v
                del self.queues[ctx.guild.id][next_song_id]

            await asyncio.sleep(1)

        if ctx.guild.id in self.queues.keys():
            del self.queues[ctx.guild.id]
        if voice_client.is_connected():
            await voice_client.disconnect()
        await ctx.send(f"대기열이 비어있고 모든 노래를 재생했어요. `{voice_client.channel}`에서 나갈께요.")

    @staticmethod
    async def voice_check(ctx: commands.Context, *, check_connected: bool = False, check_playing: bool = False, check_paused: bool = False) -> tuple:
        voice_client: discord.VoiceClient = ctx.voice_client
        user_voice: discord.VoiceState = ctx.message.author.voice

        if check_playing and check_paused:
            raise custom_errors.IgnoreThis

        if not user_voice:
            return 1, "먼저 음성 채널에 들어가주세요."

        if check_connected and (voice_client is None or not voice_client.is_connected()):
            return 2, "먼저 음악을 재생해주세요."

        if check_playing and not voice_client.is_playing():
            return 3, "음악이 재생중이 아닙니다. 먼저 음악을 재생해주세요."

        if check_paused and voice_client.is_playing():
            return 4, "음악이 재생중입니다. 먼저 음악을 일시정지해주세요."

        return 0, None

    @staticmethod
    async def conn_voice(ctx: commands.Context) -> discord.VoiceClient:
        _voice_client: discord.VoiceClient = ctx.voice_client
        _user_voice: discord.VoiceState = ctx.message.author.voice
        _voice_channel = _user_voice.channel

        if not _voice_client:
            await _voice_channel.connect()
            _voice_client = ctx.voice_client

        return _voice_client

    @commands.command(name="재생", description="음악을 재생합니다.", usage="`재생 [유튜브 URL 또는 제목]`", aliases=["play", "p", "ㅔ", "대기", "queue", "q", "ㅂ"])
    async def play(self, ctx: commands.Context, *, url):
        voice_state = await self.voice_check(ctx)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        embed = discord.Embed(title="유튜브 음악 재생",
                              color=discord.Color.red(),
                              timestamp=ctx.message.created_at).set_footer(text=str(ctx.author),
                                                                           icon_url=ctx.author.avatar_url)
        embed.description = "잠시만 기다려주세요... (연결중)"
        msg = await ctx.send(embed=embed)

        try:
            voice_client: discord.VoiceClient = await asyncio.wait_for(self.conn_voice(ctx), timeout=10)
        except asyncio.TimeoutError:
            try:
                __voice_client: discord.VoiceClient = ctx.voice_client
                await __voice_client.disconnect(force=True)
            except:  # 일단 강제 연결 해제를 시도하고 안되면 그냥 넘어갑니다. (혹시라도 들어가있는 경우 나가기 위함)
                pass
            return await ctx.send("음성 연결에 실패했습니다. 명령어를 다시 실행해주세요.")

        if ctx.guild.id not in self.queues.keys():
            self.queues[ctx.guild.id] = {}
        res = await get_youtube.get_youtube(url)

        embed.title += " - 재생 시작" if not voice_client.is_playing() else " - 재생 대기열에 추가됨"
        embed.description = f"업로더: [`{res.vid_author}`]({res.vid_channel_url})\n제목: [`{res.vid_title}`]({res.vid_url})"
        embed.set_image(url=res.thumb)
        to_add = {
            "vid_url": res.vid_url,
            "vid_title": res.vid_title,
            "vid_author": res.vid_author,
            "vid_channel_url": res.vid_channel_url,
            "thumb": res.thumb,
            "tgt_url": res.tgt_url,
            "req_by": ctx.author
        }

        to_add_name = "playing" if not voice_client.is_playing() else round(time.time())

        if not voice_client.is_playing():
            vol = 0.3
            to_add["vol"] = vol
            to_add["loop"] = 0
            to_add["random"] = 0
            voice_client.play(discord.FFmpegPCMAudio(res.tgt_url, before_options=get_youtube.before_args))
            voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
            voice_client.source.volume = vol
            asyncio.create_task(self.queue_task(ctx, voice_client))

        await msg.edit(embed=embed)
        self.queues[ctx.guild.id][to_add_name] = to_add

    @commands.command(name="스킵", description="재생중인 음악을 스킵합니다.", aliases=["s", "skip", "ㄴ"])
    async def skip(self, ctx: commands.Context):
        voice_state = await self.voice_check(ctx, check_connected=True, check_playing=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        voice_client: discord.VoiceClient = ctx.voice_client
        voice_client.stop()

    @commands.command(name="정지", description="음악 재생을 멈춥니다.", aliases=["stop", "ㄴ새ㅔ"])
    async def stop(self, ctx: commands.Context):
        voice_state = await self.voice_check(ctx, check_connected=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        del self.queues[ctx.guild.id]

    @commands.command(name="일시정지", description="음악을 일시정지합니다.", aliases=["pause", "ps", "ㅔㄴ"])
    async def pause(self, ctx: commands.Context):
        voice_state = await self.voice_check(ctx, check_connected=True, check_playing=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        voice_client: discord.VoiceClient = ctx.voice_client
        voice_client.pause()
        await ctx.send("플레이어를 일시정지했어요.")

    @commands.command(name="계속재생", description="음악 일시정지를 해제합니다.", aliases=["resume", "r", "ㄱ"])
    async def resume(self, ctx: commands.Context):
        voice_state = await self.voice_check(ctx, check_connected=True, check_paused=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        voice_client: discord.VoiceClient = ctx.voice_client
        voice_client.resume()
        await ctx.send("일시정지를 해제했어요.")

    @commands.command(name="볼륨", description="음악의 볼륨을 조절합니다.", usage="`볼륨 [1~100]`", aliases=["volume", "vol", "v", "패ㅣㅕㅡㄷ", "ㅍ"])
    async def volume(self, ctx: commands.Context, vol: int = None):
        voice_state = await self.voice_check(ctx, check_connected=True, check_paused=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        current_voice = self.queues[ctx.guild.id]["playing"]["vol"]
        if vol is None:
            return await ctx.send(f"현재 볼륨은 {current_voice * 100}% 입니다.")
        if not 0 < vol <= 100:
            return await ctx.send("볼륨 값은 0에서 100 사이로만 가능합니다.")
        voice_client: discord.VoiceClient = ctx.voice_client
        voice_client.source.volume = vol / 100
        await ctx.send(f"볼륨을 {vol}%로 조정했어요.")

    @commands.command(name='루프', description="재생중인 음악을 무한 반복하거나 무한 반복을 해제합니다.", aliases=["무한반복", "loop", "repeat"])
    async def music_loop(self, ctx):
        voice_state = await self.voice_check(ctx, check_connected=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        queue = self.queues[ctx.guild.id]
        if not bool(queue["playing"]["loop"]):
            msg = await ctx.send(f"{ctx.author.mention} 정말로 이 음악을 무한반복할까요?")
            res = await utils.confirm(self.bot, ctx, msg)
            if not res:
                return await msg.edit(content=f"{ctx.author.mention} 무한반복이 취소되었습니다.")
            queue["playing"]["loop"] = 1
            return await msg.edit(content=f"{ctx.author.mention} 이 음악을 무한반복할께요!")
        elif bool(queue["playing"]["loop"]):
            msg = await ctx.send(f"{ctx.author.mention} 정말로 무한반복을 해제할까요?")
            res = await utils.confirm(self.bot, ctx, msg)
            if not res:
                return await msg.edit(content=f"{ctx.author.mention} 무한반복 해제가 취소되었습니다.")
            queue["playing"]["loop"] = 0
            return await msg.edit(content=f"{ctx.author.mention} 무한반복이 해제되었습니다.")

    @commands.command(name="셔플", description="대기 리스트에서 음악을 무작위로 재생합니다.", aliases=["랜덤", "random", "shuffle", "sf", "ㄶ", "ㄴㅎ"])
    async def shuffle(self, ctx):
        voice_state = await self.voice_check(ctx, check_connected=True)
        if voice_state[0] != 0:
            return await ctx.send(voice_state[1])
        queue = self.queues[ctx.guild.id]
        if not bool(queue["playing"]["random"]):
            msg = await ctx.send(f"{ctx.author.mention} 정말로 랜덤 재생 기능을 켤까요?")
            res = await utils.confirm(self.bot, ctx, msg)
            if not res:
                return await msg.edit(content=f"{ctx.author.mention} 랜덤 재생이 취소되었습니다.")
            queue["playing"]["random"] = 1
            return await msg.edit(content=f"{ctx.author.mention} 랜덤 재생이 켜졌어요!")
        elif bool(queue["playing"]["random"]):
            msg = await ctx.send(f"{ctx.author.mention} 정말로 랜덤 재생을 해제할까요?")
            res = await utils.confirm(self.bot, ctx, msg)
            if not res:
                return await msg.edit(content=f"{ctx.author.mention} 랜덤 재생 해제가 취소되었습니다.")
            queue["playing"]["random"] = 0
            return await msg.edit(content=f"{ctx.author.mention} 랜덤 재생이 해제되었습니다.")

    @commands.command(name="대기열", description="현재 음악 대기열을 보여줍니다.", aliases=["재생리스트", "pl", "ql", "queuelist", "playlist", "비", "ㅔㅣ"])
    async def queue_list(self, ctx: commands.Context):
        if ctx.guild.id not in self.queues.keys():
            return await ctx.send("현재 재생중이 아닙니다.")

        queue_list = self.queues[ctx.guild.id]
        temp_ql_embed = discord.Embed(title="뮤직 대기 리스트", color=discord.Colour.from_rgb(225, 225, 225),
                                      timestamp=ctx.message.created_at)
        temp_ql_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        playing_vid_url = queue_list["playing"]["vid_url"]
        playing_vid_title = queue_list["playing"]["vid_title"]
        playing_vid_author = queue_list["playing"]["vid_author"]
        playing_vid_channel_url = queue_list["playing"]["vid_channel_url"]
        playing_thumb = queue_list["playing"]["thumb"]
        vol = queue_list["playing"]["vol"]
        one_embed = discord.Embed(title="현재 재생중", colour=discord.Color.green())
        one_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        one_embed.set_image(url=playing_thumb)
        req_by = queue_list["playing"]["req_by"]
        one_embed.add_field(name="정보",
                            value=f"업로더: [`{playing_vid_author}`]({playing_vid_channel_url})\n제목: [`{playing_vid_title}`]({playing_vid_url})",
                            inline=False)
        one_embed.add_field(name="요청자", value=f"{req_by.mention} (`{req_by}`)", inline=False)
        one_embed.add_field(name="현재 볼륨", value=f"{float(vol) * 100}%", inline=False)
        one_embed.add_field(name="대기중인 음악 개수", value=f"{len([x for x in queue_list.keys() if not x == 'playing'])}개")
        if ctx.voice_client.is_paused():
            one_embed.add_field(name="플레이어 상태", value="현재 일시정지 상태입니다.", inline=False)
        elif queue_list["playing"]["loop"]:
            one_embed.add_field(name="플레이어 상태", value="반복 재생 기능이 켜져있습니다.", inline=False)
        elif queue_list["playing"]["random"]:
            one_embed.add_field(name="플레이어 상태", value="랜덤 재생 기능이 켜져있습니다.", inline=False)
        if len(queue_list.keys()) == 1:
            return await ctx.send(embed=one_embed)
        ql_num = 1
        embed_list = [one_embed]
        ql_embed = None
        for x in queue_list.keys():
            if x == "playing":
                ql_embed = temp_ql_embed.copy()
                continue
            if ql_num != 1 and (ql_num - 1) % 5 == 0:
                embed_list.append(ql_embed)
                ql_embed = temp_ql_embed.copy()
            queue_vid_url = queue_list[x]["vid_url"]
            queue_vid_title = queue_list[x]["vid_title"]
            queue_req_by = queue_list[x]["req_by"]
            ql_embed.add_field(name="대기리스트" + str(ql_num),
                               value=f"제목: [`{queue_vid_title}`]({queue_vid_url})\n"
                                     f"요청자: {queue_req_by.mention} (`{queue_req_by}`)",
                               inline=False)
            ql_num += 1
        next_song = queue_list[list(queue_list.keys())[1]]
        next_embed = discord.Embed(title="다음곡", color=discord.Colour.red())
        next_vid_url = next_song["vid_url"]
        next_vid_title = next_song["vid_title"]
        next_vid_author = next_song["vid_author"]
        next_vid_channel_url = next_song["vid_channel_url"]
        next_thumb = next_song["thumb"]
        next_req_by = next_song["req_by"]
        next_embed.add_field(name="정보",
                             value=f"업로더: [`{next_vid_author}`]({next_vid_channel_url})\n"
                                   f"제목: [`{next_vid_title}`]({next_vid_url})",
                             inline=False)
        next_embed.add_field(name="요청자", value=f"{next_req_by.mention} (`{next_req_by}`)", inline=False)
        next_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        next_embed.set_image(url=next_thumb)
        embed_list.append(ql_embed)
        embed_list.append(next_embed)
        await utils.start_page(self.bot, ctx, embed_list, embed=True)

    @commands.group(name="재생목록", description="자신의 재생목록을 보여줍니다.")
    async def playlist(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            playlist_list = await self.bot.jbot_db_global.res_sql("SELECT * FROM playlist WHERE user_id=?", (ctx.author.id,))
            embed = discord.Embed(title="재생목록",
                                  description=f"음악 {len(playlist_list)}개\n"
                                              f"음악 추가는 `{ctx.prefix}재생목록 추가` 명령어로, 음악 제거는 `{ctx.prefix}재생목록 제거` 명령어를 이용해주세요.\n"
                                              f"재생목록에 저장된 모든 노래를 재생하고 싶으시면 `{ctx.prefix}재생목록 재생` 명령어를 사용해주세요.",
                                  color=discord.Colour.from_rgb(225, 225, 225))
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            if len(playlist_list) == 0:
                return await ctx.send(f"재생목록에 음악이 하나도 없네요...\n"
                                      f"음악 추가는 `{ctx.prefix}재생목록 추가` 명령어로, 음악 제거는 `{ctx.prefix}재생목록 제거` 명령어를 이용해주세요.")
            embed_list = []
            tgt_embed = embed.copy()
            count = 0
            for x in playlist_list:
                if count != 0 and count % 5 == 0:
                    embed_list.append(tgt_embed)
                    tgt_embed = embed.copy()
                tgt_embed.add_field(name=x["title"], value=x["youtube_link"], inline=False)
                count += 1
            embed_list.append(tgt_embed)
            if len(embed_list) == 1:
                return await ctx.send(embed=embed_list[0])
            await utils.start_page(self.bot, ctx, embed_list, embed=True)

    @playlist.command(name="추가")
    async def add_playlist(self, ctx: commands.Context, *, url):
        embed = discord.Embed(title="재생목록 추가", description="정말로 이 음악을 재생목록에 추가할까요?")
        search_res = await get_youtube.get_youtube(url)
        vid_url = search_res.vid_url
        vid_title = search_res.vid_title
        thumb = search_res.thumb
        embed.add_field(name="제목", value=vid_title, inline=False)
        embed.add_field(name="링크", value=vid_url, inline=False)
        embed.set_image(url=thumb)
        msg = await ctx.send(embed=embed)
        res = await utils.confirm(self.bot, ctx, msg)
        if not res:
            reject = discord.Embed(title="재생목록 추가", description="재생목록 추가가 취소되었습니다.")
            return await msg.edit(embed=reject)
        await self.bot.jbot_db_global.exec_sql("INSERT INTO playlist(user_id, youtube_link, title) VALUES (?, ?, ?)", (ctx.author.id, vid_url, vid_title))
        succeed = discord.Embed(title="재생목록 추가", description="이 음악을 재생목록에 추가했습니다.")
        await msg.edit(embed=succeed)

    @playlist.command(name="제거")
    async def remove_playlist(self, ctx: commands.Context, *, title):
        global vid_url, vid_title, info
        embed = discord.Embed(title="재생목록 제거", description="정말로 이 음악을 재생목록에 제거할까요?")
        try:
            if title.startswith("https://") or title.startswith("youtube.com"):
                info = await self.bot.jbot_db_global.res_sql("SELECT * FROM playlist WHERE user_id=? AND youtube_link=?", (ctx.author.id, title))
                vid_url = info[0]["youtube_link"]
                vid_title = info[0]["title"]
            else:
                info = await self.bot.jbot_db_global.res_sql("SELECT * FROM playlist WHERE user_id=? AND title=?", (ctx.author.id, title))
                vid_url = info[0]["youtube_link"]
                vid_title = info[0]["title"]
        except IndexError:
            return await ctx.send("해당 음악을 찾지 못했습니다.")
        embed.add_field(name="제목", value=vid_title, inline=False)
        embed.add_field(name="링크", value=vid_url, inline=False)
        msg = await ctx.send(embed=embed)
        res = await utils.confirm(self.bot, ctx, msg)
        if not res:
            reject = discord.Embed(title="재생목록 제거", description="재생목록 제거가 취소되었습니다.")
            return await msg.edit(embed=reject)
        succeed = discord.Embed(title="재생목록 제거", description="이 음악을 재생목록에 제거했습니다.")
        await self.bot.jbot_db_global.exec_sql("DELETE FROM playlist WHERE user_id=? AND youtube_link=?", (ctx.author.id, vid_url))
        await msg.edit(embed=succeed)

    @playlist.command(name="재생")
    async def play_playlist(self, ctx: commands.Context):
        playlist_list = await self.bot.jbot_db_global.res_sql("SELECT * FROM playlist WHERE user_id=?", (ctx.author.id,))
        if len(playlist_list) == 0:
            return await ctx.send(f"재생목록이 비어있습니다. 먼저 `{ctx.prefix}재생목록 추가` 명령어로 재생목록에 음악을 추가해주세요.")
        voice_state = await self.voice_check(ctx, check_connected=True)
        init_embed = discord.Embed(title="재생목록 재생",
                                   description="정말로 재생 대기열에 재생목록에 있는 음악을 모두 추가할까요?",
                                   color=discord.Colour.from_rgb(225, 225, 225))
        msg = await ctx.send(embed=init_embed)
        res = await utils.confirm(self.bot, ctx=ctx, msg=msg)
        if not res:
            cancel_embed = discord.Embed(title="재생목록 재생",
                                         description="재생목록 재생을 취소했습니다.",
                                         color=discord.Color.red())
            return await msg.edit(embed=cancel_embed)
        pass_embed = discord.Embed(title="재생목록 재생",
                                   description="잠시만 기다려주세요...",
                                   color=discord.Color.green())
        await msg.edit(embed=pass_embed)
        if voice_state[0] == 1:
            return await ctx.send("먼저 명령어 실행 전에 음성 채널에 연결해주세요.")
        if voice_state[0] == 2:
            try:
                await asyncio.wait_for(self.conn_voice(ctx), timeout=10)
            except asyncio.TimeoutError:
                try:
                    __voice_client: discord.VoiceClient = ctx.voice_client
                    await __voice_client.disconnect(force=True)
                except:  # 일단 강제 연결 해제를 시도하고 안되면 그냥 넘어갑니다. (혹시라도 들어가있는 경우 나가기 위함)
                    pass
                return await ctx.send("음성 연결에 실패했습니다. 명령어를 다시 실행해주세요.")
            self.queues[ctx.guild.id] = {}
        vol = 0.3
        for x in playlist_list:
            ytdl_res = await get_youtube.get_youtube(x["youtube_link"])
            key_to_use = time.time() if "playing" in self.queues[ctx.guild.id] else "playing"
            to_add = {
                "vid_url": ytdl_res.vid_url,
                "vid_title": ytdl_res.vid_title,
                "vid_author": ytdl_res.vid_author,
                "vid_channel_url": ytdl_res.vid_channel_url,
                "thumb": ytdl_res.thumb,
                "tgt_url": ytdl_res.tgt_url,
                "req_by": ctx.author
            }
            if key_to_use == "playing":
                to_add["vol"] = vol
                to_add["loop"] = 0
                to_add["random"] = 0
            self.queues[ctx.guild.id][key_to_use] = to_add
        finished_embed = discord.Embed(title="재생목록 재생",
                                       description=f"`{'`, `'.join([x['title'] for x in playlist_list])}`을(를) 대기열에 추가했어요!",
                                       color=discord.Color.green())
        await msg.edit(embed=finished_embed)
        if voice_state[0] == 2:
            to_play = self.queues[ctx.guild.id]["playing"]
            voice_client: discord.VoiceClient = ctx.voice_client
            voice_client.play(discord.FFmpegPCMAudio(to_play["tgt_url"], before_options=get_youtube.before_args))
            voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
            voice_client.source.volume = vol
            run_embed = discord.Embed(title="유튜브 음악 재생 - 재생 시작",
                                      description=f"업로더: [`{to_play['vid_author']}`]({to_play['vid_channel_url']})\n"
                                                  f"제목: [`{to_play['vid_title']}`]({to_play['vid_url']})",
                                      color=discord.Color.red(),
                                      timestamp=ctx.message.created_at)
            run_embed.set_footer(text=str(to_play['req_by']), icon_url=to_play['req_by'].avatar_url)
            run_embed.set_image(url=to_play['thumb'])
            await ctx.send(embed=run_embed)
            asyncio.create_task(self.queue_task(ctx, voice_client))


def setup(bot):
    bot.add_cog(Music(bot))
