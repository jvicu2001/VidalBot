import json
import time

import discord
from discord.ext import commands


class AdminMisc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command(
        name='prefix',
        help='Visualiza y (solo administrador) cambia el prefijo del bot en este servidor'
    )
    async def prefix(self, ctx: commands.Context, new_prefix: str = None):
        if not new_prefix:
            await ctx.send(f'El prefijo en este servidor es: {(await self.bot.get_prefix(ctx.message))[2]}')
        else:
            if ctx.author.guild_permissions.administrator:
                with open('prefixes.json', 'r') as f:
                    prefixes: dict = json.load(f)
                    f.close()

                prefixes.update({f'{ctx.guild.id}': new_prefix})
                with open('prefixes.json', 'w') as f:
                    json.dump(prefixes, f)
                    f.close()

                await ctx.send(f'Prefijo cambiado a: {new_prefix}')
    
    @commands.command(
        name='message'
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def message(self, ctx: commands.Context, channel: discord.TextChannel, *text):
        text = " ".join(text)
        print(channel)
        if ctx.guild:

            if ctx.guild.get_channel(channel.id):
                await channel.send(text)


    @commands.command(
        name='dm'
    )
    @commands.guild_only()
    @commands.is_owner()
    async def dm(self, ctx: commands.Context, user: discord.Member, *text):
        if len(text) > 0 and await ctx.guild.fetch_member(user.id):
            text = " ".join(text)
            dm = user.dm_channel
            if dm is None:
                dm = await user.create_dm()
            await dm.send(text)
            await ctx.send(f"¡Mensaje enviado a {user.display_name}!")

    @commands.command(
        name='ping',
        help='Muestra la latencia entre el bot y los servidores de Discord.'
    )
    async def ping(self, ctx: commands.Context):
        embed: discord.Embed= discord.Embed(
            title='¡Pong! 🏓',
            color = discord.Colour.dark_green()
        )
        embed.add_field(
            name='♥ Heartbeat',
            value=f'{round(self.bot.latency*1000,2)}ms',
            inline=False
        )
        before = time.monotonic()
        message: discord.Message = await ctx.send(embed=embed)
        message_delay =(time.monotonic() - before)
        embed.add_field(
            name='📩 Mensaje',
            value=f'{round(message_delay * 1000, 2)} ms'
        )
        embed.color = discord.Colour.green()
        await message.edit(embed=embed)

    


def setup(bot):
    bot.add_cog(AdminMisc(bot))
