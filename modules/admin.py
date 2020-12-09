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
import datetime
import time
import json
from . import jbot_db, utils, custom_errors
from .cilent import CustomClient
from discord.ext import commands


async def warn(jbot_db_global: jbot_db.JBotDB, jbot_db_warns: jbot_db.JBotDB, member: discord.Member, issued_by: discord.Member, reason=None, ctx: commands.Context = None,
               message: discord.Message = None):
    current_time = time.strftime('%Y%m%d%H%M%S')
    global ctx_or_message
    if message is None and ctx is None:
        raise commands.MissingRequiredArgument
    if message is None:
        ctx_or_message = ctx
    if ctx is None:
        ctx_or_message = message
    if reason is None:
        reason = "없음"
    guild = ctx_or_message.guild
    embed = discord.Embed(title="맴버 경고", description="경고 번호: "+str(current_time), color=discord.Colour.red())
    embed.add_field(name="경고를 받은 유저", value=member.mention + f" ({member.id})")
    embed.add_field(name="경고를 부여한 유저", value=issued_by.mention + f" ({issued_by.id})")
    embed.add_field(name="사유", value=reason)
    embed.set_footer(text=datetime.datetime.today().strftime('%Y-%m-%d %X'))
    await ctx_or_message.channel.send(embed=embed)
    await send_to_log(jbot_db_global, guild, embed)
    column_set = jbot_db.set_column({"name": "date", "type": "TEXT", "default": False},
                                    {"name": "user_id", "type": "INTEGER", "default": False},
                                    {"name": "issued_by", "type": "INTEGER", "default": False},
                                    {"name": "reason", "type": "TEXT", "default": False})
    await jbot_db_warns.exec_sql(f"""CREATE TABLE IF NOT EXISTS "{guild.id}_warns" ( {column_set} )""")
    await jbot_db_warns.exec_sql(f"""INSERT INTO "{guild.id}_warns" VALUES (?, ?, ?, ?)""", (current_time, member.id, issued_by.id, reason))
    warn_list = await jbot_db_warns.res_sql(f"""SELECT * FROM "{guild.id}_warns" WHERE user_id=?""", (member.id,))
    guild_data = await jbot_db_global.res_sql("""SELECT warn FROM guild_setup WHERE guild_id=?""", (guild.id,))
    warn_data = json.loads(guild_data[0]["warn"])
    if not bool(warn_data):
        return
    if "mute" in warn_data.keys() and len(warn_list) == warn_data["mute"]:
        mute_role_id = await jbot_db_global.res_sql("SELECT mute_role FROM guild_setup WHERE guild_id=?", (guild.id,))
        if not bool(mute_role_id[0]["mute_role"]):
            return
        mute_role = guild.get_role(mute_role_id[0]["mute_role"])
        await member.add_roles(mute_role, reason="경고 누적")
        await ctx_or_message.channel.send(f"{member.mention} 경고 {warn_data['mute']}회 누적으로 자동으로 뮤트되었어요.")
    if "kick" in warn_data.keys() and len(warn_list) == warn_data["kick"]:
        try:
            await member.send(f"`{guild.name}`에서 추방되었습니다. (사유: 경고 누적으로 자동 추방)")
        except discord.Forbidden:
            await ctx_or_message.channel.send("유저에게 추방 안내 DM을 보내지 못했어요. 바로 추방할께요.")
        await member.kick(reason="경고 누적")
        await ctx_or_message.channel.send(f"`{member}`님이 경고 {warn_data['kick']}회 누적으로 자동으로 추방되었어요.")
    if "ban" in warn_data.keys() and len(warn_list) == warn_data["ban"]:
        try:
            await member.send(f"`{guild.name}`에서 차단되었어요. (사유: 경고 누적으로 자동 차단)")
            await member.send("https://www.youtube.com/watch?v=FXPKJUE86d0")
        except discord.Forbidden:
            await ctx_or_message.channel.send("유저에게 차단 안내 DM을 보내지 못했어요. 바로 차단할께요.")
        await member.ban(reason="경고 누적")
        await ctx_or_message.channel.send(f"`{member}`님이  경고 {warn_data['ban']}회 누적으로 자동으로 차단되었어요.")


async def remove_warn(jbot_db_global: jbot_db.JBotDB, jbot_db_warns: jbot_db.JBotDB, tgt_member: discord.Member, num, ctx: commands.Context = None, message: discord.Message = None):
    global ctx_or_message
    if message is None and ctx is None:
        raise commands.MissingRequiredArgument
    if message is None:
        ctx_or_message = ctx
    if ctx is None:
        ctx_or_message = message
    guild = ctx_or_message.guild
    warn_list = await jbot_db_warns.res_sql(f"""SELECT * FROM "{guild.id}_warns" WHERE user_id=? AND date=?""", (tgt_member.id, num))
    if len(warn_list) == 0:
        raise custom_errors.FailedFinding
    await jbot_db_warns.exec_sql(f"""DELETE FROM "{guild.id}_warns" WHERE user_id=? AND date=?""", (tgt_member.id, num))
    embed = discord.Embed(title="맴버 경고 삭제됨", color=discord.Colour.red())
    embed.add_field(name="경고를 받았던 유저", value=tgt_member.mention + f" ({tgt_member.id})")
    embed.add_field(name="경고를 받은 날짜", value=num)
    embed.set_footer(text=datetime.datetime.today().strftime('%Y-%m-%d %X'))
    await ctx_or_message.channel.send(embed=embed)
    await send_to_log(jbot_db_global, guild, embed)


async def update_setup(jbot_db_global: jbot_db.JBotDB, bot: CustomClient, ctx: commands.Context, msg: discord.Message,
                       embed_list: list, setup_type: str, to_change):
    embed_ok = embed_list[0]
    embed_no = embed_list[1]
    embed_cancel = embed_list[2]
    res = await utils.confirm(bot, ctx, msg)
    if res is True:
        await jbot_db_global.exec_sql(f"UPDATE guild_setup SET {setup_type}=? WHERE guild_id=?", (to_change, ctx.guild.id))
        await msg.edit(embed=embed_ok)
    elif res is False:
        await msg.edit(embed=embed_no)
    elif res is None:
        await msg.edit(embed=embed_cancel)


async def send_to_log(jbot_db_global: jbot_db.JBotDB, guild: discord.Guild, embed: discord.Embed):
    guild_data = await jbot_db_global.res_sql("SELECT log_channel FROM guild_setup WHERE guild_id=?", (guild.id,))
    try:
        log_channel = guild.get_channel(guild_data[0]["log_channel"])
    except IndexError:
        return
    if log_channel is None:
        return
    await log_channel.send(embed=embed)


async def process_before_after(before: list, after: list):
    added = []
    removed = []
    for x in after:
        if x not in before:
            added.append(x)
    for y in before:
        if y not in after:
            removed.append(y)
    return_dict = {"added": added, "removed": removed}
    print(return_dict)
    return return_dict
