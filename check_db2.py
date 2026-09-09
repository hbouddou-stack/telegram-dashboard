import aiosqlite
import asyncio

async def inspect():
    async with aiosqlite.connect('backup_bot.db') as db:
        async with db.execute("SELECT source, strftime('%Y-%m-%d %H:%M', created_at) as exact, COUNT(*) as cnt FROM academy_students GROUP BY source, exact ORDER BY exact DESC LIMIT 15") as cur:
            for r in await cur.fetchall():
                print(f'{r[0]} | {r[1]} | {r[2]}')

asyncio.run(inspect())
