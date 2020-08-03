import discord
import datetime
import json
import time
from . import jbot_db, confirm
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
    embed = discord.Embed(title="맴버 경고", description=str(current_time), color=discord.Colour.red())
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
    warn_exist = await jbot_db_warns.res_sql("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f"{guild.id}_warns",), return_raw=True)
    if not bool(len(warn_exist)):
        await jbot_db_warns.exec_sql(f"""CREATE TABLE "{guild.id}_warns" ( {column_set} )""")
    await jbot_db_warns.exec_sql(f"""INSERT INTO "{guild.id}_warns" VALUES (?, ?, ?, ?)""", (current_time, member.id, issued_by.id, reason))
    warn_list = await jbot_db_warns.res_sql(f"""SELECT * FROM "{guild.id}_warns" WHERE user_id=?""", (member.id,))
    if len(warn_list) == 3:
        mute_role_id = await jbot_db_global.res_sql("SELECT mute_role FROM guild_setup WHERE guild_id=?", (guild.id,))
        if not bool(mute_role_id[0]["mute_role"]):
            return
        mute_role = guild.get_role(mute_role_id[0]["mute_role"])
        await member.add_roles(mute_role, reason="경고 누적")
        await ctx_or_message.channel.send(f"{member.mention} 경고 3회 누적으로 자동으로 뮤트되었습니다.")
    if len(warn_list) == 6:
        await member.send(f"`{guild.name}`에서 추방되었습니다. (사유: 경고 누적으로 자동 추방)")
        await member.kick(reason="경고 누적")
        await ctx_or_message.channel.send(f"`{member}` 경고 6회 누적으로 자동으로 추방되었습니다.")
    if len(warn_list) == 9:
        await member.send(f"`{guild.name}`에서 차단되었습니다. (사유: 경고 누적으로 자동 차단)")
        await member.send("https://www.youtube.com/watch?v=FXPKJUE86d0")
        await member.ban(reason="경고 누적")
        await ctx_or_message.channel.send(f"`{member}` 경고 9회 누적으로 자동으로 차단되었습니다.")


async def update_setup(jbot_db_global: jbot_db.JBotDB, bot: commands.Bot, ctx: commands.Context, msg: discord.Message,
                       embed_list: list, setup_type: str, to_change):
    embed_ok = embed_list[0]
    embed_no = embed_list[1]
    embed_cancel = embed_list[2]
    res = await confirm.confirm(bot, ctx, msg)
    if res is True:
        await jbot_db_global.exec_sql(f"UPDATE guild_setup SET {setup_type}=? WHERE guild_id=?", (to_change, ctx.guild.id))
        await msg.edit(embed=embed_ok)
    elif res is False:
        await msg.edit(embed=embed_no)
    elif res is None:
        await msg.edit(embed=embed_cancel)


async def send_to_log(jbot_db_global: jbot_db.JBotDB, guild: discord.Guild, embed: discord.Embed):
    guild_data = await jbot_db_global.res_sql("SELECT log_channel FROM guild_setup WHERE guild_id=?", (guild.id,))
    log_channel = guild.get_channel(guild_data[0]["log_channel"])
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
