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
import asyncio
import websockets
import random
import time
from discord.ext import commands
from discord.ext import tasks
from modules.cilent import CustomClient


class Tasks(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.jbot_db_global = bot.jbot_db_global
        self.presence_cycle.start()
        self.stock_price.start()
        self.cancel = False

    def cog_unload(self):
        self.cancel = True
        self.presence_cycle.cancel()
        self.stock_price.cancel()

    @tasks.loop()
    async def presence_cycle(self):
        # 팁: 이렇게 하면 오류로 무한루프가 멈춰도 다시 작동합니다
        while True:
            if self.cancel:
                break
            act_list = ["'제이봇 도움'이라고 말해보세요!",
                        f"{len(self.bot.guilds)}개 서버에서 작동",
                        f"{len(list(self.bot.get_all_members()))} 유저들과 함께"]
            for x in act_list:
                try:
                    await self.bot.change_presence(activity=discord.Game(str(x)))
                    await asyncio.sleep(5)
                except (asyncio.streams.IncompleteReadError, discord.ConnectionClosed, websockets.exceptions.ConnectionClosedError):
                    print("Failed Changing. Retrying...")
                    await asyncio.sleep(5)
                    await self.bot.change_presence(activity=discord.Game(str(x)))
                    await asyncio.sleep(5)

    @tasks.loop()
    async def stock_price(self):
        while True:
            if self.cancel:
                break
            stock = await self.jbot_db_global.res_sql("""SELECT * FROM stock""")
            for x in stock:
                if len(stock) == 0:
                    break
                random_price = random.randint(0, 60)
                random_percentage = random.randint(1, 100)
                random_multipler = random.choice([1, 1, 1, 1, random.randint(2, 3)])
                score = x["score"]
                curr_price = x["curr_price"]
                curr_history = x["history"].split(",")
                if random_percentage < score: # 가격 하락
                    curr_price -= random_price * random_multipler ** 2
                    score -= random.randint(1, 10)
                    curr_history.append(str(curr_price))
                else: # 가격 상승
                    curr_price += random_price * random_multipler
                    score += random.randint(1, 10)
                    curr_history.append(str(curr_price))
                if len(curr_history) > 20:
                    del curr_history[0]
                await self.jbot_db_global.exec_sql("""UPDATE stock SET curr_price=?, score=?, history=? WHERE name=?""",
                                                   (curr_price, score, ','.join(curr_history), x["name"]))
            self.bot.last_stock_change = round(time.time())
            await asyncio.sleep(60*5)

    @presence_cycle.before_loop
    async def before_loop_start(self):
        await self.bot.wait_until_ready()

    @stock_price.before_loop
    async def before_loop_start(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Tasks(bot))
