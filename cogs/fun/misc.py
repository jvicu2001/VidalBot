import random

import discord
from discord.ext import commands
from typing import Union


class MiscCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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
        help='Obtén la imagen de un emoji custom.'
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

def setup(bot):
    bot.add_cog(MiscCommands(bot))
