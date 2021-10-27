import datetime
import json

import aiohttp
import aiosqlite
import config
import discord
from discord.ext import commands, tasks




class HoroscopoTiaYoli(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category = "Fun"
        self.init_db.start()

    @tasks.loop(minutes=2, count=1)
    async def init_db(self):
        db = await aiosqlite.connect(config.database)
        await db.execute('''
    CREATE TABLE IF NOT EXISTS "TiaYoli" (
        "id" INTEGER NOT NULL UNIQUE,
        "horoscopo"	TEXT NOT NULL,
        "dia" TEXT NOT NULL,
        PRIMARY KEY("id")
    );
        ''')
        await db.commit()
        await db.close()
        

    meses = {
    "enero": "01", 
    "febrero": "02", 
    "marzo": "03", 
    "abril": "04", 
    "mayo": "05", 
    "junio": "06", 
    "julio": "07", 
    "agosto": "08", 
    "septiembre": "09", 
    "octubre": "10", 
    "noviembre": "11", 
    "diciembre": "12"
    } 

    async def armar_horoscopo(self, signo: str, horoscopo: dict) -> discord.Embed:
        embed = discord.Embed(
            title = horoscopo['horoscopo'][signo]['nombre'],
            type = 'rich',
            color = 0x100029,
            description=f"""{horoscopo['horoscopo'][signo]['fechaSigno']}\n
❤ Amor: {horoscopo['horoscopo'][signo]['amor']}\n
🏥 Salud: {horoscopo['horoscopo'][signo]['salud']}\n
💵 Dinero: {horoscopo['horoscopo'][signo]['dinero']}\n
🎨 Color: {horoscopo['horoscopo'][signo]['color']}\n
🔢 Número: {horoscopo['horoscopo'][signo]['numero']}\n\
Horóscopo para el {horoscopo['titulo']}"""
            )
        embed.set_footer(
            text = f"Horóscopo auspiciado por {horoscopo['autor']} y xor.cl",
            icon_url='https://i.imgur.com/aG8Jbzz.png'
        )
        return embed
    
    async def obtener_horoscopo(self, ctx: commands.Context, cursor: aiosqlite.Cursor):
        tyaas = 'https://api.xor.cl/tyaas/'
        # Obtener datos desde la API de TYaaS
        async with aiohttp.ClientSession() as session:
                async with session.get(tyaas) as resp:
                    if resp.status == 200:
                        horoscopo = await resp.json()
                        horoscopo_dump = json.dumps(horoscopo)
                        # Obtener valores ya guardados en la base de datos
                        await cursor.execute("""SELECT * FROM 'TiaYoli';""")
                        valor_db = await cursor.fetchone()

                        # Si es que existen datos y estos corresponden al día actual, devolver
                        # los datos ya guardados en la base de datos.
                        # Caso contrario, se actualizan los datos de la base de datos
                        # y se devuelven estos nuevos datos
                        if valor_db:
                            dia_guardado = valor_db[2]
                            if dia_guardado[5:] == f"{self.meses[horoscopo['titulo'][2:].strip()]}-{int(horoscopo['titulo'][:2]):02}":
                                return json.loads(valor_db[1])
                        
                        dia = datetime.datetime.today().strftime("%Y-%m-%d")

                        # Guardar los nuevos datos en la base de datos
                        await cursor.execute('''INSERT INTO "TiaYoli"(id, horoscopo, dia) VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET horoscopo=?, dia=?;''', [0, horoscopo_dump, dia, horoscopo_dump, dia])
                        return horoscopo
                    else:
                        await ctx.send(f'Hubo un error\nError {resp.status}')
                        return None

    @commands.command(
        name='horoscopo',
        aliases=['yoli', 'tiayoli'],
        help='¡Obtenga su horóscopo de la Tía Yoli!'
    )
    async def horoscopo(self, ctx, signo: str):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        await cursor.execute("""SELECT * FROM 'TiaYoli';""")
        saved_data = await cursor.fetchone()
        # Si es que existen datos en la base de dato y corresponden al día actual,
        # utilizar estos datos guardados.
        # En caso contrario, obtener nuevos datos desde la API
        if saved_data:
            today = datetime.date.today()
            saved_day = datetime.date.fromisoformat(saved_data[2])
            if today == saved_day:
                horoscopo = json.loads(saved_data[1])
            else:
                horoscopo = await self.obtener_horoscopo(ctx, cursor)
        else:
            horoscopo = await self.obtener_horoscopo(ctx, cursor)
        
        if horoscopo:
            try:
                embed = await self.armar_horoscopo(signo.lower(), horoscopo)
                await ctx.send(embed=embed)
            except KeyError:
                await ctx.send("No se pudo encontrar el signo.\nAsegurate de que está bien escrito y de que no tenga tildes.")

        await db.commit()
        await db.close()




def setup(bot):
    bot.add_cog(HoroscopoTiaYoli(bot))
