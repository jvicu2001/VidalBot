import logging
import glob

import discord
from discord.channel import TextChannel
from discord.ext import commands, ipc
from discord.ext.commands.errors import ExtensionNotFound
from discord.flags import Intents
import json
import utils.database

import config

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(console_handler)


class VidalBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def invoke(self, ctx: commands.Context):

        # Ignora los mensajes en los canales bloqueados si no se tiene un rol de staff
        if ctx.guild:
            if ctx.author.guild_permissions.administrator is False:
                data: dict = await utils.database.get_guild_config(ctx.guild)
                if data:
                    lck_chan = data.get('locked_channels', [])
                    staffroles = data.get('staffroles', [])
                    if ctx.channel.id in lck_chan and len(set(staffroles).intersection([r.id for r in ctx.author.roles])) == 0:
                        return
        return await super().invoke(ctx)


def get_prefix(bot, message:discord.Message):
    file = open("prefixes.json", 'r')
    prefixes = json.load(file)
    file.close()
    try:
        return commands.when_mentioned_or(prefixes[f'{message.guild.id}'])(bot, message)
    except (KeyError, AttributeError):
        return commands.when_mentioned_or(config.prefix)(bot, message)


bot = VidalBot(command_prefix=get_prefix, intents=Intents.all())
logger.info(f"Bot instance created with default prefix {config.prefix}")

# Carga las extensiones comunes
extensions = [path[2:-3].replace('/', '.').replace('\\', '.') for path in glob.glob('./cogs/*/*.py')]
for module in extensions:
    try:
        bot.load_extension(module)
        logger.info(f'Loaded extension {module}')
    except (ModuleNotFoundError, ExtensionNotFound):
        logger.warning(f'{module} is NOT a module.')

bot.run(config.token)
logger.info('Bot instance started')

