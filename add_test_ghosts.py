import asyncio
import aiosqlite
from config import DATABASE_PATH

async def add_test_ghosts():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Insert fake ghost users who have NO matching academy_students record
        test_ghosts = [
            (999001, 'Ahmed', 'Benali', 'ahmed_benali_test'),
            (999002, 'Fatima', 'Alaoui', 'fatima_test'),
            (999003, 'Youssef', None, None),
        ]
        for tid, fn, ln, un in test_ghosts:
            await db.execute("""
                INSERT OR IGNORE INTO users (telegram_id, first_name, last_name, username, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (tid, fn, ln, un))
        await db.commit()
        print("Test ghosts added!")
        
        # Verify
        async with db.execute("""
            SELECT u.telegram_id, u.first_name, u.username
            FROM users u
            LEFT JOIN academy_students s ON s.telegram_id = u.telegram_id
            WHERE s.telegram_id IS NULL
            ORDER BY u.created_at DESC LIMIT 10
        """) as cur:
            rows = await cur.fetchall()
            print(f"Total unlinked users: {len(rows)}")
            for r in rows:
                print(dict(r))

asyncio.run(add_test_ghosts())
