import discord
from discord.ext import commands
import aiohttp
from io import BytesIO

from PIL import Image
from discord.ext.commands import context

class ImageManipulation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.category = "Fun"

    @commands.command(
        name='weezer',
        aliases=['weezerme'],
        help='Convierte un avatar en una portada de Weezer'
    )
    async def weezer(self, ctx: commands.Context, user: discord.Member = None):
        async with ctx.channel.typing():
            if user is None:
                avatar_url = str(ctx.author.avatar_url_as(format='png'))
            else:
                avatar_url = str(user.avatar_url_as(format='png'))
            
            weezer_url = 'https://i.imgur.com/RQEUK1w.png'

            image = Image.new('RGBA', (512, 512))

            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    if resp.status == 200:
                        avatar_bytes = await resp.content.read()
                        avatar = Image.open(BytesIO(avatar_bytes), 'r').resize((512, 512), Image.ANTIALIAS)

            async with aiohttp.ClientSession() as session:
                async with session.get(weezer_url) as resp:
                    if resp.status == 200:
                        weezer_bytes = await resp.content.read()
                        weezer = Image.open(BytesIO(weezer_bytes), 'r').resize((512, 512), Image.ANTIALIAS)

            image.paste(avatar, (0, 0))
            image.alpha_composite(weezer, (0, 0))

            final = BytesIO()
            image.save(final, format='PNG')
            final = BytesIO(final.getvalue())
            await ctx.send(
                f'{("You" if user == None or user == ctx.author else user.display_name)} just got weezerd.',
                file=discord.File(final, filename='weezerd.png')
            )


def setup(bot):
    bot.add_cog(ImageManipulation(bot))