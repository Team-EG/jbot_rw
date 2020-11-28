import discord
import json
from aiohttp import web
from aiohttp.web import Request
from aiohttp.web import Response
from discord.ext import commands
from modules.cilent import CustomClient


class API(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        self.site: web.TCPSite
        self.bot.loop.create_task(self.run_api())

    async def run_api(self):
        @self.routes.get("/api/guild_setup/{guild_id}")
        async def get_guild_setup(request: Request):
            guild_id = int(request.match_info["guild_id"])
            guild_setup = await self.bot.jbot_db_global.res_sql("""SELECT * FROM guild_setup WHERE guild_id=?""", (guild_id,))
            if not bool(guild_setup):
                return web.json_response({"description": "Guild Not Found. Check guild_id."}, status=404)
            return web.json_response(guild_setup[0])

        @self.routes.get("/api/guild/{guild_id}")
        async def get_guild_info(request: Request):
            guild_id = int(request.match_info["guild_id"])
            tgt_guild: discord.Guild = self.bot.get_guild(guild_id)
            tgt_guild = tgt_guild if tgt_guild else await self.bot.fetch_guild(guild_id)
            if tgt_guild is None:
                return web.json_response({"description": "Guild Not Found."}, status=404)
            roles = tgt_guild.roles if tgt_guild.roles else await tgt_guild.fetch_roles()
            guild_data = {"name": tgt_guild.name,
                          "text_channels": [{x.id: x.name} for x in tgt_guild.channels if isinstance(x, discord.TextChannel)],
                          "members": [{x.id: [str(x), x.nick if x.nick else x.name]} for x in tgt_guild.members],
                          "roles": [{x.id: x.name} for x in roles]}
            return web.json_response(guild_data)

        self.app.add_routes(self.routes)
        runner = web.AppRunner(self.app)
        await runner.setup()
        self.site = web.TCPSite(runner, '0.0.0.0', 9002)
        await self.bot.wait_until_ready()
        await self.site.start()

    def cog_unload(self):
        self.bot.loop.create_task(self.site.stop())


def setup(bot):
    bot.add_cog(API(bot))
