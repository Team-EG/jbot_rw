import discord
import random
import asyncio
from discord.ext import commands
from modules import custom_errors


class PartTime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_global = bot.jbot_db_global

    async def cog_check(self, ctx: commands.Context):
        acc_list = await self.jbot_db_global.res_sql("""SELECT * FROM game WHERE user_id=?""", (ctx.author.id,))
        if not bool(acc_list):
            await ctx.send("계정이 존재하지 않습니다. 먼저 계정을 생성해주세요")
            raise custom_errors.IgnoreThis
        return True

    @commands.group(name="알바", description="알바를 합니다.", usage="`알바 [할 알바]`\n(할 수 있는 알바 리스트는 `알바 도움` 명령어를 참고해주세요.)")
    async def part_time(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.part_time_help.__call__(ctx)

    @part_time.command(name="도움")
    async def part_time_help(self, ctx):
        embed = discord.Embed(title="알바 기능 도움말", color=discord.Color.from_rgb(225, 225, 225))
        embed.add_field(name="알바 편의점", value="편의점에서 알바를 합니다.", inline=False)
        #embed.add_field(name="", value="", inline=False)
        #embed.add_field(name="", value="", inline=False)
        await ctx.send(embed=embed)

    @part_time.command(name="편의점")
    async def work_conv(self, ctx, debug=None):
        if debug:
            if ctx.author not in [288302173912170497, 665450122926096395, 558323117802389514]:
                raise custom_errors.NotWhitelisted
        goods_list = {
            "커피": 2500,
            "과자": 1500,
            "아이스크림": 1000,
            "삼각김밥": 900,
            "컵라면": 800,
            "음료수": 1800
        }
        help_embed = discord.Embed(title="편의점 알바", description="10초후 알바가 시작됩니다. 다음 가격표를 잘 보고 계산할 준비를 해주세요. 게임이 시작되면 가격표가 지워집니다.")
        [help_embed.add_field(name=x, value=f"{y}원") for x, y in goods_list.items()]
        msg = await ctx.send(embed=help_embed)
        await asyncio.sleep(10)
        await msg.delete()
        for _x in range(random.randint(3, 10)):
            to_buy = []
            total_price = 0
            _goods_list = goods_list.copy()
            for x in range(random.randint(1, 5)):
                chosen = random.choice(list(_goods_list.keys()))
                to_buy.append(chosen)
                total_price += _goods_list[chosen]
                del _goods_list[chosen]

            init_embed = discord.Embed(title="편의점 알바",
                                       description=f"계산대: `{'`, `'.join(to_buy)}`",
                                       color=discord.Color.from_rgb(225, 225, 225))
            init_embed.set_footer(text="가격을 10초안에 입력해주세요.")
            msg = await ctx.send(embed=init_embed)
            if debug == "-debug":
                await ctx.send(total_price)
            try:
                m = await self.bot.wait_for("message", timeout=10, check=lambda _m: _m.author.id == ctx.author.id and _m.channel.id == msg.channel.id)
                resp = int(m.content)
                if resp != total_price:
                    await m.add_reaction("❌")
                    raise custom_errors.IgnoreThis
                await m.add_reaction("✅")
                await msg.delete()
            except (asyncio.TimeoutError, ValueError, custom_errors.IgnoreThis):
                await msg.delete()
                fail_embed = discord.Embed(title="편의점 알바 실패",
                                           description='편의점 사장: "이런거 하나도 제대로 못해?"\n`편의점 알바에 실패했습니다. 돈을 얻지 못했습니다.`',
                                           color=discord.Color.red())
                return await ctx.send(embed=fail_embed)
        curr_money = (await self.jbot_db_global.res_sql("""SELECT money FROM game WHERE user_id=?""", (ctx.author.id,)))[0]["money"]
        curr_money += 8590
        await self.jbot_db_global.exec_sql("""UPDATE game SET money=? WHERE user_id=?""", (curr_money, ctx.author.id))
        success_embed = discord.Embed(title="편의점 알바 성공", description="알바를 성공적으로 마쳤습니다. `8590`원을 알바비로 얻었습니다.", color=discord.Color.green())
        await ctx.send(embed=success_embed)

    @part_time.command(name="학원강사")
    async def part_time_tutor(self, ctx):
        return await ctx.send("아직 준비중인 기능입니다. ~~일해라 GPM567~~")


def setup(bot):
    bot.add_cog(PartTime(bot))
