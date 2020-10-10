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
import json
import logging
from discord.ext import commands
from modules import custom_errors
from modules import utils


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
        report_required = False
        embed = discord.Embed(title="이런! ", colour=discord.Color.red())
        if isinstance(error, commands.BotMissingPermissions):
            embed.title += "봇이 필요한 권한을 가지고 있지 않네요..."
            embed.description = f"필요한 권한: `{', '.join(error.missing_perms)}`"
        elif isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            embed.title = "Aㅓ... 합필이면... 잘 알아두세요. 당신은 이 명령어를 실행할 권한이 읎어요."
            embed.description = f"필요한 권한: `{', '.join(error.missing_perms)}`"
        elif isinstance(error, commands.CheckFailure):
            embed.title = "당신은 이 명령어를 실행할 권한이 없네요..."
            embed.description = "자세한 내용은 서버 관리자나 [Team EG 디스코드 서버](https://discord.gg/gqJBhar)에 문의해주세요."
        elif isinstance(error, commands.CommandOnCooldown):
            cooldown = int(f"{error.retry_after}".split(".")[0])
            embed.title += "아직 쿨다운이 남았어요..."
            embed.description = f"남은 시간: `{utils.parse_second(cooldown)}`"
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.title += "누락된 필수 항목이 있어요..."
            embed.description = f"누락된 항목들: `{error.param.name}`"
        elif isinstance(error, custom_errors.NotWhitelisted):
            embed.title += "해당 명령어는 Team EG 관리자만 사용할 수 있어요..."
            embed.description = "~~아니 근데 이 명령어는 어떻게 찾으셨어요?~~"
        elif isinstance(error, custom_errors.NotGuildOwner):
            embed.title += "이 서버의 소유자가 아니네요..."
            embed.description = "해당 명령어는 서버 소유자만 사용할 수 있어요."
        elif isinstance(error, custom_errors.IllegalString):
            embed.title += "이 명령어 사용시에는 입력이 금지된 단어가 포함되어있네요..."
            embed.description = f"금지된 단어 리스트: `{', '.join(error.banned)}`"
        elif isinstance(error, custom_errors.NotAdmin):
            embed.title += "이 서버의 관리자가 아니네요..."
            embed.description = "해당 명령어는 서버 관리자만 사용할 수 있어요."
        elif isinstance(error, custom_errors.FailedFinding):
            embed.title += "DB에 찾으시는 것이 없네요..."
            embed.description = "이것이 오류라고 생각된다면 [이 링크를 통해 알려주세요.](https://discord.gg/gqJBhar)"
        elif isinstance(error, custom_errors.NotEnabled):
            embed.title += "이 명령어를 사용하기 위해 필요한 기능이 꺼져있네요."
            embed.description = f"이 명령어를 사용하기 위해서는 `{error.not_enabled}` 기능을 사용해야 해요."
        elif isinstance(error, custom_errors.IgnoreThis):
            return
        else:
            logger = logging.getLogger("discord")
            logger.error(error)
            embed.title += "예기치 못한 오류가 발생했어요..."
            embed.description = f"```py\n{error}```\n" \
                                f"이 오류 정보를 개발자에게 알려주시면 봇 개선에 도움이 됩니다. [이 링크를 통해 알려주세요.](https://discord.gg/gqJBhar)"
            report_required = True
        await ctx.message.add_reaction("⏰") if isinstance(error, commands.CommandOnCooldown) else await ctx.message.add_reaction("⚠")
        await ctx.send(embed=embed)
        if report_required:
            msg = await ctx.send("잠시만요! 이 오류 정보를 개발자에게 전송할까요? 오류 전송시 오류 내용과 명령어를 실행한 메시지 내용이 전달됩니다.")
            res = await utils.confirm(self.bot, ctx, msg)
            if not res:
                return await ctx.send("전송을 취소했어요.")
            report_embed = discord.Embed(title="예기치 않은 오류 발생",
                                         description=f"예외\n"
                                                     f"```py\n{error}```\n"
                                                     f"메시지\n```{ctx.message.content}```\n\n",
                                         colour=discord.Color.red(),
                                         timestamp=ctx.message.created_at).set_footer(text=f"유저: {str(ctx.author)} ({ctx.author.id})")
            await self.bot.get_guild(743330013360947231).get_channel(764359951266480189).send(embed=report_embed)
            await ctx.send("성공적으로 전송했어요!")


def setup(bot):
    bot.add_cog(Error(bot))
