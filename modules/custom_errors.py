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
from discord.ext import commands


class NotWhitelisted(commands.CommandError):
    pass


class NotGuildOwner(commands.CommandError):
    pass


class NotAdmin(commands.CommandError):
    pass


class NoYDLRes(commands.CommandError):
    pass


class ConnectionTimeout(commands.CommandError):
    pass


class FailedFinding(commands.CommandError):
    pass


class IgnoreThis(commands.CommandError):
    pass


class NotEnabled(commands.CommandError):
    def __init__(self, not_enabled):
        self.not_enabled = not_enabled


class IllegalString(commands.CommandError):
    def __init__(self, banned: list = None):
        self.banned = banned
