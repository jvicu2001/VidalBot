import logging

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

base_modules = [
            'cogs.fun.hello',
            'cogs.fun.animal_pics',
            'cogs.fun.akinator',
            'cogs.fun.kanye',
            'cogs.fun.games',
            'cogs.fun.tyaas',
            'cogs.fun.wates',
            'cogs.fun.image_manipulation',
            'cogs.admin.misc',
            'cogs.admin.base_error_catch',
            'cogs.db.initialize'
            ]
            
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

for module in base_modules:
    bot.load_extension(module)
    logger.info(f'Loaded extension {module}')

bot.run(config.token)
logger.info('Bot instance started')
