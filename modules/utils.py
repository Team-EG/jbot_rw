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
