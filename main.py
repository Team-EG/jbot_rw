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
import asyncio
import discord
import json
import os
import logging
import nest_asyncio
from discord.ext import commands
from modules import custom_errors
from modules.cilent import CustomClient

nest_asyncio.apply()
loop = asyncio.get_event_loop()

logger = logging.getLogger('discord')
logging.basicConfig(level=logging.INFO)  # DEBUG/INFO/WARNING/ERROR/CRITICAL
handler = logging.FileHandler(filename=f'jbot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

print("Removing all temp files...")
[os.remove("temp/"+x) for x in os.listdir("temp")]
print("Done!")


def get_bot_settings() -> dict:
    with open('bot_settings.json', 'r') as f:
        return json.load(f)


if get_bot_settings()["debug"]:
    print("Bot running in debug mode.")


async def get_prefix(bot, message):
    jbot_db_global = bot.jbot_db_global
    try:
        if message.guild is None:
            guild_prefix = "제이봇 "
        else:
            data = (await jbot_db_global.res_sql("""SELECT prefix FROM guild_setup WHERE guild_id=?""", (message.guild.id,)))
            guild_prefix = data[0]["prefix"]
    except IndexError:
        await jbot_db_global.exec_sql("INSERT INTO guild_setup(guild_id) VALUES (?)", (message.guild.id,))
        data = (await jbot_db_global.res_sql("""SELECT prefix FROM guild_setup WHERE guild_id=?""", (message.guild.id,)))
        guild_prefix = data[0]["prefix"]
    return commands.when_mentioned_or(*['제이봇 ', 'j!', guild_prefix])(bot, message)


bot = CustomClient(command_prefix=get_prefix, help_command=None)


async def is_whitelisted(ctx):
    if ctx.author.id in get_bot_settings()["whitelist"]:
        return True
    raise custom_errors.NotWhitelisted


@bot.event
async def on_ready():
    shards = bot.shard_ids
    if bot.shard_ids is None:
        shards = [1]
    print("Running " + str(len(shards)) + " shards.")
    print("Bot Ready.")
    logger.info("Bot online.")
    await bot.change_presence(activity=discord.Game("테스트"))


@bot.command()
@commands.check(is_whitelisted)
async def _old_cog(ctx, choose, cog_name=None):
    global embed2
    embed1 = discord.Embed(title="Cog 명령어", description="잠시만 기다려주세요...", colour=discord.Color.from_rgb(225, 225, 225))
    msg = await ctx.send(embed=embed1)
    if choose == "update":
        updated_cogs = []
        for cog_file in os.listdir("./cogs"):
            if cog_file.endswith('.py'):
                bot.reload_extension(f'cogs.{cog_file.replace(".py", "")}')
            updated_cogs.append(cog_file)
        embed2 = discord.Embed(title="Cog 명령어", description=f"Cog 업데이트 완료!\n`{', '.join(updated_cogs)}`", colour=discord.Color.from_rgb(225, 225, 225))
        await msg.edit(embed=embed2)
    elif choose == "load":
        bot.load_extension("cogs." + cog_name)
        embed2 = discord.Embed(title="Cog 명령어", description=f"`{cog_name}` 로드 완료!", colour=discord.Color.from_rgb(225, 225, 225))
    elif choose == "reload":
        bot.reload_extension("cogs." + cog_name)
        embed2 = discord.Embed(title="Cog 명령어", description=f"`{cog_name}` 리로드 완료!", colour=discord.Color.from_rgb(225, 225, 225))
    elif choose == "unload":
        bot.unload_extension("cogs." + cog_name)
        embed2 = discord.Embed(title="Cog 명령어", description=f"`{cog_name}` 언로드 완료!", colour=discord.Color.from_rgb(225, 225, 225))
    else:
        embed2 = discord.Embed(title="Cog 명령어", description=f"`{choose}` 옵션은 존재하지 않습니다.", colour=discord.Colour.red())
    await msg.edit(embed=embed2)


@bot.command(name="cog", aliases=["cogs"])
@commands.check(is_whitelisted)
async def _new_cog(ctx):
    load = "⏺"
    unload = "⏏"
    reload = "🔄"
    up = "⬆"
    down = "⬇"
    stop = "⏹"
    emoji_list = [load, unload, reload, up, down, stop]
    msg = await ctx.send("잠시만 기다려주세요...")
    for x in emoji_list:
        await msg.add_reaction(x)
    cog_list = [c.replace(".py", "") for c in os.listdir("./cogs") if c.endswith(".py")]
    cogs_dict = {}
    base_embed = discord.Embed(title="제이봇 Cog 관리 패널", description=f"`cogs` 폴더의 Cog 개수: {len(cog_list)}개")
    for x in cog_list:
        if x in [x.lower() for x in bot.cogs.keys()]:
            cogs_dict[x] = True
        else:
            cogs_dict[x] = False
    cogs_keys = [x for x in cogs_dict.keys()]
    selected = cogs_keys[0]
    selected_num = 0

    def check(reaction, user):
        return user == ctx.author and str(reaction) in emoji_list and reaction.message.id == msg.id

    while True:
        tgt_embed = base_embed.copy()
        for k, v in cogs_dict.items():
            if k == selected:
                k = "▶" + k
            tgt_embed.add_field(name=k, value=f"상태: {'로드됨' if v else '언로드됨'}", inline=False)
        await msg.edit(content=None, embed=tgt_embed)
        try:
            reaction, user = await bot.wait_for("reaction_add", check=check, timeout=60)
        except asyncio.TimeoutError:
            await msg.clear_reactions()
            await msg.edit(content="Cog 관리 패널이 닫혔습니다.", embed=None)
            break
        if str(reaction) == down:
            if selected_num+1 == len(cogs_keys):
                wd = await ctx.send("이미 마지막 Cog 입니다.")
                await wd.delete(delay=3)
            else:
                selected_num += 1
                selected = cogs_keys[selected_num]
        elif str(reaction) == up:
            if selected_num == 0:
                wd = await ctx.send("이미 첫번째 Cog 입니다.")
                await wd.delete(delay=3)
            else:
                selected_num -= 1
                selected = cogs_keys[selected_num]
        elif str(reaction) == reload:
            if not cogs_dict[selected]:
                wd = await ctx.send("먼저 Cog를 로드해주세요.")
                await wd.delete(delay=3)
            else:
                bot.reload_extension("cogs." + selected)
        elif str(reaction) == unload:
            if not cogs_dict[selected]:
                wd = await ctx.send("이미 Cog가 언로드되있습니다.")
                await wd.delete(delay=3)
            else:
                bot.unload_extension("cogs." + selected)
                cogs_dict[selected] = False
        elif str(reaction) == load:
            if cogs_dict[selected]:
                wd = await ctx.send("이미 Cog가 로드되있습니다.")
                await wd.delete(delay=3)
            else:
                bot.load_extension("cogs." + selected)
                cogs_dict[selected] = True
        elif str(reaction) == stop:
            await msg.clear_reactions()
            await msg.edit(content="Cog 관리 패널이 닫혔습니다.", embed=None)
            break
        await msg.remove_reaction(reaction, ctx.author)


@bot.command(name="종료")
@commands.is_owner()
async def _close(ctx):
    await ctx.send("봇을 종료합니다.")
    [bot.unload_extension(f"cogs.{x.replace('.py', '')}") for x in os.listdir("./cogs") if x.endswith('.py')]
    await bot.jbot_db_global.close_db()
    await bot.jbot_db_warns.close_db()
    await bot.jbot_db_level.close_db()
    await bot.close()


[bot.load_extension(f"cogs.{x.replace('.py', '')}") for x in os.listdir("./cogs") if x.endswith('.py')]

bot.run_bot(canary=True)
