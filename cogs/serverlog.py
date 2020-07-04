import discord
from discord.ext import commands
from modules import admin


class ServerLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if str(message.content) is None:
            return
        embed = discord.Embed(title='메시지 삭제됨',
                              description=message.channel.mention + f" (`#{message.channel.name}`)",
                              colour=discord.Color.red())
        embed.set_author(name=message.author.display_name + f" ({message.author})", icon_url=message.author.avatar_url)
        embed.add_field(name="메시지 내용", value=message.content)
        await admin.send_to_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        if len(payload.message_ids) == 1:
            return
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        embed = discord.Embed(title='메시지 대량 삭제됨',
                              description=channel.mention + f" (`#{channel.name}`)",
                              colour=discord.Color.red())
        embed.add_field(name='삭제된 메시지 개수', value=str(len(payload.message_ids)), inline=False)
        await admin.send_to_log(guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content == after.content:
            return
        embed = discord.Embed(title='메시지 수정됨',
                              description=after.channel.mention + f" (`#{after.channel.name}`)",
                              colour=discord.Color.lighter_grey())
        embed.set_author(name=after.author.display_name + f" ({after.author})", icon_url=after.author.avatar_url)
        if bool(before.content) is False or bool(after.content) is False:
            return
        embed.add_field(name='기존 내용', value=f'{before.content}')
        embed.add_field(name='수정된 내용', value=f'{after.content}', inline=False)
        await admin.send_to_log(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(title='채널 삭제됨', colour=discord.Color.red())
        embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon_url)
        embed.add_field(name='채널 이름', value=f'`#{channel.name}`', inline=False)
        await admin.send_to_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(title='채널 생성됨', colour=discord.Color.green())
        embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon_url)
        embed.add_field(name='채널 이름', value=channel.mention + f' (`#{channel.name}`)', inline=False)
        await admin.send_to_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        embed = discord.Embed(title='채널 업데이트됨', description=after.mention + f" (`#{after.name}`)",
                              colour=discord.Color.lighter_grey())
        embed.set_author(name=after.guild.name, icon_url=after.guild.icon_url)
        count = 0
        if not before.name == after.name:
            embed.add_field(name='채널 이름', value=f'{before.name} -> {after.name}', inline=False)
            count += 1
        if not before.category == after.category:
            embed.add_field(name='카테고리 변경', value=f'{before.category} -> {after.category}', inline=False)
            count += 1
        before_overwrites = before.overwrites
        after_overwrites = after.overwrites
        # added_roles_dict = {} <- leaving for later
        added_roles = []
        deleted_roles = []
        changed_roles_dict = {}
        for k, v in after_overwrites.items():
            if k not in before_overwrites.keys():
                added_roles.append(k)
                # added_roles_dict[k] = [x[0] for x in list(v) if x[1] is True] <- leaving for later
        for k, v in before_overwrites.items():
            if k in after_overwrites.keys() and dict(v) == dict(after_overwrites[k]):
                continue
            elif k in after_overwrites.keys() and dict(v) != dict(after_overwrites[k]):
                after_dict = dict(after_overwrites[k])
                changed_perms = []
                for k2, v2 in after_dict.items():
                    if v2 != dict(v)[k2]:
                        changed_perms.append(k2)
                changed_roles_dict[k] = changed_perms
            else:
                deleted_roles.append(k)
        if len(added_roles) != 0:
            embed.add_field(name="추가된 역할", value=', '.join([x.mention for x in added_roles]), inline=False)
            count += 1
        if len(deleted_roles) != 0:
            embed.add_field(name="제거된 역할", value=', '.join([x.mention for x in deleted_roles]), inline=False)
            count += 1
        for k, v in changed_roles_dict.items():
            embed.add_field(name=f"{k} 역할 권한 변경됨", value=f"{k.mention} 역할의 변경된 권한들: \n`{', '.join(v)}`", inline=False)
            count += 1
        if count == 0:
            embed.add_field(name="기타 변경됨", value="변경된 내용을 찾을 수 없습니다. (채널 주제, NSFW, 슬로우모드 등)")
        await admin.send_to_log(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        pass

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(title='역할 생성됨', colour=discord.Color.green())
        embed.set_author(name=role.guild.name, icon_url=role.guild.icon_url)
        embed.add_field(name='역할', value=f'{role.mention} (`@{role.name}`)', inline=False)
        await admin.send_to_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = discord.Embed(title='역할 삭제됨', colour=discord.Color.red())
        embed.set_author(name=role.guild.name, icon_url=role.guild.icon_url)
        embed.add_field(name='역할 이름', value=f'`@{role.name}`', inline=False)
        await admin.send_to_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        pass

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        pass

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        pass

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        embed = discord.Embed(title="새 초대코드 생성됨", colour=discord.Color.green())
        embed.set_author(name=invite.guild.name, icon_url=invite.guild.icon_url)
        embed.add_field(name="초대코드를 생성한 사람", value=invite.inviter.mention + f" (`{invite.inviter}`)", inline=False)
        embed.add_field(name="초대코드", value=invite.url)
        await admin.send_to_log(invite.guild, embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        embed = discord.Embed(title="초대코드 삭제됨", colour=discord.Color.red())
        embed.set_author(name=invite.guild.name, icon_url=invite.guild.icon_url)
        embed.add_field(name="삭제된 초대코드", value=invite.url)
        await admin.send_to_log(invite.guild, embed)

    @commands.command(name="로그테스트")
    async def log_test(self, ctx):
        embed = discord.Embed(title="로그 테스트", description="로그가 정상적으로 보내졌네요!",
                              color=discord.Colour.from_rgb(225, 225, 225))
        await admin.send_to_log(ctx.guild, embed)


def setup(bot):
    bot.add_cog(ServerLog(bot))
