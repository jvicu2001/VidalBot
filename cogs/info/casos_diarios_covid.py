import asyncio
import csv
import datetime

import aiohttp
import aiosqlite
import config
import discord
from discord.ext import commands, tasks
from discord.ext.commands.errors import MissingRequiredArgument

meses = {
    "01": "enero", 
    "02": "febrero", 
    "03": "marzo", 
    "04": "abril", 
    "05": "mayo", 
    "06": "junio", 
    "07": "julio", 
    "08": "agosto", 
    "09": "septiembre", 
    "10": "octubre", 
    "11": "noviembre", 
    "12": "diciembre"
    } 


class CasosCovidChile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category = "Info"
        self.init_db.start()
        self.url_consulta = "https://api.github.com/repos/MinCiencia/Datos-COVID19/contents/output/producto5"

        self.consultar_cambio_datos.start()

    @tasks.loop(minutes=2, count=1)
    async def init_db(self):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        await cursor.executemany('''
        INSERT OR IGNORE into GlobalVars(property_name, property_value) VALUES(?, NULL);
        ''', (("covid_cl_SHA",), ("covid_cl_text",), ("covid_cl_channel",), ("covid_cl_fecha",)))
        await db.commit()
        await db.close()
    

    """
    Revisa cada 15 minutos si hay algún cambio en el hash del archivo de donde se obtienen
    los valores de los casos de contagios nacionales.

    Si se encuentra una diferencia, ejecuta self.texto_datos, que obtiene todos los datos
    necesarios y construye un mensaje estructurado para poder ser enviado al canal
    predefinido de Discord y de Telegram, de haber sidos configurados.

    Para evitar reconstruir los datos cada vez que se solicite el mensaje nuevamente, se
    almacena el texto estructurado en la base de datos.
    """
    @tasks.loop(minutes=15)
    async def consultar_cambio_datos(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url_consulta) as resp:
                if resp.status == 200:
                    archivos = await resp.json()
                    dato = [d for d in archivos if d['name'] == "TotalesNacionales_T.csv"][0]
                    
                    db = await aiosqlite.connect(config.database)
                    cursor = await db.cursor()
                    await cursor.execute('''
                    SELECT property_value FROM GlobalVars WHERE property_name="covid_cl_SHA";
                    ''')

                    # Se compara en hash SHA almacenado contra el archivo que se encuentra en GitHub
                    sha = await cursor.fetchone()
                    if sha[0] != dato['sha']:
                        await cursor.executemany('''
                        UPDATE GlobalVars SET property_value=? WHERE property_name=?;
                        ''', ((dato['sha'],"covid_cl_SHA"), (datetime.datetime.utcnow().isoformat(),"covid_cl_fecha")))
                        
                        # Como todos los datos se actualizan en un único Job en GitHub,
                        # se pueden obtener todos los datos al mismo tiempo.
                        texto = await self.texto_datos(dato['download_url'])

                        # Guardar texto para consultas individuales
                        await cursor.execute('''UPDATE GlobalVars SET property_value=? WHERE property_name=?''',
                        (texto, "covid_cl_text"))
                        await db.commit()

                        # Publicar los resultados en Discord y Telegram
                        await self.discord_publish(texto)
                        await self.telegram_publish(texto)
                        
                    await db.close()


    """
    Grupo base de los comandos sobre COVID.
    Si se llama por si solo, envía el mensaje estructurado que se encuentra en
    la base de datos.
    """
    @commands.group(
        name = 'covid',
        help = 'Solicita y administra la recolección de datos sobre el COVID-19 en Chile'
    )
    async def covid(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            db = await aiosqlite.connect(config.database)
            cursor = await db.cursor()
            await cursor.execute('''SELECT property_value FROM GlobalVars WHERE property_name=?;''',
                        ("covid_cl_text",))
            
            message = await cursor.fetchone()
            message = message[0]

            if message:
                await self.discord_publish(message, ctx.channel.id)
            else:
                await ctx.send('No hay información recolectada aún.')

            await db.close()

    """
    Establece el canal de Discord donde se publicarán los datos diarios.
    Es preferible que este canal sea de anuncios, porque estos permiten
    publicar sus mensajes en otros servidores.
    """
    @commands.guild_only()
    @commands.is_owner()
    @commands.has_permissions(administrator=True)
    @covid.command(
        name = 'setchannel',
        brief = 'Establece canal datos COVID-19',
        help = 'Establece el canal donde se publicarán actualizaciones sobre el COVID-19'
    )
    async def covid_setchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        await cursor.execute('''UPDATE GlobalVars SET property_value=? WHERE property_name=?;''',
                    (channel.id, "covid_cl_channel"))

        await db.commit()
        await db.close()

        await ctx.send(f'Canal de publicación de datos actualizado a {channel.mention}')

    @covid_setchannel.error
    async def covid_setchannel_error(self, ctx: commands.Context, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send_help(self.covid_setchannel)
        else:
            await ctx.send(f'Ha ocurrido un error\n```\n{error.__class__.__name__}: {error}\n```')

    
    """
    Remueve el canal de publicación de los datos diarios en Discord.
    """
    @commands.guild_only()
    @commands.is_owner()
    @commands.has_permissions(administrator=True)
    @covid.command(
        name = 'removechannel',
        brief = 'Remueve canal datos COVID-19',
        help = 'Remueve el canal donde se publicarán actualizaciones sobre el COVID-19'
    )
    async def covid_removechannel(self, ctx: commands.Context):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        await cursor.execute('''UPDATE GlobalVars SET property_value=? WHERE property_name=?;''',
                    (None, "covid_cl_channel"))

        await db.commit()
        await db.close()

        await ctx.send('Canal de publicación de datos eliminado.')

    """
    (Re)enviar el texto estructurado al canal de Telegram preconfigurado.
    Disponible por si hubo algún problema con la publicación automática.
    """
    @commands.guild_only()
    @commands.is_owner()
    @covid.command(
        name = 'telegram_post',
        brief = 'Postea la info guardada a Telegram',
        help = 'Envía el mensaje guardado de la info sobre el COVID-19 al canal predefinido de Telegram'
    )
    async def covid_telegram_post(self, ctx: commands.Context):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        await cursor.execute('''SELECT property_value FROM GlobalVars WHERE property_name=?;''',
                    ("covid_cl_text",))

        message = await cursor.fetchone()
        
        message = message[0]

        if message:
            resp = await self.telegram_publish(message)
            if resp['okay']:
                await ctx.send('El mensaje fue enviado exitosamente.')
            else:
                await ctx.send(f"El mensaje no se pudo enviar\nCod. {resp['error_code']}: {resp['description']}")
        else:
            await ctx.send('No hay información recolectada aún.')

        await db.close()

    @commands.guild_only()
    @covid.command(
        name = 'post',
        brief = 'Postea la info guardada en el canal prefedinido',
        help = 'Envía el mensaje guardado de la info sobre el COVID-19 al canal predefinido de Discord'
    )
    async def covid_discord_post(self, ctx: commands.Context):
        pass

    
    async def telegram_publish(self, message: str):
        if config.covid['bot_token'] != '' and config.covid['group_id']:
            message = message.replace('**', '#').replace('*', '_').replace('#', '*').replace('(', '\\(').replace(')', '\\)').replace('.', '\\.').replace('-', '\\-').replace('+', '\\+')
            async with aiohttp.ClientSession() as session:
                params = {
                    'chat_id': config.covid['group_id'],
                    'text': message + '\n[Enviado por VidalBot](https://github.com/jvicu2001/VidalBot)',
                    'parse_mode': 'MarkdownV2',
                    'disable_web_page_preview': 'true'
                }
                async with session.get(
                    f"https://api.telegram.org/bot{config.covid['bot_token']}/sendMessage",
                    params=params
                ) as resp:
                    return await resp.json()

        return 'Canal de Telegram no configurado.'


    async def discord_publish(self, message:str, channel_id = None):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()
        await cursor.execute('''
        SELECT property_value FROM GlobalVars WHERE property_name=?;
        ''', ("covid_cl_channel",))
        if channel_id is None:
            channel_id = await cursor.fetchone()
            channel_id = channel_id[0]
        if channel_id:
            channel: discord.TextChannel = self.bot.get_channel(int(channel_id))
        else:
            print('No hay un canal configurado para mostrar la información sobre COVID-19')
            return

        embed = discord.Embed(
            title = 'Estado del Coronavirus COVID-19 en Chile',
            type = 'rich',
            color = discord.Colour.blurple(),
            description = message
        )
        await cursor.execute('''
            SELECT property_value FROM GlobalVars WHERE property_name=?;
            ''', ("covid_cl_fecha",))
        fecha = await cursor.fetchone()
        fecha = fecha[0]
        dt = datetime.datetime.fromisoformat(fecha)
        embed.set_footer(
            text = f"Información actualizada al: {dt.strftime('%a, %d %b %Y, %H:%m:%S UTC')}"
        )
        sent_message: discord.Message = await channel.send(embed=embed)

        # Intentar publicar el mensaje
        try:
            await sent_message.publish()
        except:
            pass

        

    async def texto_datos(self, datos_url: str):
        url_positividad = 'https://github.com/MinCiencia/Datos-COVID19/raw/master/output/producto49/Positividad_Diaria_Media_T.csv'
        url_pcr = 'https://github.com/MinCiencia/Datos-COVID19/raw/master/output/producto17/PCREstablecimiento_T.csv'
        url_ventiladores = 'https://github.com/MinCiencia/Datos-COVID19/raw/master/output/producto20/NumeroVentiladores_T.csv'
        url_residencias = 'https://github.com/MinCiencia/Datos-COVID19/raw/master/output/producto36/ResidenciasSanitarias_T.csv'
        url_UCI = 'https://github.com/MinCiencia/Datos-COVID19/raw/master/output/producto23/PacientesCriticos_T.csv'
        url_VMI = 'https://github.com/MinCiencia/Datos-COVID19/raw/master/output/producto30/PacientesVMI_T.csv'

        def nf(val):
            return '.'.join([str(val)[::-1][i:i + 3] for i in range(0, len(str(val)), 3)])[::-1].replace('-.', '-')


        """
        --- CASOS COVID ---
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(datos_url) as resp:
                if resp.status == 200:
                    datos = await resp.text()
                    datos = csv.DictReader(datos.splitlines())

                    *_, ayer_casos, hoy_casos = datos
                    _ = None

                    def diff(anterior, actual, campo: str):
                        valor = round(float(actual[campo])) - round(float(anterior[campo]))
                        return f"{['', '+'][valor > 0]}{valor}"

                    dia = f"{hoy_casos['Fecha'][8:]} de {meses[hoy_casos['Fecha'][5:7]]} del {hoy_casos['Fecha'][:4]}"


        """
        --- PCR ---
        """
        await asyncio.sleep(2)  # Para evitar un RateLimit
        async with aiohttp.ClientSession() as session:
            async with session.get(url_pcr) as resp:
                if resp.status == 200:
                    datos = await resp.text()
                    datos = csv.DictReader(datos.splitlines())

                    *_, pcr = datos
                    _ = None

        
        """
        --- POSITIVIDAD ---
        """
        await asyncio.sleep(2)  # Para evitar un RateLimit
        async with aiohttp.ClientSession() as session:
            async with session.get(url_positividad) as resp:
                if resp.status == 200:
                    datos = await resp.text()
                    datos = csv.DictReader(datos.splitlines())

                    *_, positividad = datos
                    _ = None


        """
        --- VENTILADORES ---
        """
        await asyncio.sleep(2)  # Para evitar un RateLimit
        async with aiohttp.ClientSession() as session:
            async with session.get(url_ventiladores) as resp:
                if resp.status == 200:
                    datos = await resp.text()
                    datos = csv.DictReader(datos.splitlines())

                    *_, ayer_vent, hoy_vent = datos
                    _ = None


        """
        --- RESIDENCIAS ---
        """
        await asyncio.sleep(2)  # Para evitar un RateLimit
        async with aiohttp.ClientSession() as session:
            async with session.get(url_residencias) as resp:
                if resp.status == 200:
                    datos = await resp.text()
                    datos = csv.reader(datos.splitlines())

                    *_, residencias = datos
                    _ = None
                    residencias_total = int(sum([(float(i) if i != '' else 0) for i in residencias[32:]]))
                    residencias_cupos = int(sum([(float(i) if i != '' else 0) for i in residencias[1:17]]))
                    residencias = None
        

        """
        --- PACIENTES CONECTADOS ---
        """
        await asyncio.sleep(2)  # Para evitar un RateLimit
        async with aiohttp.ClientSession() as session:
            async with session.get(url_VMI) as resp:
                if resp.status == 200:
                    datos = await resp.text()
                    datos = csv.DictReader(datos.splitlines())

                    *_, ayer_vmi, hoy_vmi = datos
                    _ = None
        

        """
        --- PACIENTES CRÍTICOS ---
        """
        await asyncio.sleep(2)  # Para evitar un RateLimit
        async with aiohttp.ClientSession() as session:
            async with session.get(url_UCI) as resp:
                if resp.status == 200:
                    datos = await resp.text()
                    datos = csv.DictReader(datos.splitlines())

                    *_, ayer_uci, hoy_uci = datos
                    _ = None
                    
        texto_pub = f"""Información para el día **{dia}** (hasta las 21:00 del día anterior)

**Total confirmados**: {nf(round(float(hoy_casos['Casos totales'])))} (+{nf(round(float(hoy_casos['Casos nuevos totales'])))})
*({nf(round(float(hoy_casos['Casos nuevos con sintomas'])))} sintomáticos, {nf(round(float(hoy_casos['Casos nuevos sin sintomas'])))} asintomáticos, {nf(round(float(hoy_casos['Casos nuevos sin notificar'])))} sin notificar)*
**Total activos**: {nf(round(float(hoy_casos['Casos activos'])))} ({nf(diff(ayer_casos, hoy_casos,'Casos activos'))})
**Recuperados**: {nf(round(float(hoy_casos['Casos confirmados recuperados'])))} ({nf(diff(ayer_casos, hoy_casos, 'Casos confirmados recuperados'))})
**Fallecidos**: {nf(round(float(hoy_casos['Fallecidos'])))} ({nf(diff(ayer_casos, hoy_casos, 'Fallecidos'))})

**Exámenes realizados**: {nf(round(float(pcr['Total realizados'])))} (+{nf(round(float(pcr['Total informados ultimo dia'])))}, positividad: {str(round(float(positividad['positividad'])*100, 2)).replace('.', ',')}%)
**Pacientes conectados**: {nf(round(float(hoy_vmi['Pacientes VMI'])))} ({nf(diff(ayer_vmi, hoy_vmi, 'Pacientes VMI'))}), críticos: {nf(round(float(hoy_uci['Pacientes criticos'])))} ({nf(diff(ayer_uci, hoy_uci ,'Pacientes criticos'))})
**Ventiladores disponibles**: {nf(hoy_vent['disponibles'])} ({nf(diff(ayer_vent, hoy_vent, 'disponibles'))})

**Residencias sanitarias**: {residencias_total} con {residencias_cupos} habitaciones"""

        return texto_pub

def setup(bot):
    bot.add_cog(CasosCovidChile(bot))
