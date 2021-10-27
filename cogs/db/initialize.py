from discord.ext import commands
import aiosqlite

import config

class DatabaseSetup(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.category = "Owner"

    @commands.Cog.listener()
    async def on_ready(self):
        db = await aiosqlite.connect(config.database)
        cursor = await db.cursor()

        await cursor.execute('''
        CREATE TABLE IF NOT EXISTS "Module Channels" (
            guild_id INTEGER NOT NULL UNIQUE,
            PRIMARY KEY("guild_id")
        );
        ''')
        await cursor.execute('''
        CREATE TABLE IF NOT EXISTS GlobalVars (
            property_name TEXT NOT NULL UNIQUE,
            property_value TEXT,
            PRIMARY KEY(property_name)
        );''')
        await cursor.execute('''
        CREATE TABLE IF NOT EXISTS GuildConfig (
            "guild_id" INTEGER NOT NULL UNIQUE,
            config TEXT DEFAULT "{}",
            PRIMARY KEY("guild_id")
        );''')
        await db.commit()
        await db.close()


def setup(bot):
    bot.add_cog(DatabaseSetup(bot))