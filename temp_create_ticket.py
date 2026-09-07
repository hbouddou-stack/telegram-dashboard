async def create_crm_ticket(telegram_id, username, first_name, theme, subtheme, message, status='new', is_ghost=False, ai_topic='', file_data=None, file_name=None):
    from config import DATABASE_PATH
    import aiosqlite
    import json
    from datetime import datetime
    try:
        has_attachment = 1 if (file_data or file_name) else 0
        init_conv = [{
            "sender": "student",
            "name": first_name or "أنت",
            "text": message,
            "file_data": file_data,
            "file_name": file_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }]
        conv_json = json.dumps(init_conv, ensure_ascii=False)
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute(
                'INSERT INTO crm_tickets (telegram_id, username, first_name, theme, subtheme, message, status, is_ghost, ai_topic, conversation, has_attachment, file_data, file_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (telegram_id, username, first_name, theme, subtheme, message, status, is_ghost, ai_topic, conv_json, has_attachment, file_data, file_name)
            )
            await db.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return None
