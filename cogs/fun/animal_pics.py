import discord
from discord.ext import commands
import asyncio
import aiohttp
import json


class RandomAnimals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def dict_dive(self, path, jsondoc):
        value = jsondoc
        for level in path:
            value = value[level]
        return value
    
    # Generador de Embeds, toma campos predefinidos para armar un embed de animalitos estandar
    async def random_base(self, ctx, api_url, header_text, image_field_path, favicon_url, footer_text):
        async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    if resp.status == 200:
                        animal = await resp.json()
                        embed = discord.Embed(
                            title = header_text,
                            type = 'rich',
                            color = 0xffd859
                            )
                        embed.set_image(url = self.dict_dive(image_field_path, animal))
                        embed.set_footer(
                            text=footer_text,
                            icon_url = favicon_url
                            )
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f'Hubo un error :c\nError {resp.status}')
    
    
    @commands.command(
                    name='cat',
                    aliases=['gato', 'gatito'],
                    help = "Muestra la imagen de un gato obtenida desde random.cat",
                    brief="Imágenes de gatos"
                    )
    async def cat(self, ctx):
        await self.random_base(
            ctx, 
            api_url = 'https://aws.random.cat/meow',
            header_text = 'Aquí te va un gatito',
            image_field_path = ['file'],
            favicon_url = 'https://purr.objects-us-east-1.dream.io/static/ico/favicon-96x96.png',
            footer_text = 'Gatito auspiciado por random.cat'
            )

    
    @commands.command(
                    name='fox',
                    aliases=['zorro', 'zorrito'],
                    help="Muestra la imagen de un zorro obtenida desde randomfox.ca",
                    brief="Imágenes de zorros"
                    )
    async def fox(self, ctx):
        await self.random_base(
            ctx, 
            api_url = 'https://randomfox.ca/floof/',
            header_text = 'Aquí te va un zorrito',
            image_field_path = ['image'],
            favicon_url = 'https://randomfox.ca/logo.png',
            footer_text = 'Zorrito auspiciado por randomfox.ca'
            )
            
    @commands.command(
                    name='dog',
                    aliases=['perro', 'perrito'],
                    help="Muestra la imagen de un perro obtenida desde random.dog",
                    brief="Imágenes de perros"
                    )
    async def dog(self, ctx):
        await self.random_base(
            ctx, 
            api_url = 'https://random.dog/woof.json',
            header_text = 'Aquí te va un perrito',
            image_field_path = ['url'],
            favicon_url = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/google/274/dog_1f415.png',
            footer_text = 'Perrito auspiciado por random.dog'
            )
            
    @commands.command(
                    name='shiba',
                    aliases=['shibe', 'shibainu'],
                    help="Muestra la imagen de un Shiba Inu obtenida desde shibe.online",
                    brief="Imágenes de Shiba Inus"
                    )
    async def shiba(self, ctx):
        await self.random_base(
            ctx, 
            api_url = 'http://shibe.online/api/shibes',
            header_text = 'Aquí te va un shiba',
            image_field_path = [0],
            favicon_url = 'https://assets.stickpng.com/images/5845e770fb0b0755fa99d7f4.png',
            footer_text = 'Shiba Inu auspiciado por shibe.online'
            )
            
    @commands.command(
                    name='bunny', 
                    aliases=['conejo', 'conejito'],
                    help="Muestra la imagen de un conejo obtenida desde bunnies.io",
                    brief="Imágenes de conejos"
                    )
    async def bunny(self, ctx):
        await self.random_base(
            ctx, 
            api_url = 'https://api.bunnies.io/v2/loop/random/?media=gif,png',
            header_text = 'Aquí te va un conejito',
            image_field_path = ['media', 'gif'],
            favicon_url = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/google/274/rabbit-face_1f430.png',
            footer_text = 'Conejito auspiciado por bunnies.io'
            )
            
    @commands.command(
                    name='duck', 
                    aliases=['pato', 'patito'],
                    help="Muestra la imagen de un pato obtenida desde random-d.uk",
                    brief="Imágenes de patos"
                    )
    async def duck(self, ctx):
        await self.random_base(
            ctx, 
            api_url = 'https://random-d.uk/api/v2/random',
            header_text = 'Aquí te va un patito',
            image_field_path = ['url'],
            favicon_url = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/google/274/duck_1f986.png',
            footer_text = 'Patito auspiciado por random-d.uk'
            )

        
def setup(bot):
    bot.add_cog(RandomAnimals(bot))