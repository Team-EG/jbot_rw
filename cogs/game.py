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
import random
import asyncio
import time
import json
from discord.ext import commands
from modules import custom_errors, utils
from modules.cilent import CustomClient


class Game(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.jbot_db_global = bot.jbot_db_global

    async def cog_check(self, ctx: commands.Context):
        if ctx.invoked_with in ["계정생성", "계정생선"]:
            return True
        acc_list = await self.jbot_db_global.res_sql("""SELECT * FROM game WHERE user_id=?""", (ctx.author.id,))
        if not bool(acc_list):
            await ctx.send("계정이 존재하지 않습니다. 먼저 계정을 생성해주세요")
            raise custom_errors.IgnoreThis
        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        if ctx.invoked_with in ["계정생성", "계정생선"]:
            return
        acc_list = await self.jbot_db_global.res_sql("""SELECT * FROM game WHERE user_id=?""", (ctx.author.id,))
        money_borrow_info = [acc_list[0]["borrowed_money"], acc_list[0]["borrowed_deadline"]]
        if not bool(money_borrow_info[1]):
            pass
        elif float(money_borrow_info[1]) - time.time() < 0:
            if acc_list[0]["money"] < money_borrow_info[0]:
                await self.jbot_db_global.exec_sql("""DELETE FROM game WHERE user_id=?""", (ctx.author.id,))
                embed = discord.Embed(title="게임 오버 - 그러게 대출을 미리 갚았어야죠...",
                                      description="당신이 대출을 제때 갚지 않았기 때문에 당신의 모든 재산이 압류되었고 이 상황이 믿기지 않은 당신은 한강으로 가버렸습니다.\n"
                                                  "(게임 계정이 삭제되었습니다. 게임 기능을 사용하기 위해서는 계정을 다시 생성해주세요.)",
                                      color=discord.Color.red())
                await ctx.send(embed=embed)
                raise custom_errors.IgnoreThis
            money = acc_list[0]["money"] - money_borrow_info[0]
            await self.jbot_db_global.exec_sql("""UPDATE game SET money=?, borrowed_money=0, borrowed_deadline=NULL WHERE user_id=?""", (money, ctx.author.id))
            await ctx.send("밀린 대출 금액을 자동으로 갚았습니다.")
        elif float(money_borrow_info[1]) - time.time() < 60*60:
            tgt_time = round(float(money_borrow_info[1]) - time.time())
            await ctx.send(f"대출한 돈을 갚을 시기가 얼마 남지 않았습니다. 남은 시간: {utils.parse_second(tgt_time)}")
        return

    async def cog_after_invoke(self, ctx: commands.Context):
        acc_list = await self.jbot_db_global.res_sql("""SELECT money FROM game WHERE user_id=?""", (ctx.author.id,))
        if not bool(acc_list):
            return
        if acc_list[0]["money"] < 0:
            await self.jbot_db_global.exec_sql("""DELETE FROM game WHERE user_id=?""", (ctx.author.id,))
            embed = discord.Embed(title="게임 오버 - 마이너스 통장",
                                  description="당신은 통장이 마이너스 통장이 된 이후 빚을 값기 위해 막노동을 했지만 전혀 나아지지 않아 결국 한강에 가버렸습니다.\n"
                                              "(게임 계정이 삭제되었습니다. 게임 기능을 사용하기 위해서는 계정을 다시 생성해주세요.)",
                                  color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name="계정생성", description="게임 기능의 계정을 생성합니다.")
    async def create_account(self, ctx):
        acc_list = await self.jbot_db_global.res_sql("""SELECT * FROM game WHERE user_id=?""", (ctx.author.id,))
        if bool(acc_list):
            return await ctx.send("이미 계정이 존재합니다.")
        random_num = random.randint(1000, 10000)
        await self.jbot_db_global.exec_sql("""INSERT INTO game(user_id, money) VALUES (?, ?)""", (ctx.author.id, random_num))
        embed = discord.Embed(title="계정 생성 완료!", description=f"현재 당신의 지갑에는 `{random_num}`원이 있습니다.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name="계정생선", description="대충 Team EG에서 개발되다가 취소된 봇에 있던 이스터에그입니다.")
    async def fish_account(self, ctx):
        embed = discord.Embed(title="생선이요...?", description="`계정생성` 명령어를 사용해주세요!")
        embed.set_image(url='https://img5.yna.co.kr/etc/inner/KR/2019/10/24/AKR20191024168000051_01_i_P2.jpg')
        embed.set_footer(text=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(name="계정삭제", description="게임 기능의 계정을 삭제합니다.")
    async def remove_account(self, ctx):
        confirm_embed = discord.Embed(title="계정 삭제", description=f"정말로 계정을 삭제할까요? 계정을 삭제할 경우 __**모든 게임 관련 데이터**__가 삭제됩니다.", color=discord.Color.red())
        msg = await ctx.send(embed=confirm_embed)
        res = await utils.confirm(self.bot, ctx, msg)
        deleted_embed = discord.Embed(title="계정 삭제 완료", description=f"계정이 삭제되었습니다.", color=discord.Color.red())
        failed_embed = discord.Embed(title="계정 삭제 취소", description=f"계정 삭제가 취소되었습니다..", color=discord.Color.red())
        if res:
            await self.jbot_db_global.exec_sql("""DELETE FROM game WHERE user_id=?""", (ctx.author.id,))
            return await msg.edit(embed=deleted_embed)
        await msg.edit(embed=failed_embed)

    @commands.command(name="한강가즈아", description="한강으로 갑니다.")
    async def goto_hangang(self, ctx):
        go_or_nogo = random.randint(1, 100)
        if go_or_nogo <= 95:
            current_debt = (await self.jbot_db_global.res_sql("""SELECT borrowed_money FROM game WHERE user_id=?""", (ctx.author.id,)))[0]["borrowed_money"]
            amount = 2000000 + int(current_debt)
            borrowed_deadline = time.time() + (60 * 60 * 72)
            embed = discord.Embed(title="한강가즈아 실패", description="당신은 한강에 뛰어내렸지만 구조되었습니다. 벌금으로 빚 200만원이 추가되었습니다.", color=discord.Color.green())
            await self.jbot_db_global.exec_sql("""UPDATE game SET borrowed_money=?, borrowed_deadline=? WHERE user_id=?""", (amount, borrowed_deadline, ctx.author.id))
            return await ctx.send(embed=embed)
        await self.jbot_db_global.exec_sql("""DELETE FROM game WHERE user_id=?""", (ctx.author.id,))
        embed = discord.Embed(title="게임 오버 - 왜 이런짓을...",
                              description="당신은 한강에 뛰어내렸고 그 결과 고통스럽게 사망했습니다.\n"
                                          "(게임 계정이 삭제되었습니다. 게임 기능을 사용하기 위해서는 계정을 다시 생성해주세요.)",
                              color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command(name="알바", description="알바를 통해 돈을 얻습니다.")
    @commands.cooldown(1, 60*10, commands.BucketType.user)
    async def work(self, ctx):
        money = (await self.jbot_db_global.res_sql("""SELECT money FROM game WHERE user_id=?""", (ctx.author.id,)))[0]["money"]
        to_add = random.randint(1000, 8590)
        money += to_add
        await self.jbot_db_global.exec_sql("""UPDATE game SET money=? WHERE user_id=?""", (money, ctx.author.id))
        embed = discord.Embed(title="알바 완료", description=f"알바를 통해 `{to_add}`원을 벌었습니다.\n현재 당신의 지갑에는 `{money}`원이 있습니다.", color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command(name="지갑", description="자신 또는 해당 유저의 계정을 보여줍니다.", usage="`지갑 (유저)`", aliases=["계정"])
    async def account_view(self, ctx, user: discord.User = None):
        user = user if user is not None else ctx.author
        acc = (await self.jbot_db_global.res_sql("""SELECT * FROM game WHERE user_id=?""", (user.id,)))[0]
        stock_data = await self.jbot_db_global.res_sql("""SELECT * FROM stock""")
        description = """**수치 관련 설명**
`학업`이 일정 크기 이상일 경우 `학원강사`, `과외쌤` 일을 할 수 있습니다. 학업을 올리기 위해서는 일정 금액을 지불하고 학원을 다니면 됩니다.
`힘`이 일정 크기 이상일 경우 `막노동`이 가능합니다. 힘을 키우기 위해서는 헬스장에서 일정 금액을 지불하고 헬스를 하면 됩니다.
`친절도`가 일정 크기 이상일 경우 `콜센터 직원` 일을 할 수 있습니다. 친절도를 올리기 위해서는 `학원강사`, `과외쌤` 일을 하면 됩니다.
"""
        embed = discord.Embed(title=f"{user.name}님의 계정 정보", description="참고: 현재 학업/힘/친절도 기능은 준비중입니다.", color=discord.Color.from_rgb(225, 225, 225), timestamp=ctx.message.created_at)
        embed.add_field(name="돈", value=f"`{acc['money']}`원", inline=False)
        embed.add_field(name="학업", value=str(acc["intelligent"]), inline=False)
        embed.add_field(name="힘", value=str(acc["power"]), inline=False)
        embed.add_field(name="친절도", value=str(acc["kindness"]), inline=False)
        # embed.add_field(name="현재 직업", value=str(acc["current_job"]) if bool(acc["current_job"]) else "백수", inline=False)
        embed.add_field(name="갚아야 하는 대출",
                        value=f"금액: `{acc['borrowed_money']}`원\n남은 시간: {utils.parse_second(round(float(acc['borrowed_deadline'])-time.time()))}" if bool(acc['borrowed_deadline']) else "없음",
                        inline=False)
        stock_embed = discord.Embed(title=f"{user.name}님의 주식 정보", color=discord.Color.from_rgb(225, 225, 225), timestamp=ctx.message.created_at)
        for k, v in json.loads(acc["stock"]).items():
            tgt_stock = [x for x in stock_data if x["name"] == v["name"]][0]
            stock_embed.add_field(name=v["name"]+f" (코드: {k})", value=f"개수: {v['amount']}개\n수익: {(tgt_stock['curr_price']*v['amount'])-v['bought_price']}원", inline=False)
        await utils.start_page(self.bot, ctx, lists=[embed, stock_embed], embed=True)

    @commands.command(name="대출", description="은행에서 대출을 받습니다.", usage="`대출 [돈 액수]`")
    async def borrow_money(self, ctx, amount: int):
        usr_data = (await self.jbot_db_global.res_sql("""SELECT money, borrowed_money FROM game WHERE user_id=?""", (ctx.author.id,)))[0]
        if bool(usr_data["borrowed_money"]):
            return await ctx.send("아직 갚지 않은 돈이 있습니다. 먼저 돈을 갚아주세요.")
        if amount < 1000:
            return await ctx.send("돈은 1000원 이상부터 대출받을 수 있습니다.")
        borrowed_deadline = time.time() + (60*60*72)
        random_percent = random.randint(2, 25)
        interest = round(amount / random_percent)
        conf_embed = discord.Embed(title="돈 대출",
                                   description=f"정말로 `{amount}`원을 대출할까요? (이자: `{interest}`원)\n대출한 금액은 이자를 포함해서 72시간 안에 갚아야 합니다.",
                                   color=discord.Color.from_rgb(225, 225, 225))
        msg = await ctx.send(embed=conf_embed)
        res = await utils.confirm(self.bot, ctx, msg)
        if not res:
            cancel_embed = discord.Embed(title="돈 대출", description="대출이 취소되었습니다.", color=discord.Color.red())
            return await msg.edit(embed=cancel_embed)
        await self.jbot_db_global.exec_sql("""UPDATE game SET money=?, borrowed_money=?, borrowed_deadline=? WHERE user_id=?""", (int(usr_data["money"])+amount, amount+interest, borrowed_deadline, ctx.author.id))
        ok_embed = discord.Embed(title="돈 대출", description="대출이 완료되었습니다.", color=discord.Color.green())
        await msg.edit(embed=ok_embed)

    @commands.command(name="대출갚기", description="대출한 돈을 갚습니다.")
    async def return_money(self, ctx):
        usr_data = (await self.jbot_db_global.res_sql("""SELECT money, borrowed_money FROM game WHERE user_id=?""", (ctx.author.id,)))[0]
        if not bool(usr_data["borrowed_money"]):
            return await ctx.send("갚아야 할 돈이 없습니다.")
        if int(usr_data["money"]) < int(usr_data["borrowed_money"]):
            return await ctx.send("돈이 부족합니다.")
        money = int(usr_data["money"]) - int(usr_data["borrowed_money"])
        await self.jbot_db_global.exec_sql("""UPDATE game SET money=?, borrowed_money=0, borrowed_deadline=NULL WHERE user_id=?""", (money, ctx.author.id))
        embed = discord.Embed(title="대출 갚기", description=f"대출한 돈을 모두 갚았습니다. (현재 돈: `{money}`원)", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name="헬스장", description="헬스를 해서 힘을 키웁니다.")
    async def are_you_hell_chang(self, ctx):
        menu_embed = discord.Embed(title="헬스장 가격", desciption="이모지 반응으로 선택해주세요")
        menu_embed.add_field(name="1. 기본", value="가격: `10000`원 | 힘 추가 정도: 5~10", inline=False)
        menu_embed.add_field(name="2. 트레이너 포함", value="가격: `30000`원 | 힘 추가 정도: 20~50", inline=False)
        menu_embed.add_field(name="3. 헬창이 되기", value="가격: `100000`원 | 힘 추가 정도: 50~200")
        menu_dict = {
            "1️⃣": [10000, [5, 10]],
            "2️⃣": [30000, [20, 50]],
            "3️⃣": [100000, [50, 100]]
        }
        usr_data = (await self.jbot_db_global.res_sql("""SELECT money, power FROM game WHERE user_id=?""", (ctx.author.id,)))[0]
        money = usr_data["money"]
        power = usr_data["power"]
        msg = await ctx.send(embed=menu_embed)
        for x in menu_dict.keys():
            await msg.add_reaction(x)

        def check(reaction, user):
            return user.id == ctx.author.id and reaction.message.id == msg.id and str(reaction) in menu_dict.keys()

        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)
        except asyncio.TimeoutError:
            for x in menu_dict.keys():
                await msg.remove_reaction(x, msg.author)
            return await ctx.send("시간이 만료되었습니다.", delete_after=5)

        selected = menu_dict[str(reaction)]

        for x in menu_dict.keys():
            await msg.remove_reaction(x, msg.author)

        if selected[0] > money:
            return await ctx.send("돈이 부족합니다.")
        money -= selected[0]

        working_embed = discord.Embed(title="헬스장에서 운동하는중", description="잠시만 기다려주세요...", )
        await msg.edit(embed=working_embed)
        await asyncio.sleep(5)
        fail_rate = random.randint(1, 100)
        selected_num = random.randint(*selected[1])
        if fail_rate < 30:
            power -= selected_num
            finish_embed = discord.Embed(title="운동 실패",
                                         description=f"당신을 헬스장에서 운동을 너무 무리하게 하다가 근육이 손상되었습니다."
                                                     f"힘이 `{selected_num}` 만큼 감소했습니다. (현재 힘: `{power}` | 현재 돈: `{money}`원)")
        else:
            power += selected_num
            finish_embed = discord.Embed(title="운동 완료",
                                         description=f"힘이 `{selected_num}` 만큼 증가했습니다! (현재 힘: `{power}` | 현재 돈: `{money}`원)")

        await self.jbot_db_global.exec_sql("""UPDATE game SET money=?, power=? WHERE user_id=?""", (money, power, ctx.author.id))
        await msg.edit(embed=finish_embed)

    @commands.command(name="학원", description="학원에서 공부를 합니다.")
    async def idk_academy(self, ctx):
        menu_embed = discord.Embed(title="학원 수업 리스트", desciption="이모지 반응으로 선택해주세요")
        menu_embed.add_field(name="1. 1과목 공부하기", value="가격: `100000`원 | 학업 추가 정도: 5~10", inline=False)
        menu_embed.add_field(name="2. 4과목 공부하기", value="가격: `500000`원 | 학업 추가 정도: 20~50", inline=False)
        menu_embed.add_field(name="3. 재종반 수업 듣기", value="가격: `1000000`원 | 학업 추가 정도: 50~200")
        menu_dict = {
            "1️⃣": [100000, [5, 10]],
            "2️⃣": [500000, [20, 50]],
            "3️⃣": [1000000, [50, 100]]
        }
        usr_data = (await self.jbot_db_global.res_sql("""SELECT money, intelligent FROM game WHERE user_id=?""", (ctx.author.id,)))[0]
        money = usr_data["money"]
        intelligent = usr_data["intelligent"]
        msg = await ctx.send(embed=menu_embed)
        for x in menu_dict.keys():
            await msg.add_reaction(x)

        def check(reaction, user):
            return user.id == ctx.author.id and reaction.message.id == msg.id and str(reaction) in menu_dict.keys()

        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)
        except asyncio.TimeoutError:
            for x in menu_dict.keys():
                await msg.remove_reaction(x, msg.author)
            return await ctx.send("시간이 만료되었습니다.", delete_after=5)

        selected = menu_dict[str(reaction)]

        for x in menu_dict.keys():
            await msg.remove_reaction(x, msg.author)

        if selected[0] > money:
            return await ctx.send("돈이 부족합니다.")
        money -= selected[0]

        working_embed = discord.Embed(title="학원에서 공부하는중", description="잠시만 기다려주세요...", )
        await msg.edit(embed=working_embed)
        await asyncio.sleep(5)

        fail_rate = random.randint(1, 100)
        selected_num = random.randint(*selected[1])
        if fail_rate < 30:
            intelligent -= selected
            finish_embed = discord.Embed(title="공부 실패",
                                         description=f"당신은 수업중에 너무 졸려서 수업중 졸다가 선생님께 걸려서 학원에서 퇴학되었습니다."
                                                     f"학업이 `{selected_num}` 만큼 감소했습니다. (현재 학업: `{intelligent}` | 현재 돈: `{money}`원)")
        else:
            intelligent += selected_num
            finish_embed = discord.Embed(title="공부 완료",
                                         description=f"학업이 `{selected_num}` 만큼 증가했습니다! (현재 학업: `{intelligent}` | 현재 돈: `{money}`원)")

        await self.jbot_db_global.exec_sql("""UPDATE game SET money=?, intelligent=? WHERE user_id=?""",
                                           (money, intelligent, ctx.author.id))
        await msg.edit(embed=finish_embed)

    @commands.command(name="투자", description="투자를 해서 돈을 얻거나 잃습니다.", usage="`투자 [돈 액수]`", aliases=["가즈아"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def gambling(self, ctx, to_lose_money: int):
        money = (await self.jbot_db_global.res_sql("""SELECT money FROM game WHERE user_id=?""", (ctx.author.id,)))[0]["money"]
        if to_lose_money > money:
            return await ctx.send("돈이 부족합니다.")
        can_do_list = ["비트코인", "부동산", "지인이 추천해준", "IT기업"]
        percentage = random.randint(1, 100)
        random_times = random.randint(2, 4)
        if percentage <= 30:
            money += to_lose_money * random_times
            await ctx.send(f"{random.choice(can_do_list)} 투자에 성공하였습니다. {random_times}배의 돈을 얻었습니다. (현재 돈: `{money}`)")
        else:
            money -= to_lose_money * random_times
            await ctx.send(f"{random.choice(can_do_list)} 투자에 실패하였습니다. {random_times}배의 돈을 잃었습니다. (현재 돈: `{money}`)")
        await self.jbot_db_global.exec_sql("""UPDATE game SET money=? WHERE user_id=?""", (money, ctx.author.id))

    @commands.command(name="가위바위보", description="제이봇과 가위바위보를 합니다", usage="`가위바위보 [돈 액수]`")
    async def rockpapercissor(self, ctx, amount: int):
        money = (await self.jbot_db_global.res_sql("""SELECT money FROM game WHERE user_id=?""", (ctx.author.id,)))[0]["money"]
        if amount > money:
            return await ctx.send("돈이 부족합니다.")
        base_embed = discord.Embed(title="가위바위보",
                                   description=f"이모지 반응을 10초 안에 선택해주세요! (우승하면 `{amount}`원 획득)",
                                   color=discord.Color.from_rgb(225, 225, 225))
        rpc = ['✌', '✊', '🖐']
        msg = await ctx.send(embed=base_embed)
        for x in rpc:
            await msg.add_reaction(x)
        try:
            def check(reaction, user):
                return str(reaction) in rpc and user.id == ctx.author.id and reaction.message.id == msg.id

            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=10)
        except asyncio.TimeoutError:
            return await ctx.send("시간이 지나서 자동으로 취소되었습니다.")
        finally:
            for x in rpc:
                await msg.remove_reaction(x, self.bot.user)

        user_choice = str(reaction)
        bot_choice = random.choice(rpc)

        won_embed = discord.Embed(title=f"{ctx.author.name}님 우승",
                                  description=f"{ctx.author.name}님이 저를 이기셨어요... ({user_choice} vs {bot_choice})\n(+`{amount}`원)",
                                  color=discord.Color.green())
        lose_embed = discord.Embed(title=f"제이봇 우승",
                                   description=f"제가 이겼어요! ({user_choice} vs {bot_choice})\n(-`{amount}`원)",
                                   color=discord.Color.red())
        draw_embed = discord.Embed(title=f"비겼음",
                                   description=f"이런! 비겼네요... ({user_choice} vs {bot_choice})",
                                   color=discord.Color.from_rgb(225, 225, 225))

        if (user_choice == rpc[0] and bot_choice == rpc[2]) or (user_choice == rpc[1] and bot_choice == rpc[0]) or (user_choice == rpc[2] and bot_choice == rpc[1]):
            await self.jbot_db_global.exec_sql("""UPDATE game SET money=? WHERE user_id=?""", (money + amount, ctx.author.id))
            return await msg.edit(embed=won_embed)
        elif user_choice == bot_choice:
            return await msg.edit(embed=draw_embed)
        elif (user_choice == rpc[0] and bot_choice == rpc[1]) or (user_choice == rpc[1] and bot_choice == rpc[2]) or (user_choice == rpc[2] and bot_choice == rpc[0]):
            await self.jbot_db_global.exec_sql("""UPDATE game SET money=? WHERE user_id=?""", (money - amount, ctx.author.id))
            return await msg.edit(embed=lose_embed)


def setup(bot: CustomClient):
    bot.add_cog(Game(bot))
