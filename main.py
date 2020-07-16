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
for x in temp_file_list:
    os.remove("temp/"+x)
print("Done!")

jbot_db_global = jbot_db.JBotDB("jbot_db_global")
logger.info("DB Loaded.")


def get_bot_settings():
    with open('bot_settings.json', 'r') as f:
        return json.load(f)


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
async def cog(ctx, choose, cog_name=None):
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


# cog를 불러오는 스크립트
for filename in os.listdir("./cogs"):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename.replace(".py", "")}')

bot.run(get_bot_settings()["canary_token"])
