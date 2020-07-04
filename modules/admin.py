import discord
import datetime
import json
import time
from . import jbot_db, confirm
from discord.ext import commands


async def warn(jbot_db_warns: jbot_db.JBotDB, member: discord.Member, issued_by: discord.Member, reason=None, ctx: commands.Context = None,
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
    await send_to_log(guild, embed)
    column_set = jbot_db.set_column(date=None, user_id=None, reason=None, issued_by=None)
    lvl_exist = await jbot_db_warns.check_if_table_exist(f"{guild.id}_warns")
    if not lvl_exist:
        await jbot_db_warns.create_table("jbot_db_warns", f"{guild.id}_warns", column_set)
    await jbot_db_warns.insert_db(f"{guild.id}_warns", "date", current_time)
    await jbot_db_warns.update_db(f"{guild.id}_warns", "user_id", member.id, "date", current_time)
    await jbot_db_warns.update_db(f"{guild.id}_warns", "reason", reason, "date", current_time)
    await jbot_db_warns.update_db(f"{guild.id}_warns", "issued_by", issued_by.id, "date", current_time)


async def update_setup(jbot_db_global: jbot_db.JBotDB, bot: commands.Bot, ctx: commands.Context, msg: discord.Message,
                       embed_list: list, setup_type: str, to_change: str):
    with open("cache/guild_setup.json", "r") as f:
        guild_data = json.load(f)
    embed_ok = embed_list[0]
    embed_no = embed_list[1]
    embed_cancel = embed_list[2]
    res = await confirm.confirm(bot, ctx, msg)
    if res is True:
        await jbot_db_global.update_db("guild_setup", setup_type, to_change, "guild_id", ctx.guild.id)
        if to_change == "None":
            to_change = None
        elif to_change == "False":
            to_change = False
        elif to_change == "True":
            to_change = bool(to_change)
        guild_data[str(ctx.guild.id)][setup_type] = to_change
        await msg.edit(embed=embed_ok)
    elif res is False:
        await msg.edit(embed=embed_no)
    elif res is None:
        await msg.edit(embed=embed_cancel)
    with open("cache/guild_setup.json", "w") as f:
        json.dump(guild_data, f, indent=4)


async def send_to_log(guild: discord.Guild, embed: discord.Embed):
    with open("cache/guild_setup.json", "r") as f:
        guild_data = json.load(f)
    if guild_data[str(guild.id)]["log_channel"] is None:
        return
    log_channel = guild.get_channel(int(guild_data[str(guild.id)]["log_channel"]))
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
