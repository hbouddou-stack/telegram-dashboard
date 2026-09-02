import asyncio
import aiosqlite

async def test():
    # Use the same db path as main.py uses locally
    from config import DATABASE_PATH
    print("DB PATH:", DATABASE_PATH)
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT s.student_id, s.academic_id, s.first_name, s.last_name, s.email, s.telegram_id, s.telegram_username,
                       s.year, s.gender, s.dob, s.source, s.phone, s.created_at, s.payment_status,
                       s.email_sent, s.email_sent_at, s.email_opened_at, s.email_clicked_at,
                       s.whatsapp_sent, s.whatsapp_sent_at, s.whatsapp_clicked_at, s.last_click_source,
                       s.group_joined, s.joined_at, s.folder_clicked_at, s.bot_started_at, s.excluded,
                       u.first_name as tg_first_name, u.last_name as tg_last_name
                FROM academy_students s
                LEFT JOIN users u ON u.telegram_id = s.telegram_id
                ORDER BY s.created_at DESC, s.first_name ASC
            """) as cur:
                rows = await cur.fetchall()
                print("Query Success. Rows:", len(rows))
    except Exception as e:
        print("ERROR:", str(e))

asyncio.run(test())
