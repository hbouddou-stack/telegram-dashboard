import asyncio
import aiosqlite

async def test():
    async with aiosqlite.connect('backup_bot.db') as db:
        # Check if 104820 is there
        async with db.execute("SELECT student_id, magic_token, telegram_id FROM academy_students WHERE student_id = 104820") as cur:
            print("Direct INT query:", await cur.fetchone())

        clean_sid = "104820"
        async with db.execute("SELECT student_id, magic_token, telegram_id FROM academy_students WHERE magic_token = ? OR student_id = ? OR LOWER(email) = ?", (clean_sid, clean_sid, clean_sid.lower())) as cur:
            print("Parameter query:", await cur.fetchone())

asyncio.run(test())
