import logging
import glob

import discord
from discord.ext import commands
from discord.flags import Intents
import json

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

            
def get_prefix(bot, message:discord.Message):
    file = open("prefixes.json", 'r')
    prefixes = json.load(file)
    file.close()
    try:
        return commands.when_mentioned_or(prefixes[f'{message.guild.id}'])(bot, message)
    except (KeyError, AttributeError):
        return commands.when_mentioned_or(config.prefix)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, intents=Intents.all())
logger.info(f"Bot instance created with default prefix {config.prefix}")

extensions = [path[2:-3].replace('/', '.') for path in glob.glob('./cogs/*/*.py')]

for module in extensions:
    try:
        bot.load_extension(module)
        logger.info(f'Loaded extension {module}')
    except ModuleNotFoundError:
        logger.warning(f'{module} is NOT a module.')

bot.run(config.token)
logger.info('Bot instance started')
