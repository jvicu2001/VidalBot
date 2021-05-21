from sqlite3.dbapi2 import Cursor
from discord.ext import commands
import sqlite3

import config

class DatabaseSetup(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        db = sqlite3.connect(config.database)
        cursor = db.cursor()

        cursor.execute('''
CREATE TABLE IF NOT EXISTS "Module Channels" (
	"guild_id"	INTEGER NOT NULL UNIQUE,
	PRIMARY KEY("guild_id")
);
        ''')
        db.commit()
        db.close()


def setup(bot):
    bot.add_cog(DatabaseSetup(bot))