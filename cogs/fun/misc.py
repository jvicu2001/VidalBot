import random

import discord
from discord.ext import commands
from typing import Union

from discord.ext.commands.errors import BadUnionArgument


class MiscCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category = "Fun"
        self.rng = random.Random()

    @commands.command(
        name='rate',
        help="Califica un usuario o texto"
    )
    @commands.guild_only()
    async def rate(self, ctx: commands.Context, *arg):
        arg = " ".join(arg).strip()
        if arg == "" or arg is None:
            seed = ctx.author.id
            text = ctx.author.display_name
        else:

            try:
                user: discord.Member = await commands.MemberConverter().convert(ctx, argument=arg)
                seed = user.id
                text = user.display_name
            except (commands.MemberNotFound, commands.BadArgument):
                seed = arg
                text = arg
        
        self.rng.seed(seed)
        rating = self.rng.random() * 100
        return await ctx.send(
            'A {} le doy un {:.2f} de 100'.format(text, rating))
        
    @commands.command(
        name='emoji',
        aliases=['emote'],
        help='Obtén la imagen de un emoji.'
    )
    async def emoji(self, ctx: commands.Context, emoji: Union[discord.Emoji, discord.PartialEmoji]):
        embed = discord.Embed(
            title= f'Mostrando el emoji :{emoji.name}:',
            type='rich',
            url=emoji.url
        )
        if isinstance(emoji, discord.Emoji):
            embed.set_footer(
                text = f'Emoji del servidor "{emoji.guild.name}"',
                icon_url = emoji.guild.icon_url_as(format='jpg',size=64)
        )
        embed.set_image(url=emoji.url)
        await ctx.send(embed=embed)

    @emoji.error
    async def emoji_error(self, ctx: commands.Context, error):
        if isinstance(error, BadUnionArgument):
            embed = discord.Embed(
                title = '¡No se pudo encontrar el emoji!',
                type = 'rich',
                color = discord.Colour.dark_red(),
                description = 'Si lo que buscas es la imagen de un emoji entre los incluidos con Discord, \
puedes hacerlo siguiendo los siguientes pasos (Solo disponibles en Escritorio y Navegador)'
            )
            embed.set_image(url='https://i.imgur.com/asd1RID.gif')
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'Ha ocurrido un error:\n```{error.__class__.__name__}: {error}\n```')


        

def setup(bot):
    bot.add_cog(MiscCommands(bot))
