import asyncio
import discord
import json
import os
import logging
import nest_asyncio
from discord.ext import commands
from modules import jbot_db
from modules import custom_errors

nest_asyncio.apply()
loop = asyncio.get_event_loop()

logger = logging.getLogger('discord')
logging.basicConfig(level=logging.INFO)  # DEBUG/INFO/WARNING/ERROR/CRITICAL
handler = logging.FileHandler(filename=f'jbot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

print("Removing all temp files...")
temp_file_list = os.listdir("temp")
for fl in temp_file_list:
    os.remove("temp/"+fl)
print("Done!")

jbot_db_global = jbot_db.JBotDB("jbot_db_global")
logger.info("DB Loaded.")


def get_bot_settings() -> dict:
    with open('bot_settings.json', 'r') as f:
        return json.load(f)


if get_bot_settings()["debug"]:
    print("Bot running in debug mode.")


async def get_prefix(bot, message):
    data = (await jbot_db_global.res_sql("""SELECT prefix FROM guild_setup WHERE guild_id=?""", (message.guild.id,)))
    try:
        guild_prefix = data[0]["prefix"]
    except IndexError:
        await jbot_db_global.exec_sql("INSERT INTO guild_setup(guild_id) VALUES (?)", (message.guild.id,))
        data = (await jbot_db_global.res_sql("""SELECT prefix FROM guild_setup WHERE guild_id=?""", (message.guild.id,)))
        guild_prefix = data[0]["prefix"]
    except KeyError:
        guild_prefix = "제이봇 "
    return commands.when_mentioned_or(*[guild_prefix])(bot, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix, help_command=None)


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
    if choose == "load":
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
        return user == ctx.author and str(reaction) in emoji_list

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


# cog를 불러오는 스크립트
for filename in os.listdir("./cogs"):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename.replace(".py", "")}')

bot.run(get_bot_settings()["canary_token"])
