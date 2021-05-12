import asyncio
import logging
from discord.ext import commands

import config

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

prefix = config.prefix

base_modules = [
            'cogs.fun.hello',
            'cogs.fun.animal_pics',
            'cogs.fun.akinator',
            'cogs.fun.kanye'
            ]
            


bot = commands.Bot(command_prefix=prefix)
logger.info(f"Bot instance created with prefix {prefix}")

for module in base_modules:
    bot.load_extension(module)
    logger.info(f'Loaded extension {module}')

bot.run(config.token)
logger.info('Bot instance started')

