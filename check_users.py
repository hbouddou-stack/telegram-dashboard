import aiosqlite
import asyncio

async def test():
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("PRAGMA table_info(users)") as cur:
            cols = [row[1] for row in await cur.fetchall()]
            
    query_cols = ["telegram_id", "first_name", "last_name"]
    missing = [c for c in query_cols if c not in cols]
    print("MISSING IN USERS:", missing)

asyncio.run(test())
