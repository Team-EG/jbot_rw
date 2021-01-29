"""
    jbot_rw
    Copyright (C) 2020-2021 Team EG

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
import ssl
import aiohttp
import aiohttp_cors
from aiohttp import web
from aiohttp.web import Request
from aiohttp.web import Response
from discord.ext import commands
from modules import jbot_db
from modules.cilent import CustomClient


class API(commands.Cog):
    discord_api = "https://discord.com/api/v6"

    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        self.site: web.TCPSite
        self.cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(allow_credentials=True,
                                              expose_headers="*",
                                              allow_headers="*",)
        })
        self.bot.loop.create_task(self.run_api())

    async def run_api(self):
        column = jbot_db.set_column({"name": "token", "type": "TEXT", "default": False},
                                    {"name": "user_id", "type": "INTEGER", "default": False})
        await self.bot.jbot_db_memory.exec_sql(f"""CREATE TABLE IF NOT EXISTS cache ( {column} )""")

        @self.routes.get("/api/guild_setup/{guild_id}")
        async def get_guild_setup(request: Request):
            auth_failed = await self.check_auth(request)
            if isinstance(auth_failed, Response):
                return auth_failed
            guild_id = int(request.match_info["guild_id"])
            guild_setup = await self.bot.jbot_db_global.res_sql("""SELECT * FROM guild_setup WHERE guild_id=?""", (guild_id,))
            if not bool(guild_setup):
                return web.json_response({"description": "Guild Not Found. Check guild_id."}, status=404)
            tgt_guild: discord.Guild = self.bot.get_guild(guild_id)
            user = tgt_guild.get_member(auth_failed)
            if not user.guild_permissions.administrator or user.id != tgt_guild.owner.id:
                return web.json_response({"description": "You don't have permission."}, status=403)
            to_return = guild_setup[0]
            to_return["to_give_roles"] = json.loads(to_return["to_give_roles"])
            to_return["warn"] = json.loads(to_return["warn"])
            return web.json_response(guild_setup[0])

        @self.routes.get("/api/guild/{guild_id}")
        async def get_guild_info(request: Request):
            auth_failed = await self.check_auth(request)
            if isinstance(auth_failed, Response):
                return auth_failed
            guild_id = int(request.match_info["guild_id"])
            tgt_guild: discord.Guild = self.bot.get_guild(guild_id)
            if tgt_guild is None:
                return web.json_response({"description": "Guild Not Found."}, status=404)
            user = tgt_guild.get_member(auth_failed)
            if not user.guild_permissions.administrator or user.id != tgt_guild.owner.id:
                return web.json_response({"description": "You don't have permission."}, status=403)
            roles = tgt_guild.roles if tgt_guild.roles else await tgt_guild.fetch_roles()
            guild_data = {"name": tgt_guild.name,
                          "text_channels": [{x.id: x.name} for x in tgt_guild.channels if isinstance(x, discord.TextChannel)],
                          "members": [{x.id: [str(x), x.nick if x.nick else x.name]} for x in tgt_guild.members],
                          "roles": [{x.id: x.name} for x in roles]}
            return web.json_response(guild_data)
            
        @self.routes.get("/api/user-guilds/{user_id}")
        async def get_user_guild_info(request: Request):
            user_id = int(request.match_info["user_id"])
            tgt_user: discord.User = self.bot.get_user(user_id)
            guild_list = []
            for x in self.bot.guilds:
                if user_id in [u.id for u in x.members]:
                    guild_list.append(x)
            if not tgt_user or not guild_list:
                return web.json_response({"description": "User Not Found."}, status=404)
            return web.json_response([{"id": int(x.id),
                                       "name": str(x.name),
                                       "icon_url": str(x.icon_url),
                                       "has_perm": bool(x.get_member(user_id).guild_permissions.administrator)} for x in guild_list])

        @self.routes.get("/api/level/{guild_id}")
        async def get_level_info(request: Request):
            guild_id = int(request.match_info["guild_id"])
            guild_setting = await self.bot.jbot_db_global.res_sql("""SELECT use_level FROM guild_setup WHERE guild_id=?""", (guild_id,))
            if not guild_setting:
                return web.json_response({"description": "Guild Not Found"}, status=404)
            if not bool(guild_setting[0]["use_level"]):
                return web.json_response({"description": "Level Not Enabled."}, status=403)
            level = await self.bot.jbot_db_level.res_sql(f"""SELECT * FROM "{guild_id}_level" ORDER BY exp DESC""")
            to_return = level.copy()
            for x in range(len(level)):
                user_id = level[x]["user_id"]
                #user = self.bot.get_user(user_id)
                guild = self.bot.get_guild(guild_id)
                member = guild.get_member(user_id)
                member = member if member else self.bot.get_user(user_id)
                if member is None:
                    to_return[x]["name"] = None
                    to_return[x]["nick"] = None
                    to_return[x]["avatar_url"] = None
                    continue
                to_return[x]["name"] = str(member)
                to_return[x]["nick"] = str(member.nick if hasattr(member, "nick") and member.nick else member.name)
                to_return[x]["avatar_url"] = str(member.avatar_url_as(format="webp", size=128)) #avatar_url_as(size=128)
            guild_data: discord.Guild = self.bot.get_guild(guild_id)
            return web.json_response({"guild_name": str(guild_data) if guild_data else None,
                                      "guild_member_count": int(guild_data.member_count) if guild_data else None,
                                      "guild_profile": str(guild_data.icon_url_as(format="webp", size=128)) if guild_data else None,
                                      "levels": to_return})

        @self.routes.get("/api/playlist/{user_id}")
        async def get_playlist(request: Request):
            user_id = int(request.match_info["user_id"])
            playlist = await self.bot.jbot_db_global.res_sql("""SELECT * FROM playlist WHERE user_id=?""", (user_id,))
            if not bool(playlist):
                return web.json_response({"description": "Playlist Not Found. Check user_id."}, status=404)
            return web.json_response(playlist)

        @self.routes.get("/api/warns/{guild_id}")
        async def get_warns(request: Request):
            guild_id = int(request.match_info["guild_id"])
            warn_exist = await self.bot.jbot_db_warns.res_sql("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f"{guild_id}_warns",), return_raw=True)
            if not bool(len(warn_exist)):
                return web.json_response({"description": "No warns found."}, status=404)
            warn_list = await self.bot.jbot_db_warns.res_sql(f"""SELECT * FROM "{guild_id}_warns";""")
            if not bool(warn_list):
                return web.json_response({"description": "No warns found."}, status=404)
            to_return = warn_list.copy()
            tgt_guild: discord.Guild = self.bot.get_guild(guild_id)
            for x in range(len(warn_list)):
                user_id = warn_list[x]["user_id"]
                member = tgt_guild.get_member(user_id)
                member = member if member else self.bot.get_user(user_id)
                admin_id = warn_list[x]["issued_by"]
                admin = tgt_guild.get_member(admin_id)
                admin = admin if admin else self.bot.get_user(admin_id)
                to_return[x]["tgt"] = {}
                to_return[x]["admin"] = {}
                if member is None:
                    to_return[x]["tgt"]["name"] = None
                    to_return[x]["tgt"]["nick"] = None
                    to_return[x]["tgt"]["avatar_url"] = None
                else:
                    to_return[x]["tgt"]["name"] = str(member)
                    to_return[x]["tgt"]["nick"] = str(member.nick if hasattr(member, "nick") and member.nick else member.name)
                    to_return[x]["tgt"]["avatar_url"] = str(member.avatar_url)
                if admin is None:
                    to_return[x]["admin"]["name"] = None
                    to_return[x]["admin"]["nick"] = None
                    to_return[x]["admin"]["avatar_url"] = None
                else:
                    to_return[x]["admin"]["name"] = str(admin)
                    to_return[x]["admin"]["nick"] = str(admin.nick if hasattr(admin, "nick") and admin.nick else admin.name)
                    to_return[x]["admin"]["avatar_url"] = str(admin.avatar_url)
            return web.json_response(to_return)

        @self.routes.post("/api/login")
        async def login_api(request: Request):
            return web.json_response({"description": "Deprecated."}, status=404)

            '''
            body = await request.json()
            if "token" not in body.keys():
                return web.json_response({"description": "Incorrect Body."}, status=400)
            cache = await self.bot.jbot_db_memory.res_sql("""SELECT token FROM cache WHERE discord=?""", (body['token'],))
            if cache:
                resp = {"token": cache[0]["token"]}
                return web.json_response(resp)
            header = {"Authorization": f"Bearer {body['token']}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.discord_api + "/users/@me", headers=header) as resp:
                    if resp.status != 200:
                        return web.json_response({"description": "Invalid User Token."}, status=403)
                    user = await resp.json()
            if user is None:
                return web.json_response({"description": "User Not Found."}, status=404)
            user_id = user["id"]
            token = jwt.encode({"user_id": user_id, "time": round(time.time())}, 'secret', algorithm='HS256').decode('utf-8')
            await self.bot.jbot_db_memory.exec_sql("""INSERT INTO cache VALUES (?, ?, ?)""", (body['token'], token, user_id))
            resp = {"token": token}
            return web.json_response(resp)
            '''

        @self.routes.post("/api/update/{guild_id}")
        async def update_settings(request: Request):
            auth_failed = await self.check_auth(request)
            if isinstance(auth_failed, Response):
                return auth_failed
            guild_id = int(request.match_info["guild_id"])
            tgt_guild: discord.Guild = self.bot.get_guild(guild_id)
            user = tgt_guild.get_member(auth_failed)
            if not user.guild_permissions.administrator or user.id != tgt_guild.owner.id:
                return web.json_response({"description": "You don't have permission."}, status=403)
            available_guilds = [x["guild_id"] for x in await self.bot.jbot_db_global.res_sql("""SELECT guild_id FROM guild_setup""")]
            if guild_id not in available_guilds:
                return web.json_response({"description": "Guild Not Found."}, status=404)
            body = await request.json()
            usable_keys = ["prefix", "talk_prefix", "log_channel", "announcement", "welcome_channel",
                           "starboard_channel", "greet", "bye", "greetpm", "use_level", "use_antispam",
                           "use_globaldata", "mute_role", "to_give_roles", "warn"]
            for x in body.keys():
                if x not in usable_keys:
                    return web.json_response({"description": f"Incorrect Setting Key. ({x})"}, status=400)
            to_update = ', '.join([f"{x}=?" for x in body.keys()])
            await self.bot.jbot_db_global.exec_sql(f"UPDATE guild_setup SET {to_update} WHERE guild_id=?", (*body.values(), guild_id))
            guild_setup = await self.bot.jbot_db_global.res_sql("""SELECT * FROM guild_setup WHERE guild_id=?""", (guild_id,))
            return web.json_response(guild_setup[0])

        self.app.add_routes(self.routes)
        [self.cors.add(x) for x in self.app.router.routes()]
        runner = web.AppRunner(self.app)
        await runner.setup()
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain("jebserver_ssl/cert.pem", "jebserver_ssl/privkey.pem")
        self.site = web.TCPSite(runner, '0.0.0.0', 9002, ssl_context=ssl_context)
        await self.bot.wait_until_ready()
        await self.site.start()

    async def check_auth(self, request: Request):
        header = request.headers
        if "Authorization" not in header.keys():
            return web.json_response({"description": "Requires Authorization"}, status=400)
        cache = await self.bot.jbot_db_memory.res_sql("""SELECT user_id FROM cache WHERE token=?""", (header['Authorization'],))
        if not cache:
            try_login = await self.request_to_discord(header['Authorization'])
            if isinstance(try_login, Response):
                return try_login
            cache = [{"user_id": try_login}]
        return int(cache[0]["user_id"])

    async def request_to_discord(self, token):
        cache = await self.bot.jbot_db_memory.res_sql("""SELECT token FROM cache WHERE discord=?""", (token,))
        if cache:
            resp = {"token": cache[0]["token"]}
            return web.json_response(resp)
        header = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession() as session:
            # 나중에 클라세션 생성 안해도 되는 방법을 찾아야 될듯
            async with session.get(self.discord_api + "/users/@me", headers=header) as resp:
                if resp.status == 429:
                    return web.json_response({"description", "We are rate limited. Please try again later."}, status=429)
                elif resp.status != 200:
                    return web.json_response({"description": "Invalid User Token."}, status=403)
                user = await resp.json()
        if not user:
            return web.json_response({"description": "User Not Found."}, status=404)
        user_id = user["id"]
        does_exist = await self.bot.jbot_db_memory.res_sql("""SELECT * FROM cache WHERE user_id=?""", (user_id,))
        if does_exist:
            await self.bot.jbot_db_memory.exec_sql("""UPDATE cache SET token=? WHERE user_id=?""", (token, user_id))
        else:
            await self.bot.jbot_db_memory.exec_sql("""INSERT INTO cache VALUES (?, ?)""", (token, user_id))
        return user_id

    def cog_unload(self):
        self.bot.loop.create_task(self.site.stop())


def setup(bot):
    bot.add_cog(API(bot))
