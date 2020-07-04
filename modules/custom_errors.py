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


class IllegalString(commands.CommandError):
    def __init__(self, banned: list = None):
        self.banned = banned
