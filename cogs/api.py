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
        self.auths = {}
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        self.site: web.TCPSite
        self.bot.loop.create_task(self.run_api())

    async def run_api(self):
        @self.routes.get("/api/guild_setup/{guild_id}")
        async def get_guild_setup(request: Request):
            auth_failed = self.check_auth(request)
            if auth_failed:
                return auth_failed
            guild_id = int(request.match_info["guild_id"])
            guild_setup = await self.bot.jbot_db_global.res_sql("""SELECT * FROM guild_setup WHERE guild_id=?""", (guild_id,))
            if not bool(guild_setup):
                return web.json_response({"description": "Guild Not Found. Check guild_id."}, status=404)
            return web.json_response(guild_setup[0])

        @self.routes.get("/api/guild/{guild_id}")
        async def get_guild_info(request: Request):
            auth_failed = self.check_auth(request)
            if auth_failed:
                return auth_failed
            guild_id = int(request.match_info["guild_id"])
            tgt_guild: discord.Guild = self.bot.get_guild(guild_id)
            #tgt_guild = tgt_guild if tgt_guild else await self.bot.fetch_guild(guild_id)
            if tgt_guild is None:
                return web.json_response({"description": "Guild Not Found."}, status=404)
            roles = tgt_guild.roles if tgt_guild.roles else await tgt_guild.fetch_roles()
            guild_data = {"name": tgt_guild.name,
                          "text_channels": [{x.id: x.name} for x in tgt_guild.channels if isinstance(x, discord.TextChannel)],
                          "members": [{x.id: [str(x), x.nick if x.nick else x.name]} for x in tgt_guild.members],
                          "roles": [{x.id: x.name} for x in roles]}
            return web.json_response(guild_data)

        @self.routes.get("/api/level/{guild_id}")
        async def get_level_info(request: Request):
            guild_id = int(request.match_info["guild_id"])
            guild_setting = (await self.bot.jbot_db_global.res_sql("""SELECT use_level FROM guild_setup WHERE guild_id=?""", (guild_id,)))[0]
            if not bool(guild_setting["use_level"]):
                return web.json_response({"description": "Level is not enabled."}, status=403)
            level = await self.bot.jbot_db_level.res_sql(f"""SELECT * FROM "{guild_id}_level" ORDER BY exp DESC""")
            to_return = level.copy()
            for x in range(len(level)):
                user_id = level[x]["user_id"]
                #user = self.bot.get_user(user_id)
                guild = self.bot.get_guild(guild_id)
                member = guild.get_member(user_id)
                if member is None:
                    to_return[x]["name"] = None
                    to_return[x]["nick"] = None
                    to_return[x]["avatar_url"] = None
                    continue
                to_return[x]["name"] = str(member)
                to_return[x]["nick"] = str(member.nick if member.nick else member.name)
                to_return[x]["avatar_url"] = str(member.avatar_url)
            return web.json_response(to_return)

        @self.routes.post("/api/login")
        async def login_api(request: Request):
            body = await request.json()
            if "user_id" not in body.keys():
                return web.json_response({"description": "Incorrect Body."}, status=400)
            user = self.bot.get_user(int(body["user_id"]))
            if user is None:
                return web.json_response({"description": "User Not Found."}, status=404)
            # user = user if user else await self.bot.fetch_user(int(body["user_id"]))
            resp = {"user_id": int(user.id),
                    "name": str(user.name),
                    "discriminator": str(user.discriminator),
                    "avatar_url": str(user.avatar_url)}
            return web.json_response(resp)

        @self.routes.post("/api/update/{guild_id}")
        async def update_settings(request: Request):
            auth_failed = await self.check_auth(request)
            if isinstance(auth_failed, Response):
                return auth_failed
            guild_id = int(request.match_info["guild_id"])
            available_guilds = [x["guild_id"] for x in await self.bot.jbot_db_global.res_sql("""SELECT guild_id FROM guild_setup""")]
            if guild_id not in available_guilds:
                return web.json_response({"description": "Guild Not Found."}, status=404)
            body = await request.json()
            usable_keys = ["prefix", "talk_prefix", "log_channel", "announcement", "welcome_channel",
                           "starboard_channel", "greet", "bye", "greetpm", "use_level", "use_antispam",
                           "use_globaldata", "mute_role", "to_give_roles"]
            for x in body.keys():
                if x not in usable_keys:
                    return web.json_response({"description": f"Incorrect Setting Key. ({x})"}, status=400)
            to_update = ', '.join([f"{x}=?" for x in body.keys()])
            await self.bot.jbot_db_global.exec_sql(f"UPDATE guild_setup SET {to_update} WHERE guild_id=?", (*body.values(), guild_id))
            guild_setup = await self.bot.jbot_db_global.res_sql("""SELECT * FROM guild_setup WHERE guild_id=?""", (guild_id,))
            return web.json_response(guild_setup[0])

        self.app.add_routes(self.routes)
        runner = web.AppRunner(self.app)
        await runner.setup()
        self.site = web.TCPSite(runner, '0.0.0.0', 9002)
        await self.bot.wait_until_ready()
        await self.site.start()

    async def check_auth(self, request: Request):
        header = request.headers
        if "Authorization" not in header.keys():
            return web.json_response({"description": "Requires Authorization"}, status=403)
        return False

    def cog_unload(self):
        self.bot.loop.create_task(self.site.stop())


def setup(bot):
    bot.add_cog(API(bot))
