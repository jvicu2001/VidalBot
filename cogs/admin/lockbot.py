import discord
from discord.ext import commands
import aiosqlite
import config
import json
import utils.database
import utils.check

class LockBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category = "Admin"


    
    @commands.guild_only()
    @commands.check(utils.check.is_staff)
    @commands.command(
        name='lockbot',
        aliases=['lock'],
        brief='Bloquea un canal',
        help='Bloquéa la ejecución de comandos en este canal'
    )
    async def lock(self, ctx: commands.Context, channel: discord.TextChannel):
        data: dict = await utils.database.get_guild_config(ctx.guild)
        channels = set(data.get('locked_channels', []))
        channels.add(channel.id)
        data.update({'locked_channels': list(channels)})
        await utils.database.set_guild_config(ctx.guild, data)
        await ctx.send('¡Canal bloqueado!')

    @commands.guild_only()
    @commands.check(utils.check.is_staff)
    @commands.command(
        name='unlockbot',
        aliases=['unlock'],
        brief='Desbloquea un canal',
        help='Desbloquéa la ejecución de comandos en este canal'
    )
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel):
        data: dict = await utils.database.get_guild_config(ctx.guild)
        try:
            channels = data.get('locked_channels', [])
            channels.remove(channel.id)
            data.update({'locked_channels': channels})
            await utils.database.set_guild_config(ctx.guild, data)
            await ctx.send('¡Canal desbloqueado!')
        
        except ValueError:
            await ctx.send('¡Este canal no está bloqueado!')
        
    @commands.guild_only()
    @commands.check(utils.check.is_staff)
    @commands.command(
        name='islocked',
        aliases=['locked'],
        brief='Revisa si el canal está bloquedo',
        help='Revisa si la ejecución de comandos está bloqueada en este canal'
    )
    async def islocked(self, ctx: commands.Context, channel: discord.TextChannel = None):
        data: dict = await utils.database.get_guild_config(ctx.guild)
        if channel is None:
            locked = ctx.channel.id in data.get('locked_channels', [])
            await ctx.send(f'Este canal {"no " if locked is False else ""}está bloqueado.')
        else:
            locked = channel.id in data.get('locked_channels', [])
            await ctx.send(f'El canal {channel.mention} {"no " if locked is False else ""}está bloqueado.')
        
        


def setup(bot):
    bot.add_cog(LockBot(bot))
