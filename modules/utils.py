"""
    jbot_rw
    Copyright (C) 2020-2021 Team EG

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
from . import custom_errors
from .cilent import CustomClient
from discord.ext import commands


def parse_second(time: int):
    parsed_time = ""
    if time // (60 * 60) != 0:
        hour = time // (60 * 60)
        time -= hour * (60 * 60)
        parsed_time += f"{hour}시간 "
    if time // 60 != 0:
        minute = time // 60
        time -= minute * 60
        parsed_time += f"{minute}분 "
    parsed_time += f"{time}초"
    return parsed_time


async def start_page(bot, ctx, lists: list, time: int = 30, embed=False):
    counts = len(lists) - 1

    emoji_list = ["⬅", "⏹", "➡"]

    if embed is True:
        msg = await ctx.send(embed=lists[0])
    else:
        msg = await ctx.send(lists[0])
    counted = 0

    for x in emoji_list:
        await msg.add_reaction(x)

    try:
        while True:
            reaction = (await bot.wait_for("reaction_add", timeout=time, check=lambda r, u: r.message.id == msg.id and str(r.emoji) in emoji_list and u == ctx.author))[0]
            if str(reaction.emoji) == emoji_list[1]:
                try:
                    await msg.clear_reactions()
                except discord.Forbidden:
                    await msg.remove_reaction(emoji_list[0], msg.author)
                    await msg.remove_reaction(emoji_list[1], msg.author)
                    await msg.remove_reaction(emoji_list[2], msg.author)
                break
            elif str(reaction.emoji) == emoji_list[2]:
                try:
                    await msg.remove_reaction(emoji_list[2], ctx.author)
                except discord.Forbidden:
                    pass
                counted += 1
                if counted > counts:
                    counted = 0
                if embed is True:
                    await msg.edit(embed=lists[counted])
                else:
                    await msg.edit(content=lists[counted])
            elif str(reaction.emoji) == emoji_list[0]:
                try:
                    await msg.remove_reaction(emoji_list[0], ctx.author)
                except discord.Forbidden:
                    pass
                counted -= 1
                if counted < 0:
                    counted = counts
                if embed is True:
                    await msg.edit(embed=lists[counted])
                else:
                    await msg.edit(content=lists[counted])
    except asyncio.TimeoutError:
        await ctx.send("시간을 초과했습니다.", delete_after=5)
        try:
            await msg.clear_reactions()
        except discord.Forbidden:
            await msg.remove_reaction(emoji_list[0], msg.author)
            await msg.remove_reaction(emoji_list[1], msg.author)
            await msg.remove_reaction(emoji_list[2], msg.author)
        return


async def confirm(bot: CustomClient, ctx: commands.Context, msg: discord.Message, time: int = 30):
    emoji_list = ["⭕", "❌"]

    await msg.add_reaction("⭕")
    await msg.add_reaction("❌")

    try:
        reaction = (await bot.wait_for("reaction_add", timeout=time, check=lambda r, u: r.message.id == msg.id and str(r.emoji) in emoji_list and u == ctx.author))[0]
        if str(reaction.emoji) == emoji_list[0]:
            return True
        elif str(reaction.emoji) == emoji_list[1]:
            return False
    except asyncio.TimeoutError:
        return None


async def game_check(jbot_db_global, ctx):
    if ctx.invoked_with in ["계정생성", "계정생선"]:
        return True
    acc_list = await jbot_db_global.res_sql("""SELECT * FROM game WHERE user_id=?""", (ctx.author.id,))
    if not bool(acc_list):
        await ctx.send("계정이 존재하지 않습니다. 먼저 계정을 생성해주세요")
        raise custom_errors.IgnoreThis
    return True


async def safe_clear(msg: discord.Message, emojis: list):
    try:
        await msg.clear_reactions()
    except discord.Forbidden:
        [await msg.remove_reaction(x, msg.author) for x in emojis]


async def start_cursor(bot, ctx, lists: list, embed: discord.Embed, time: int = 30):
    up = "⬆"
    down = "⬇"
    load = "⏺"
    stop = "⏹"
    emoji_list = [up, down, load, stop]
    msg = await ctx.send("잠시만 기다려주세요...")
    for x in emoji_list:
        await msg.add_reaction(x)
    selected = lists[0]
    selected_num = 0

    def check(reaction, user):
        return user == ctx.author and str(reaction) in emoji_list and reaction.message.id == msg.id

    global reaction
    while True:
        tgt_embed = embed.copy()
        init_num = 1
        for k in lists:
            if k == selected:
                k = "▶" + k
            tgt_embed.add_field(name=f"{init_num}", value=k, inline=False)
            init_num += 1
        await msg.edit(content=None, embed=tgt_embed)
        try:
            reaction, user = await bot.wait_for("reaction_add", check=check, timeout=time)
        except asyncio.TimeoutError:
            await safe_clear(msg, emoji_list)
            return msg, None

        if str(reaction) == down:
            if selected_num + 1 == len(lists):
                selected_num = 0
                selected = lists[0]
            else:
                selected_num += 1
                selected = lists[selected_num]
        elif str(reaction) == up:
            if selected_num == 0:
                selected_num = len(lists)
                selected = lists[-1][0]
            else:
                selected_num -= 1
                selected = lists[selected_num]
        elif str(reaction) == stop:
            await safe_clear(msg, emoji_list)
            return msg, None
        elif str(reaction) == load:
            await safe_clear(msg, emoji_list)
            return msg, selected_num
