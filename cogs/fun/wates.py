import random
import sqlite3

import config
import discord
from discord.ext import commands
from discord.ext.commands.errors import MemberNotFound


class Wate(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        db = sqlite3.connect(config.database)
        db.execute('''CREATE TABLE IF NOT EXISTS MemeBan(
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            bans INTEGER,
            PRIMARY KEY(guild_id, user_id)
        );''')
        db.commit()
        db.close()
    
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(
        name='wate'
    )
    async def wate(self, ctx: commands.Context, *users):
        valid_users = []
        for user in users:
            try:
                member = await commands.MemberConverter().convert(ctx, user)
                valid_users.append(member)
            except MemberNotFound:
                pass

        for user in valid_users:
            if user.id == ctx.author.id:
                await ctx.send('Cómo te vas a pegar un wate a tí mismo a ver.')
                continue
            if random.choice([True, False]):
                db = sqlite3.connect(config.database)
                cursor = db.cursor()
                
                cursor.execute('''SELECT bans FROM "MemeBan" WHERE guild_id=? AND user_id=?;''', (ctx.guild.id, user.id))
                wates = cursor.fetchone()
                if wates == None:
                    wates = 0
                else:
                    wates = wates[0]
                new_wates = wates+1
                cursor.execute('''INSERT INTO "MemeBan"(guild_id, user_id, bans) VALUES (?, ?, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET bans=?;''', [ctx.guild.id, user.id, new_wates, new_wates])
                await ctx.send(f'Se le proporcionó un wate a {user.display_name}. Ahora tiene {new_wates} wate(s)')
                db.commit()
                db.close()
            else:
                await ctx.send(f'{user.display_name} evadió el wate 🏃‍♂️')

    @wate.error
    async def wate_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.send('Has pegados muchos wates. Espera un rato.')
        else:
            await ctx.send(f'Se ha producido un error: ```\n{error}\n```')

    @commands.guild_only()
    @commands.command(
        name='wates',
        help='Ver cuantos wates se le han pegado a alguien'
    )
    async def wates(self, ctx: commands.Context, user: discord.Member):
        db = sqlite3.connect(config.database)
        cursor = db.cursor()
        cursor.execute('''SELECT bans FROM "MemeBan" WHERE guild_id=? AND user_id=?;''', (ctx.guild.id, user.id))
        bans = cursor.fetchone()
        if bans == None:
            await ctx.send(f'Al usuario {user.display_name} nunca se le ha dado un wate.')
        else:
            await ctx.send(f'El usuario {user.display_name} ha recibido {bans[0]} wate(s).')
        db.close()

    @wates.error
    async def wates_error(self, ctx: commands.Context, error):
        await ctx.send(f'Ha ocurrido un error\n```\n{error}\n```')
    


    @commands.guild_only()
    @commands.command(
        name='waterank',
        help='Visualiza el ranking de wates.'
    )
    async def waterank(self, ctx: commands.Context):
        db = sqlite3.connect(config.database)
        cursor = db.cursor()
        cursor.execute('''SELECT user_id, bans FROM "MemeBan" WHERE guild_id=? ORDER BY bans DESC LIMIT 5;''', (ctx.guild.id,))
        waterank = cursor.fetchall()
        if len(waterank) == 0:
            await ctx.send('Nunca se le ha dado un wate a alguien acá')
        else:
            embed: discord.Embed= discord.Embed(
                title='Rank de Wates',
                type='rich',
                description="\n".join([f'{await self.bot.fetch_user(user_id=n[0])}: {n[1]}' for n in waterank])
            )
            await ctx.send(embed=embed)
        db.close()

    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.command(
        name='setwates',
        aliases=['setwate'],
        help='Establece directamente la cantidad de wates de algún usuario'
    )
    async def setwates(self, ctx: commands.Context, user: discord.Member, cantidad: int):
        db = sqlite3.connect(config.database)
        cursor = db.cursor()
        cursor.execute('''INSERT INTO "MemeBan"(guild_id, user_id, bans) VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET bans=?;''', [ctx.guild.id, user.id, cantidad, cantidad])
        db.commit()
        db.close()
        return await ctx.send(f'Ahora {user.display_name} tiene {cantidad} wates a su cuenta.')
            



    
            



def setup(bot):
    bot.add_cog(Wate(bot))
