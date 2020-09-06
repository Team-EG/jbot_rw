import discord
import json
import aiohttp
import datetime
import time
from discord.ext import commands
from modules import utils
from modules import custom_errors


class Stock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jbot_db_global = bot.jbot_db_global

    async def cog_check(self, ctx: commands.Context):
        acc_list = await self.jbot_db_global.res_sql("""SELECT * FROM game WHERE user_id=?""", (ctx.author.id,))
        if not bool(acc_list):
            await ctx.send("계정이 존재하지 않습니다. 먼저 계정을 생성해주세요")
            raise custom_errors.IgnoreThis
        return True

    @commands.group(name="주식", description="주식 관련 명령어입니다.", usage="`주식 도움` 명령어를 참고해주세요.")
    async def stock(self, ctx):
        if ctx.invoked_subcommand is None:
            stocks = await self.jbot_db_global.res_sql("""SELECT * FROM stock""")
            embed = discord.Embed(title="주식 리스트", description="주식 관련 명령어는 `제이봇 주식 도움` 명령어를 참고해주세요.",
                                  color=discord.Color.from_rgb(225, 225, 225),
                                  timestamp=datetime.datetime.fromtimestamp(self.bot.last_stock_change, tz=datetime.timezone(datetime.timedelta(hours=9))))
            current_time = round(time.time())
            embed.set_footer(text=f"마지막 업데이트: {utils.parse_second(current_time - self.bot.last_stock_change)} 전")
            for x in stocks:
                history = [int(a) for a in x["history"].split(',')]
                price_changed = history[-1] - history[-2]
                text = None
                if price_changed > 0:
                    text = f"+{price_changed}원"
                elif price_changed == 0:
                    text = f"가격 변동 없음"
                elif price_changed < 0:
                    text = f"-{abs(price_changed)}원"
                embed.add_field(name=x["name"], value=f"{x['curr_price']}원 ({text})", inline=False)
            await ctx.send(embed=embed)

    @stock.command(name="도움")
    async def stock_help(self, ctx):
        embed = discord.Embed(title="주식 명령어 도움말", color=discord.Color.from_rgb(225, 225, 225))
        embed.add_field(name=f"주식", value=f"현재 주식 차트를 보여줍니다. `주식 차트` 명령어로도 가능합니다.", inline=False)
        embed.add_field(name=f"주식 그래프 (주식 이름)", value=f"해당 주식의 최근 가격 그래프를 봅니다. 이름을 입력하지 않으면 모든 주식을 보여줍니다.", inline=False)
        embed.add_field(name=f"주식 구매 [주식 이름 (키워드)] [개수]", value=f"해당 주식을 해당 개수만큼 구매합니다.\n예시: `제이봇 주식 구매 Team 10` -> Team EG 주식을 10개 구매합니다.", inline=False)
        embed.add_field(name=f"주식 판매 [구매 코드]", value=f"해당 소유 주식을 판매합니다. 구매 코드는 `지갑` 명령어에서 2번째 페이지를 통해 확인 가능합니다.", inline=False)
        await ctx.send(embed=embed)

    @stock.command(name="차트")
    async def stock_chart(self, ctx):
        await self.stock.__call__(ctx)

    @stock.command(name="그래프")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def stock_graph(self, ctx, name=None):
        data = await self.jbot_db_global.res_sql("""SELECT name, history FROM stock""")
        if name is not None:
            data = [x for x in data if name in x["name"]]
        header = {"Content-Type": "application/json"}
        body = {"stock_list": data}
        async with aiohttp.ClientSession() as session:
            async with session.post(url="http://jebserver.iptime.org:8901/request_image", headers=header, json=body) as resp:
                image_url = await resp.text()

        embed = discord.Embed(title="주식 그래프",
                              timestamp=ctx.message.created_at,
                              color=discord.Color.from_rgb(225, 225, 225))
        embed.description = "현재 서버 글꼴 문제로 한글이 비정상적으로 출력되는 문제가 있습니다."
        embed.set_image(url=str(image_url.replace('"', '')))
        embed.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @stock.command(name="구매", aliases=["매수"])
    async def stock_buy(self, ctx, name, amount: int):
        user_data = (await self.jbot_db_global.res_sql("""SELECT money, stock FROM game WHERE user_id=?""", (ctx.author.id,)))[0]
        current_time = round(time.time())
        stock_data = json.loads(user_data["stock"])
        tgt_stock = [x for x in await self.jbot_db_global.res_sql("""SELECT name, curr_price FROM stock""") if name in x["name"]][0]
        money_req = amount * tgt_stock["curr_price"]
        if money_req > user_data["money"]:
            return await ctx.send("돈이 부족합니다.")
        embed = discord.Embed(title="주식 구매", description=f"정말로 주식을 {amount}개 구매할까요? 가격은 `{money_req}`원 입니다.",
                              color=discord.Color.from_rgb(225, 225, 225))
        msg = await ctx.send(embed=embed)
        res = await utils.confirm(self.bot, ctx=ctx, msg=msg)
        if not res:
            cancel_embed = discord.Embed(title="주식 구매", description="주식 구매를 취소했습니다.", color=discord.Color.red())
            return await msg.edit(embed=cancel_embed)
        stock_data[str(current_time)] = {"name": tgt_stock["name"], "amount": amount, "bought_price": money_req}
        stock_data = json.dumps(stock_data)
        await self.jbot_db_global.exec_sql("""UPDATE game SET money=?, stock=? WHERE user_id=?""",
                                           (user_data["money"] - money_req, stock_data, ctx.author.id))
        ok_embed = discord.Embed(title="주식 구매 완료",
                                 description=f"성공적으로 `{tgt_stock['name']}` 주식을 {amount}개 구매했습니다!",
                                 color=discord.Color.green())
        await msg.edit(embed=ok_embed)

    @stock.command(name="판매", aliases=["매도"])
    async def stock_sell(self, ctx, code: int):
        user_data = (await self.jbot_db_global.res_sql("""SELECT money, stock FROM game WHERE user_id=?""", (ctx.author.id,)))[0]
        stock_data = json.loads(user_data["stock"])
        if str(code) not in stock_data.keys():
            return await ctx.send("해당 코드를 찾을 수 없습니다.")
        to_sell = stock_data[str(code)]
        tgt_stock = [x for x in await self.jbot_db_global.res_sql("""SELECT name, curr_price FROM stock""") if to_sell["name"] in x["name"]][0]
        income = int(to_sell["amount"]) * int(tgt_stock["curr_price"])
        conf_embed = discord.Embed(title="주식 판매",
                                   description=f"정말로 {to_sell['name']} 주식을 {to_sell['amount']}개 판매할까요? (판매 금액: {income}원)",
                                   color=discord.Color.from_rgb(225, 225, 225))
        msg = await ctx.send(embed=conf_embed)
        res = await utils.confirm(self.bot, ctx=ctx, msg=msg)
        if not res:
            cancel_embed = discord.Embed(title="주식 판매", description="주식 판매를 취소했습니다.", color=discord.Color.red())
            return await msg.edit(embed=cancel_embed)
        del stock_data[str(code)]
        stock_data = json.dumps(stock_data)
        await self.jbot_db_global.exec_sql("""UPDATE game SET money=?, stock=? WHERE user_id=?""", (user_data["money"] + income, stock_data, ctx.author.id))
        ok_embed = discord.Embed(title="주식 판매 완료",
                                 description=f"주식 판매가 완료되었습니다.",
                                 color=discord.Color.green())
        await msg.edit(embed=ok_embed)


def setup(bot):
    bot.add_cog(Stock(bot))
