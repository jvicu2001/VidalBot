import config
import discord
from discord.errors import Forbidden, HTTPException
from discord.ext import commands
from discord.ext.commands.errors import MemberNotFound, UserNotFound


class UserManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category = "Admin"


    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.command(
        name='ban',
        aliases=['realban'],
        help='Banea a un usuario del servidor'
    )
    async def UserBan(self, ctx: commands.Context, user: discord.User, *reason: str):
        try:
            reason = " ".join(reason)
            dm = user.dm_channel
            if dm is None:
                dm = await user.create_dm()
            if len(reason.strip()) > 0:
                await dm.send(f'Has sido baneado de {ctx.guild.name}.\nRazón: {reason}')
            else:
                await dm.send(f'Has sido baneado de {ctx.guild.name}.')
        except HTTPException:
            await ctx.send('No se pudo notificar al usuario de su baneo.')
        await ctx.guild.ban(user=user, reason=reason)
        await ctx.send(f"El usuario {user.display_name} ha sido baneado del servidor.")
    

    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.command(
        name='unban',
        help='Desbanea a un usuario del servidor'
    )
    async def UserUnban(self, ctx: commands.Context, user: discord.User):
        try:
            await ctx.guild.unban(user=user)
            await ctx.send(f"El usuario {user.mention} ha sido desbaneado del servidor.")
        except (Forbidden, HTTPException, AttributeError):
            await ctx.send(f"Hubo un error al desbanear el usuario.")

    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.command(
        name='kick',
        help='Expulsa a un usuario del servidor'
    )
    async def UserKick(self, ctx: commands.Context, user: discord.User, *reason: str):
        if (await ctx.guild.fetch_member(user.id)):
            try:
                reason = " ".join(reason)
                dm = user.dm_channel
                if dm is None:
                    dm = await user.create_dm()
                if len(reason.strip()) > 0:
                    await dm.send(f'Has sido kickeado de {ctx.guild.name}.\nRazón: {reason}')
                else:
                    await dm.send(f'Has sido kickeado de {ctx.guild.name}.')
            except HTTPException:
                await ctx.send('No se pudo notificar al usuario de su expulsión.')
            await ctx.guild.kick(user.id, reason=reason)
            await ctx.send(f"El usuario {user.display_name} ha sido kickeado del servidor.")
        else:
            await ctx.send(f"El usuario {user.display_name} no se encuentra en el servidor.")

    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.command(
        name='multiban',
        help='Banea a múltiples usuarios del servidor'
    )
    async def MultiBan(self, ctx: commands.Context, *users):
        for _user in users:
            try:
                user = await commands.UserConverter().convert(ctx, _user)
                await self.UserBan(ctx, user)
            except MemberNotFound:
                await ctx.send(f'Usuario {_user} no encontrado.')

    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.command(
        name='multikick',
        help='Kickea a múltiples usuarios del servidor'
    )
    async def MultiKick(self, ctx: commands.Context, *users):
        for _user in users:
            try:
                user = await commands.UserConverter().convert(ctx, _user)
                await self.UserKick(ctx, user)
            except UserNotFound:
                await ctx.send(f'Usuario {_user} no encontrado.')


def setup(bot):
    bot.add_cog(UserManagement(bot))
