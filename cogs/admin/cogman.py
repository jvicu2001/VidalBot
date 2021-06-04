import glob
from typing import Mapping
import logging

import discord
from discord.ext import commands
from discord.ext.commands.errors import ExtensionAlreadyLoaded, ExtensionError, ExtensionNotFound, ExtensionNotLoaded, NoEntryPointError


class CogManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.category = "Owner"
        self.embed_color = discord.Colour.purple()
        self.logger = logging.getLogger('discord')

    
    @commands.is_owner()
    @commands.group(
        name = 'cogman',
        brief = 'Administra los Cogs del bot',
        help = 'Administra los Cogs del bot, permitiendo (des)habilitar y recargar cogs individualmente.',
        hidden=True
    )
    async def cogman(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.cogman)
    

    """
    --- LISTADO MÓDULOS ---
    """
    def order_cogs(self, cogmap: Mapping):
        values = {}
        for module in cogmap.items():
            if module[1].category not in values:
                values.update({module[1].category: []})
            values[module[1].category].append(module[0])
            print(module[1].__module__)
        return values
    
    
    @commands.is_owner()
    @cogman.group(
        name = 'list',
        help = 'Lista los Cogs cargados'
    )
    async def cogman_list(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            values = self.order_cogs(self.bot.cogs)

            embed = discord.Embed(
                title='Cogs cargados',
                type='rich',
                color=self.embed_color
            )
            for category in values.items():
                embed.add_field(
                    name=category[0],
                    value=", ".join(category[1]),
                    inline=False
                )
            await ctx.send(embed=embed)

    @commands.is_owner()
    @cogman_list.command(
        name='unloaded',
        help='Lista los módulos no cargados'
    )
    async def cogman_list_unloaded(self, ctx: commands.Context):
        extensions = [path[2:-3].replace('/', '.') for path in glob.glob('./cogs/*/*.py')]
        modlist = set([mod.__module__ for mod in list(self.bot.cogs.values())])
        unloaded_modules = [mod for mod in extensions if mod not in modlist]
        if len(unloaded_modules) > 0:
            await ctx.send(f'Modulos no cargados: {", ".join(unloaded_modules)}')
        else:
            await ctx.send("No hay modulos sin cargar.")

    
    @commands.is_owner()
    @cogman_list.command(
        name='extensions',
        aliases=['extension', 'ext'],
        help='Lista los cogs por su extensión'
    )
    async def cogman_list_ext(self, ctx: commands.Context):
        #extensions = [path[2:-3].replace('/', '.') for path in glob.glob('./cogs/*/*.py')]
        cogs = self.bot.cogs.items()
        extensions = {}
        for cog in cogs:
            extension = cog[1].__module__
            if extension not in extensions:
                extensions.update({extension: []})
            extensions[extension].append(cog[0])

        embed = discord.Embed(
            title='Cogs cargados',
            type='rich',
            color=self.embed_color
        )
        for module in sorted(extensions.keys()):
            embed.add_field(
                name=module,
                value=", ".join(extensions[module])
            )
        await ctx.send(embed=embed)

    
    """
    --- MANEJO MÓDULOS
    """
    @commands.is_owner()
    @cogman.command(
        name='reload',
        help='Recarga un módulo'
    )
    async def cogman_reload(self, ctx: commands.Context, module: str):
        if module != self.__module__:
            try:
                self.bot.reload_extension(module)
                await ctx.send("Módulo recargado correctamente")
                self.logger.info(f'Se recargó el módulo {module}')
                return
            except ExtensionNotFound:
                await ctx.send("""No se encontró el módulo.
                Prueba buscando el nombre del módulo con el comando ``cogman list unloaded``""")
            except ExtensionNotLoaded:
                await ctx.send("No se pudo cargar el módulo.")
            except NoEntryPointError:
                await ctx.send("El módulo no tiene configurado la función ``setup``.")
            except ExtensionError:
                await ctx.send("La función ``setup`` del módulo tuvo problemas al ejecutarse.")
        else:
            await ctx.send("¡No está permitido recargar a Cogman!")
    
    @commands.is_owner()
    @cogman.command(
        name='load',
        help='Carga un módulo'
    )
    async def cogman_load(self, ctx: commands.Context, module: str):
        try:
            self.bot.load_extension(module)
            await ctx.send("Módulo recargado correctamente")
            self.logger.info(f'Se cargó el módulo {module}')
        except ExtensionNotFound:
            await ctx.send("""No se encontró el módulo.
            Prueba buscando el nombre del módulo con el comando ``cogman list unloaded``""")
        except ExtensionAlreadyLoaded:
            await ctx.send("Este módulo ya se encuentra cargado.")
        except NoEntryPointError:
            await ctx.send("El módulo no tiene configurado la función ``setup``.")
        except ExtensionError:
            await ctx.send("La función ``setup`` del módulo tuvo problemas al ejecutarse.")

    @commands.is_owner()
    @cogman.command(
        name='unload',
        help='Remueve un módulo'
    )
    async def cogman_unload(self, ctx: commands.Context, module: str):
        if module != self.__module__:
            try:
                self.bot.unload_extension(module)
                await ctx.send("Módulo removido correctamente")
                self.logger.info(f'Se deshabilitó el módulo {module}')
            except ExtensionNotFound:
                await ctx.send("""No se encontró el módulo.
                Prueba buscando el nombre del módulo con el comando ``cogman list extensions``""")
            except ExtensionNotLoaded:
                await ctx.send("El módulo no está cargado.")
        else:
            await ctx.send("¡No está permitido remover a Cogman!")

def setup(bot):
    bot.add_cog(CogManager(bot))
