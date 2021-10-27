import discord
from discord import utils
from discord.embeds import Embed
from discord.ext import commands
import aiosqlite
import datetime

import config
import utils.check

from discord.ext.commands.core import command

class BotAuditLog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.category = "Admin"
    

    """
    --- Utiles ---
    """
    async def logging_channel_id(self, guild: discord.Guild):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        try:
            await cursor.execute(f'SELECT "admin.logging" FROM "Module Channels" WHERE guild_id={guild.id}')
            channel_id = await cursor.fetchone()
            await db.close()
            if channel_id:
                return channel_id[0]
            return None

        except aiosqlite.DatabaseError:
            # If there is no channel on the table or the guild is not present, the funcionality is not set up
            # Therefore, nothing should be done.
            await db.close()
            return None            


    @commands.guild_only()
    @commands.check(utils.check.is_staff)
    @commands.group(
        name='logging',
        help='Configura el logging de acciones del servidor'
    )
    async def logging(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.logging)
            

    @commands.check(utils.check.is_staff)
    @logging.group(
        name='channel'
    )
    async def channel(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.channel)

    @commands.check(utils.check.is_staff)
    @channel.command(
        name='set'
    )
    async def channel_set(self, ctx: commands.Context, channel: discord.TextChannel):
        
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        try:
            await cursor.execute("""ALTER TABLE "Module Channels" ADD COLUMN "admin.logging" INTEGER;""")
        except aiosqlite.OperationalError:
            pass

        await cursor.execute('''INSERT INTO "Module Channels"(guild_id, 'admin.logging') VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET 'admin.logging'=?;''', [ctx.guild.id, channel.id, channel.id])
        await db.commit()
        await db.close()

        await ctx.send(f"El canal {channel.mention} ha sido configurado para recibir el log del servidor")

        
    """
    --- (Des)Baneo de usuario ---
    """
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user):
        channel_id = await self.logging_channel_id(guild)
        if channel_id is not None:
            channel: discord.TextChannel = guild.get_channel(channel_id=channel_id)
            await channel.send(f"El usuario {user.mention} ha sido baneado del servidor")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user):
        channel_id = await self.logging_channel_id(guild)
        if channel_id is not None:
            channel: discord.TextChannel = guild.get_channel(channel_id=channel_id)
            await channel.send(f"El usuario {user.mention} ha sido desbaneado del servidor")


    """
    --- Mensajes editados ---
    """
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.id != self.bot.user.id and before.content != after.content:
            channel_id = await self.logging_channel_id(before.guild)
            if channel_id is not None:
                channel: discord.TextChannel = before.guild.get_channel(channel_id=channel_id)
                user: discord.Member = before.author
                embed=Embed(
                    title=f'Mensaje Editado',
                    color=discord.Colour.teal(),
                    url=after.jump_url
                )
                embed.add_field(
                    name='Autor',
                    value=user.mention,
                )
                embed.add_field(
                    name='Canal',
                    value=before.channel.mention
                )
                embed.add_field(
                    name='Antes',
                    value=before.content,
                    inline=False
                )
                embed.add_field(
                    name='Después',
                    value=after.content,
                    inline=False
                )
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author != self.bot.user:
            channel_id = await self.logging_channel_id(message.guild)
            if channel_id is not None:
                channel: discord.TextChannel = message.guild.get_channel(channel_id=channel_id)
                user: discord.Member = message.author
                embed=Embed(
                    title=f'Mensaje Eliminado',
                    color=discord.Colour.dark_red()
                )
                embed.add_field(
                    name='Autor',
                    value=user.mention,
                )
                embed.add_field(
                    name='Canal',
                    value=message.channel.mention
                )
                embed.add_field(
                    name='Mensaje',
                    value=(message.content if message.content else "Vacio"),
                    inline=False
                )
                await channel.send(embed=embed)

    """
    --- Invitaciones ---
    """
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        channel_id = await self.logging_channel_id(invite.guild)
        if channel_id is not None:
            channel: discord.TextChannel = invite.guild.get_channel(channel_id=channel_id)
            embed = discord.Embed(
                title="Invitación creada"
            )
            embed.add_field(
                name="Creado por",
                value=invite.inviter.mention,
                inline=True
            )
            embed.add_field(
                name="Cantidad de usos máximo",
                value=str(invite.max_uses),
                inline=True
            )

            dias, segundos = divmod(invite.max_age, 86400)
            embed.add_field(
                name="Límite de tiempo",
                value=str(datetime.timedelta(seconds=segundos, days=dias)) if invite.max_age > 0 else "Ninguno",
                inline=True
            )
            embed.add_field(
                name='Enlace',
                value=invite.url,
                inline=True
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        channel_id = await self.logging_channel_id(invite.guild)
        if channel_id is not None:
            channel: discord.TextChannel = invite.guild.get_channel(channel_id=channel_id)
            embed = discord.Embed(
                title="Invitación Eliminada",
                color=discord.Colour.red()
            )
            embed.add_field(
                name='Enlace',
                value=invite.url,
                inline=True
            )
            await channel.send(embed=embed)

    """
    --- Entrada y salida de usuarios
    """
    datetime_string_format="%d/%m/%Y %H:%M:%S"
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel_id = await self.logging_channel_id(member.guild)
        if channel_id is not None:
            channel: discord.TextChannel = member.guild.get_channel(channel_id=channel_id)
            embed: discord.Embed = discord.Embed(
                title='Nuevo Usuario',
                type='rich',
                color=discord.Colour.green()
            )
            embed.add_field(
                name='Usuario',
                value=member.mention
            )
            embed.add_field(
                name='creado el',
                value=member.created_at.strftime(self.datetime_string_format) + " UTC"
            )
            embed.add_field(
                name='se unió el',
                value=member.joined_at.strftime(self.datetime_string_format) + " UTC"
            )
            edad_usuario: datetime.timedelta = (datetime.datetime.utcnow() - member.created_at)
            minutos, segundos = divmod(edad_usuario.seconds, 60)
            horas, minutos = divmod(minutos, 60)
            embed.add_field(
                name='Edad de la cuenta',
                value=f'{edad_usuario.days} días, {horas} horas, {minutos} minutos, {segundos} segundos.'
            )
            embed.set_thumbnail(
                url=member.avatar_url
            )

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel_id = await self.logging_channel_id(member.guild)
        if channel_id is not None:
            channel: discord.TextChannel = member.guild.get_channel(channel_id=channel_id)
            embed: discord.Embed = discord.Embed(
                title='Un usario ha dejado el servidor',
                type='rich',
                color=discord.Colour.red()
            )
            embed.add_field(
                name='Usuario',
                value=member.mention
            )
            embed.add_field(
                name='creado el',
                value=member.created_at.strftime(self.datetime_string_format) + " UTC"
            )
            embed.add_field(
                name='se unió el',
                value=member.joined_at.strftime(self.datetime_string_format) + " UTC"
            )
            estadia_usuario: datetime.timedelta = (datetime.datetime.utcnow() - member.joined_at)
            minutos, segundos = divmod(estadia_usuario.seconds, 60)
            horas, minutos = divmod(minutos, 60)
            embed.add_field(
                name='Estadía de la cuenta',
                value=f'{estadia_usuario.days} días, {horas} horas, {minutos} minutos, {segundos} segundos.'
            )
            embed.set_thumbnail(
                url=member.avatar_url
            )

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        nick_change = before.nick != after.nick
        role_change = before.roles != after.roles
        if (nick_change or role_change):
            channel_id = await self.logging_channel_id(after.guild)
            if channel_id is not None:
                channel: discord.TextChannel = before.guild.get_channel(channel_id=channel_id)
                embed: discord.Embed = discord.Embed(
                    title='Un miembro del servidor fue modificado',
                    type='rich',
                    color=discord.Colour.teal()
                )
                embed.add_field(
                    name='Usuario',
                    value=before.mention
                )
                if nick_change:
                    embed.add_field(
                        name='Nick Anterior',
                        value=(f'"{before.nick}"' if before.nick else "Ninguno"),
                        inline=False
                    )
                    embed.add_field(
                        name='Nick actual',
                        value=(f'"{after.nick}"' if after.nick else "Ninguno")
                    )
                if role_change:
                    embed.add_field(
                        name='Roles anteriores',
                        value=f'{", ".join([r.name for r in before.roles])}',
                        inline=False
                    )
                    embed.add_field(
                        name='Roles actuales',
                        value=f'{", ".join([r.name for r in after.roles])}'
                    )
                embed.set_thumbnail(
                    url=before.avatar_url
                )

                await channel.send(embed=embed)
        

def setup(bot):
    bot.add_cog(BotAuditLog(bot))