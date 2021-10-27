import discord
from discord.ext import commands
import asyncio
import aiohttp
from discord.ext.commands.core import command
import utils.database
import json

class EntryRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category = "Admin"
        
    role = None
    
    entry_message = None

class StaffRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category = 'Admin'

    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.group(
        name='staffroles',
        brief='Maneja los roles de moderación',
        help='Maneja los roles que el bot considerará como moderación'
    )
    async def staffroles(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            data: dict = await utils.database.get_guild_config(ctx.guild)
            roles = [commands.RoleConverter().convert(ctx, r) for r in data.get('staffroles', [])]
            if len(roles) > 0:
                return await ctx.send(f'Roles configurados: {", ".join(roles)}')
            else:
                return await ctx.send('No hay roles configurados.')


    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @staffroles.command(
        name='set',
        aliases=['add'],
        help='Añade un rol a la lista de staff considerada por el bot'
    )
    async def staffroles_set(self, ctx: commands.Context, role: discord.Role):
        data: dict = await utils.database.get_guild_config(ctx.guild)
        roles = set(data.get('staffroles', []))
        roles.add(role.id)
        data.update({'staffroles': list(roles)})
        await utils.database.set_guild_config(ctx.guild, data)
        await ctx.send(f'Rol {role.name} añadido.')

    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @staffroles.command(
        name='remove',
        help='Remuevo un rol de la lista de roles de staff.'
    )
    async def staffroles_remove(self, ctx: commands.Context, role: discord.Role):
        data: dict = await utils.database.get_guild_config(ctx.guild)
        roles = data.get('staffroles', []).remove(role.id)
        data.update({'staffroles': roles})
        await utils.database.set_guild_config(ctx.guild, data)
        await ctx.send(f'Rol {role.name} removido.')
    
    

def setup(bot):
    bot.add_cog(EntryRole(bot))
    bot.add_cog(StaffRoles(bot))