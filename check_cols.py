import aiosqlite
import asyncio

async def test():
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("PRAGMA table_info(academy_students)") as cur:
            cols = [row[1] for row in await cur.fetchall()]
            
    query_cols = [
        "student_id", "academic_id", "first_name", "last_name", "email", "telegram_id", "telegram_username",
        "year", "gender", "dob", "source", "phone", "created_at", "payment_status",
        "email_sent", "email_sent_at", "email_opened_at", "email_clicked_at",
        "whatsapp_sent", "whatsapp_sent_at", "whatsapp_clicked_at", "last_click_source",
        "group_joined", "joined_at", "folder_clicked_at", "bot_started_at", "excluded"
    ]
    
    missing = [c for c in query_cols if c not in cols]
    print("MISSING IN DB:", missing)

asyncio.run(test())
