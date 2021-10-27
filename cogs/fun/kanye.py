import discord
from discord.ext import commands
import asyncio
import aiohttp

class KanyeQuotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category = "Fun"

    api_url = 'https://api.kanye.rest'

    @commands.command(
        name='kanye',
        aliases=["kanye_quote", "kanye_rest"],
        help='Entrega frases dichas por Kanye West (en inglés)\nSe obtienen desde kanye.rest',
        brief='Frases de Kanye West'
        )
    async def kanye(self, ctx):
        async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url) as resp:
                    if resp.status == 200:
                        quote = await resp.json()
                        embed = discord.Embed(
                            title = quote['quote'],
                            type = 'rich',
                            color = 0x100029,
                            description="   - Kanye West"
                            )
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f'Hubo un error\nError {resp.status}')
        

def setup(bot):
    bot.add_cog(KanyeQuotes(bot))