import asyncio
import discord
import json
import os
import logging
import nest_asyncio
import pickle
from discord.ext import commands
from modules import jbot_db
from modules import custom_errors
from modules import db_cache

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

print("Connecting to DB and downloading data from DB...")
jbot_db_global = jbot_db.JBotDB("jbot_db_global")
loop.run_until_complete(db_cache.init_cache(jbot_db_global, "guild_setup"))
print("Finished!")
logger.info("DB Loaded.")


def get_bot_settings():
    with open('bot_settings.json', 'r') as f:
        return json.load(f)


async def get_prefix(bot, message):
    cached_data = await db_cache.load_cache("guild_setup")
    try:
        guild_prefix = cached_data[str(message.guild.id)]["prefix"]
    except KeyError:
        await message.channel.send("이런! 캐시에서 서버 설정을 불러오던 도중 문제가 발생했어요! 계속 이 오류가 나온다면 먼저 저에게 관리자와 메시지 보내기 권한을 없애준 다음 `eunwoo1104#9600`으로 DM을 보내주세요.")
        await db_cache.reload_cache(jbot_db_global, "guild_setup")
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


@bot.command(name="종료")
@commands.check(is_whitelisted)
async def shutdown(ctx):
    for cog_file in os.listdir("./cogs"):
        if cog_file.endswith('.py'):
            bot.unload_extension(f'cogs.{cog_file.replace(".py", "")}')
    await jbot_db_global.close_db()
    await ctx.send("봇을 종료할께요. 봇 로그 파일은 DM을 확인해주세요.")
    log_file = discord.File("jbot.log")
    await ctx.author.send(file=log_file)
    await bot.close()
    print("Bye!")
    os._exit(0)

# cog를 불러오는 스크립트
for filename in os.listdir("./cogs"):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename.replace(".py", "")}')

bot.run(get_bot_settings()["canary_token"])
