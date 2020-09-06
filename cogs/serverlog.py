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
from discord.ext import commands
from modules import admin
from modules.cilent import CustomClient


class ServerLog(commands.Cog):
    def __init__(self, bot: CustomClient):
        self.bot = bot
        self.jbot_db_global = bot.jbot_db_global

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if str(message.content) is None:
            return
        embed = discord.Embed(title='메시지 삭제됨',
                              description=message.channel.mention + f" (`#{message.channel.name}`)",
                              colour=discord.Color.red())
        embed.set_author(name=message.author.display_name + f" ({message.author})", icon_url=message.author.avatar_url)
        embed.add_field(name="메시지 내용", value=message.content if message.content else "(메시지 내용 없음)")
        await admin.send_to_log(self.jbot_db_global, message.guild, embed)

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
        await admin.send_to_log(self.jbot_db_global, guild, embed)

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
        await admin.send_to_log(self.jbot_db_global, after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(title='채널 삭제됨', colour=discord.Color.red())
        embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon_url)
        embed.add_field(name='채널 이름', value=f'`#{channel.name}`', inline=False)
        await admin.send_to_log(self.jbot_db_global, channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(title='채널 생성됨', colour=discord.Color.green())
        embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon_url)
        embed.add_field(name='채널 이름', value=channel.mention + f' (`#{channel.name}`)', inline=False)
        await admin.send_to_log(self.jbot_db_global, channel.guild, embed)

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
            # 너무 도배 가능성이 있다고 판단됨
            return # embed.add_field(name="기타 변경됨", value="변경된 내용을 찾을 수 없습니다. (채널 주제, NSFW, 슬로우모드 등)")
        await admin.send_to_log(self.jbot_db_global, after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        embed = discord.Embed(title='서버 업데이트됨',
                              colour=discord.Color.lighter_grey())
        embed.set_author(name=after.name, icon_url=after.icon_url)
        count = 0
        not_for_this = False #emojis, text_channels, members, roles, member_count
        else_list = [] #banner, icon
        if before.emojis != after.emojis or before.text_channels != after.text_channels or before.members != after.members or before.roles != after.roles or before.member_count != after.member_count:
            not_for_this = True
        if before.banner != after.banner:
            else_list.append("서버 배너")
        if before.icon != after.icon:
            else_list.append("서버 아이콘")
        if before.name != after.name:
            embed.add_field(name='서버 이름', value=f'{before.name} -> {after.name}', inline=False)
            count += 1
        if before.region != after.region:
            embed.add_field(name='서버 지역', value=f'{before.region} -> {after.region}', inline=False)
            count += 1
        if before.verification_level != after.verification_level:
            embed.add_field(name='서버 보안 수준', value=f'{before.verification_level} -> {after.verification_level}', inline=False)
            count += 1
        if before.owner != after.owner:
            embed.add_field(name='서버 소유자', value=f'{before.owner.display_name} -> {after.owner.mention}', inline=False)
            count += 1
        if before.system_channel != after.system_channel:
            if before.system_channel is None:
                before_sys = "없음"
            else:
                before_sys = before.system_channel.mention
            if after.system_channel is None:
                after_sys = "없음"
            else:
                after_sys = after.system_channel.mention
            embed.add_field(name="시스템 메시지 채널", value=f"{before_sys} -> {after_sys}", inline=False)
            count += 1
        if before.premium_tier != after.premium_tier:
            embed.add_field(name="니트로 부스트 레벨", value=f"{before.premium_tier}레벨 -> {after.premium_tier}레벨", inline=False)
            count += 1
        if before.premium_subscription_count != after.premium_subscription_count:
            embed.add_field(name="니트로 부스트 수", value=f"{before.premium_subscription_count}개 -> {after.premium_subscription_count}개", inline=False)
            count += 1
        if bool(else_list):
            embed.add_field(name="기타 변경됨", value=', '.join(else_list), inline=False)
            count += 1
        if count == 0:
            if not_for_this is True:
                return
            # 너무 도배 가능성이 있다고 판단됨
            return # embed.add_field(name="기타 변경됨", value="변경된 내용을 찾을 수 없습니다. (봇이 감지할 수 없는 부분이 변경된 경우)", inline=False)
        await admin.send_to_log(self.jbot_db_global, after, embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(title='역할 생성됨', colour=discord.Color.green())
        embed.set_author(name=role.guild.name, icon_url=role.guild.icon_url)
        embed.add_field(name='역할', value=f'{role.mention} (`@{role.name}`)', inline=False)
        await admin.send_to_log(self.jbot_db_global, role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        embed = discord.Embed(title='역할 업데이트됨', description=after.mention, colour=discord.Color.lighter_grey())
        embed.set_author(name=after.guild.name, icon_url=after.guild.icon_url)
        count = 0
        if before.color != after.color:
            count += 1
            embed.add_field(name="역할 색상", value=f"{before.color} -> {after.color}", inline=False)
        before_perms = dict(before.permissions)
        after_perms = dict(after.permissions)
        changed_dict = {}
        if before_perms != after_perms:
            count += 1
            for x in before_perms.keys():
                if before_perms[x] != after_perms[x]:
                    changed_dict[x] = "예 -> 아니요" if before_perms[x] else "아니요 -> 예"
            res = '\n'.join([f"{k}: {v}" for k, v in changed_dict.items()])
            embed.add_field(name="변경된 권한", value=res, inline=False)
        if count == 0:
            return
        await admin.send_to_log(self.jbot_db_global, after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = discord.Embed(title='역할 삭제됨', colour=discord.Color.red())
        embed.set_author(name=role.guild.name, icon_url=role.guild.icon_url)
        embed.add_field(name='역할 이름', value=f'`@{role.name}`', inline=False)
        await admin.send_to_log(self.jbot_db_global, role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        before_emoji = list(before)
        after_emoji = list(after)
        deleted = []
        added = []
        embed = discord.Embed(title="서버 이모지 업데이트됨", colour=discord.Color.lighter_grey())
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        for x in before_emoji:
            if x not in after_emoji:
                deleted.append(x)
        if bool(deleted):
            embed.add_field(name="제거된 이모지", value=', '.join([x.name for x in deleted]))
        for x in after_emoji:
            if x not in before_emoji:
                added.append(x)
        if bool(added):
            embed.add_field(name="추가된 이모지", value=', '.join([x.name for x in added]))
        await admin.send_to_log(self.jbot_db_global, guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(title="맴버 차단 해제됨", description=str(user), colour=discord.Colour.green())
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        embed.set_thumbnail(url=user.avatar_url)
        await admin.send_to_log(self.jbot_db_global, guild, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(title="맴버 차단됨", description=str(user), colour=discord.Colour.red())
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        embed.set_thumbnail(url=user.avatar_url)
        await admin.send_to_log(self.jbot_db_global, guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        embed = discord.Embed(name="맴버 정보 업데이트됨", description=after.mention + f" ({after})", colour=discord.Color.lighter_grey())
        embed.set_author(name=after.guild.name, icon_url=after.guild.icon_url)
        before_roles = before.roles
        after_roles = after.roles
        deleted = []
        added = []
        count = 0
        if before.display_name != after.display_name:
            embed.add_field(name="닉네임 변경됨", value=f"{before.display_name} -> {after.display_name}", inline=False)
            count += 1
        if before_roles != after_roles:
            count += 1
            for x in before_roles:
                if x not in after_roles:
                    deleted.append(x)
            for x in after_roles:
                if x not in before_roles:
                    added.append(x)
            if bool(added):
                embed.add_field(name="추가된 역할", value=', '.join([x.mention for x in added]), inline=False)
            if bool(deleted):
                embed.add_field(name="제거된 역할", value=', '.join([x.mention for x in deleted]), inline=False)
        if count == 0:
            return
        await admin.send_to_log(self.jbot_db_global, after.guild, embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title="새로운 맴버", description=member.mention + f" ({member})", colour=discord.Color.green())
        embed.set_author(name=member.guild.name, icon_url=member.guild.icon_url)
        embed.set_thumbnail(url=member.avatar_url)
        await admin.send_to_log(self.jbot_db_global, member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title="맴버 퇴장", description=str(member), colour=discord.Color.red())
        embed.set_author(name=member.guild.name, icon_url=member.guild.icon_url)
        embed.set_thumbnail(url=member.avatar_url)
        await admin.send_to_log(self.jbot_db_global, member.guild, embed)

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        embed = discord.Embed(title="모든 반응 제거됨", description=f"[해당 메시지로 바로가기]({msg.jump_url})", color=discord.Colour.red())
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        await admin.send_to_log(self.jbot_db_global, guild, embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        embed = discord.Embed(title="새 초대코드 생성됨", colour=discord.Color.green())
        embed.set_author(name=invite.guild.name, icon_url=invite.guild.icon_url)
        embed.add_field(name="초대코드를 생성한 사람", value=invite.inviter.mention + f" (`{invite.inviter}`)", inline=False)
        embed.add_field(name="초대코드", value=invite.url)
        await admin.send_to_log(self.jbot_db_global, invite.guild, embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        embed = discord.Embed(title="초대코드 삭제됨", colour=discord.Color.red())
        embed.set_author(name=invite.guild.name, icon_url=invite.guild.icon_url)
        embed.add_field(name="삭제된 초대코드", value=invite.url)
        await admin.send_to_log(self.jbot_db_global, invite.guild, embed)

    @commands.command(name="로그테스트")
    async def log_test(self, ctx):
        embed = discord.Embed(title="로그 테스트", description="로그가 정상적으로 보내졌네요!",
                              color=discord.Colour.from_rgb(225, 225, 225))
        await admin.send_to_log(self.jbot_db_global, ctx.guild, embed)


def setup(bot):
    bot.add_cog(ServerLog(bot))
