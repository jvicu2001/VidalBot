import aiosqlite
import config
import discord
import json

async def get_guild_config(guild: discord.Guild):
    db = await aiosqlite.connect(config.database)
    cursor = await db.cursor()
    await cursor.execute('''
    SELECT config FROM GuildConfig WHERE guild_id=?;''', (guild.id,))
    data = await cursor.fetchone()
    await db.close()
    if data:
        return json.loads(data[0])
    else:
        await set_guild_config(guild, dict())
        return dict()

async def set_guild_config(guild: discord.Guild, data: dict):
    db = await aiosqlite.connect(config.database)
    cursor = await db.cursor()
    data_s = json.dumps(data)
    await cursor.execute('''
    INSERT INTO GuildConfig(guild_id, config) VALUES(?, ?)
    ON CONFLICT(guild_id) DO UPDATE SET config=?''', (guild.id, data_s, data_s))
    await db.commit()
    await db.close()
