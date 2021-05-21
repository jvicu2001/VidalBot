import logging

import discord
from discord.ext import commands
from discord.flags import Intents

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

prefix = config.prefix

base_modules = [
            'cogs.fun.hello',
            'cogs.fun.animal_pics',
            'cogs.fun.akinator',
            'cogs.fun.kanye',
            'cogs.fun.tyaas',
            'cogs.db.initialize'
            ]
            


bot = commands.Bot(command_prefix=prefix, intents=Intents.all())
logger.info(f"Bot instance created with prefix {prefix}")

for module in base_modules:
    bot.load_extension(module)
    logger.info(f'Loaded extension {module}')

bot.run(config.token)
logger.info('Bot instance started')
