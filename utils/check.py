import utils.database
from discord.ext import commands
import json

async def is_staff(ctx: commands.Context):
    if ctx.guild:
        data: dict = await utils.database.get_guild_config(ctx.guild)
        if data:
            roles = data.get('staffroles', [])
            if len(set(roles).intersection([r.id for r in ctx.author.roles])) > 0:
                return True
            
    return False