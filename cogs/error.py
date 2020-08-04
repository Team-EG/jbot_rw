import discord
import json
import logging
from discord.ext import commands
from modules import custom_errors


class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        with open("bot_settings.json", "r") as f:
            bot_settings = json.load(f)
        if bot_settings["debug"] is True:
            await ctx.send("디버그 모드가 켜져있습니다.")
            raise error
        embed = discord.Embed(title="오류 발생!", description="명령어를 실행하던 도중 오류가 발생했습니다.", colour=discord.Color.red())
        if isinstance(error, commands.BotMissingPermissions):
            embed.add_field(name="BotMissingPermissions", value=f"봇이 필요한 권한을 가지고 있지 않습니다.\n"
                                                                f"필요한 권한: `{', '.join(error.missing_perms)}`")
        elif isinstance(error, commands.CommandNotFound):
            return # await ctx.message.add_reaction(emoji="🤔")
        elif isinstance(error, commands.MissingPermissions):
            embed.add_field(name="MissingPermissions", value="Aㅓ... 합필이면... 잘 알아두세요. 당신은 이 명령어를 실행할 권한이 읎어요.\n"
                                                             f"필요한 권한: `{', '.join(error.missing_perms)}`")
        elif isinstance(error, commands.CheckFailure):
            embed.add_field(name="CheckFailure", value="이 서버에서는 해당 명령어를 사용할 수 없도록 설정되어있습니다.")
        elif isinstance(error, commands.CommandOnCooldown):
            embed.add_field(name="CommandOnCooldown", value=f'쿨다운이 아직 {error.retry_after:.2f}초 남았습니다.')
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.add_field(name="MissingRequiredArgument", value=f"누락된 필수 항목이 있습니다. (`{error.param.name}`)")
        elif isinstance(error, custom_errors.NotWhitelisted):
            embed.add_field(name="NotWhitelisted", value="화이트리스트에 등록된 유저가 아닙니다.")
        elif isinstance(error, custom_errors.NotGuildOwner):
            embed.add_field(name="NotGuildOwner", value="이 서버의 소유자가 아닙니다.")
        elif isinstance(error, custom_errors.IllegalString):
            embed.add_field(name="IllegalString", value="이 명령어 사용시에는 입력이 금지된 단어가 포함되어있습니다.\n"
                                                        f"금지된 단어 리스트: `{', '.join(error.banned)}`")
        elif isinstance(error, custom_errors.NotAdmin):
            embed.add_field(name="NotAdmin", value="이 서버의 관리자가 아닙니다.")
        elif isinstance(error, custom_errors.FailedFinding):
            embed.add_field(name="FailedFinding", value="DB에서 해당 값의 검색을 실패했습니다.")
        else:
            logger = logging.getLogger("discord")
            logger.error(error)
            embed.add_field(name="예기치 않은 오류 발생", value=f"```py\n{error}```")
        await ctx.message.add_reaction("⚠")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Error(bot))
