import asyncio
import datetime
import json
from os import name
import aiosqlite

import config
import discord
from discord.ext import commands, tasks


class AutoSlowmode(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.category = "Admin"
        
        self.init_db.start()
        self.check_message_volume.start()

    @tasks.loop(minutes=2, count=1)
    async def init_db(self):
        db = await aiosqlite.connect(config.database)
        try:
            await db.execute('''
            ALTER TABLE "Module Channels" ADD COLUMN "admin.autoslowmode" TEXT
            ''')
        except aiosqlite.DatabaseError:
            pass
        await db.commit()
        await db.close()

    # Row factory for accessing columns values by their name
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


    @tasks.loop(seconds=15.0)
    async def check_message_volume(self):
        db = await aiosqlite.connect(config.database)
        db.row_factory = self.dict_factory
        cursor = await db.cursor()
        await cursor.execute('''SELECT * FROM "Module Channels" WHERE "admin.autoslowmode" NOTNULL;''')
        servers = await cursor.fetchall()
        for server in servers:
            # guild_id = server['guild_id']
            # guild_name = self.bot.get_guild(guild_id)
            # print(guild_id, guild_name)
            server_data = json.loads(server['admin.autoslowmode'])
            analytics_channel: discord.TextChannel = await self.bot.fetch_channel(server_data['analytics_channel'])
            channels = server_data['channels']
            desired_rate = server_data['max_rate']

            rates = []
            for channel_id in channels:
                channel: discord.TextChannel = self.bot.get_channel(channel_id)
                if channel:
                    message_section = channel.history(limit=60)
                    last_slowmode = channel.slowmode_delay
                    actual_time = datetime.datetime.utcnow()
                    msg_time: datetime.datetime
                    msg_counter = 0
                    async for message in message_section:
                        msg_counter += 1
                        msg_time = message.created_at
                        diff = (actual_time - msg_time).seconds
                        if diff >= 30:
                            break
                    density = msg_counter/diff

                    rates.append(f'{channel.mention}: {round(density, 2)} msg/s. Slowmode actual: {last_slowmode}s')

                    with open(f'autoslowmode_log/{channel_id}.csv', 'a') as f:
                        f.write(f'{int(datetime.datetime.utcnow().timestamp())}, {round(density, 2)}, {last_slowmode}\n')

                    # print(f'{guild_name} #{channel.name} message volume = {density} msg/s')

            if analytics_channel and len(rates) > 0:
                await analytics_channel.send(
                    "Tasa de mensajes en canales monitoreados:\n{}".format("\n".join(rates)),
                    delete_after=120
                    )
        
        await db.close()

        

    @commands.has_permissions(manage_channels=True)
    @commands.group(
        name='autoslowmode',
        help='''Configura los canales manejados por autoslowmode
        AutoSlowmode limita el volumen de mensajes que recibe un canal ajustando automáticamente el cooldown para enviar \
otro mensaje.
        
        Uso: .autoslowmode <set | setlog | unset> <channel>
             .autoslowmode <unsetlog>''',
        brief='Configura AutoSlowmode'
    )
    async def autoslowmode(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help('autoslowmode')

    @autoslowmode.command(
        name='set',
        help='Habilita un canal para que sea manejado por AutoSlowmode'
    )
    async def autoslowmode_enable(self, ctx:commands.Context, channel:discord.TextChannel):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        await cursor.execute('SELECT "admin.autoslowmode" FROM "Module Channels" WHERE guild_id=?;', [ctx.guild.id])
        channels_json = await cursor.fetchone()
        if channels_json:
            channels = json.loads(channels_json[0])
        else:
            channels = json.loads('{"channels":[], "analytics_channel":null, "max_rate" :0.5}')
        
        if channel.id in channels['channels']:
            await ctx.send("Canal ya está registrado")
        else:
            channels['channels'] = set(channels['channels'])
            channels['channels'].add(channel.id)
            channels['channels'] = list(channels['channels'])
            channels_json = json.dumps(channels)
            await cursor.execute('''INSERT INTO "Module Channels"(guild_id, 'admin.autoslowmode') VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET 'admin.autoslowmode'=?;''', (ctx.guild.id, channels_json, channels_json))
            await db.commit()

            await ctx.send(f'El canal {channel.mention} se ha registado.')

        
        await db.close()
    
    @autoslowmode.command(
        name='unset',
        help='Deshabilita un canal manejado por AutoSlowmode'
    )
    async def autoslowmode_disable(self, ctx:commands.Context, channel:discord.TextChannel):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        await cursor.execute('SELECT "admin.autoslowmode" FROM "Module Channels" WHERE guild_id=?;', [ctx.guild.id])
        channels_json = await cursor.fetchone()
        channels_json = channels_json[0]

        if channels_json:
            channels = json.loads(channels_json)
            
        else:
            channels = json.loads('{"channels":[], "analytics_channel":null, max_rate:0.5}')
        

        if channel.id in channels['channels']:
            channels['channels'].remove(channel.id)
            channels_json = json.dumps(channels)
            await cursor.execute('''INSERT INTO "Module Channels"(guild_id, 'admin.autoslowmode') VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET 'admin.autoslowmode'=?;''', (ctx.guild.id, channels_json, channels_json))
            await db.commit()
            
            await ctx.send(f"El canal {channel.mention} se ha deshabilitado.")

        else:
            await ctx.send(f'El canal {channel.mention} no está registrado.')

        
        await db.close()
    
    @autoslowmode.command(
        name='setlog',
        help='Habilita un canal para reportar datos de AutoSlowmode'
    )
    async def autoslowmode_setlog(self, ctx:commands.Context, channel:discord.TextChannel):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        await cursor.execute('SELECT "admin.autoslowmode" FROM "Module Channels" WHERE guild_id=?;', [ctx.guild.id])
        channels_json = await cursor.fetchone()
        channels_json = channels_json[0]

        if channels_json:
            channels = json.loads(channels_json)

        else:
            channels = json.loads('{"channels":[], "analytics_channel":null, "max_rate":0.5}')
        

        if channels['analytics_channel'] is channel.id:
            await ctx.send("Este canal ya está registrado")

        else:
            channels['analytics_channel'] = channel.id
            channels_json = json.dumps(channels)
            await cursor.execute('''INSERT INTO "Module Channels"(guild_id, 'admin.autoslowmode') VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET 'admin.autoslowmode'=?;''', (ctx.guild.id, channels_json, channels_json))
            await db.commit()

            await ctx.send(f'El canal {channel.mention} se ha registado.')


        await db.close()
        

    @autoslowmode.command(
        name='unsetlog',
        help='Deshabilita el canal que reporta datos de AutoSlowmode'
    )
    async def autoslowmode_unsetlog(self, ctx:commands.Context):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        await cursor.execute('SELECT "admin.autoslowmode" FROM "Module Channels" WHERE guild_id=?;', [ctx.guild.id])
        channels_json = await cursor.fetchone()
        channels_json = channels_json[0]

        if channels_json:
            channels = json.loads(channels_json)
        
        else:
            channels = json.loads('{"channels":[], "analytics_channel":null, "max_rate":0.5}')

        
        if channels['analytics_channel']:
            channels['analytics_channel'] = None
            channels_json = json.dumps(channels)
            await cursor.execute('''INSERT INTO "Module Channels"(guild_id, 'admin.autoslowmode') VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET 'admin.autoslowmode'=?;''', (ctx.guild.id, channels_json, channels_json))
            await db.commit()
            await ctx.send(f'Ya no se reportarán datos sobre AutoSlowmode')
        
        else:
            await ctx.send("No hay un canal registrado.")
        

        await db.close()
        

def setup(bot):
    bot.add_cog(AutoSlowmode(bot))
