import discord
from discord.ext import commands
import traceback
import sys

from discord.ext.commands.errors import CommandNotFound

class BaseError(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if not hasattr(ctx.command, "on_error") and isinstance(error, CommandNotFound) is False:
            embed=discord.Embed(
                title='❌ Ha ocurido un error',
                type='rich',
                color=discord.Colour.red(),
                description = 'Favor reportar los errores a <@123968225565212674>'
            )
            if ctx.cog:
                embed.add_field(
                    name = 'Modulo',
                    value = ctx.cog.qualified_name
                )
            
            embed.add_field(
                name = "Comando",
                value = ctx.command.qualified_name
            )
            embed.add_field(
                name = "Error",
                value = f'{error.__class__.__name__}: {error}'
            )
            await ctx.send(embed=embed)
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(BaseError(bot))