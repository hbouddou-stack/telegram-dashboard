import io

handlers_code = """
# ==========================================
# SMS GATEWAY API
# ==========================================

async def api_admin_gateway_queue_sms(request):
    from aiohttp import web
    import datetime
    import aiosqlite
    import re
    from config import DATABASE_PATH
    import config as cfg

    try:
        data = await request.json()
        student_ids = data.get('student_ids', [])
        if not student_ids: return web.json_response({'success': False})

        bot_user = getattr(cfg, 'MAIN_BOT_USERNAME', 'alsirahquizz_bot') or 'alsirahquizz_bot'
        now_str = datetime.datetime.utcnow().isoformat()
        queued = 0

        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            for sid in student_ids:
                async with db.execute("SELECT * FROM academy_students WHERE student_id = ?", (sid,)) as cur:
                    s = await cur.fetchone()
                if not s or not s['phone']: continue

                phone = re.sub(r'\\D', '', s['phone'])
                if phone.startswith('0'): phone = '212' + phone[1:]
                
                token = s['magic_token'] or s['student_id']
                fname = s['first_name'] or ''
                text = f"السلام عليكم {fname}، إليك رابط الدخول الخاص بك للأكاديمية:\\nhttps://t.me/{bot_user}?start=sms_{token}"

                await db.execute(
                    "INSERT INTO sms_queue (student_id, phone, message, status, created_at) VALUES (?, ?, ?, 'PENDING', ?)",
                    (sid, phone, text, now_str)
                )
                queued += 1
            await db.commit()

        return web.json_response({'success': True, 'queued': queued})
    except Exception as e:
        import traceback; traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)})

async def api_sms_gateway_poll(request):
    from aiohttp import web
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT COUNT(*) as cnt FROM sms_queue WHERE status = 'PENDING'") as cur:
                pending_count = (await cur.fetchone())['cnt']
            
            async with db.execute("SELECT id, phone, message FROM sms_queue WHERE status = 'PENDING' ORDER BY id ASC LIMIT 1") as cur:
                row = await cur.fetchone()

            if row:
                return web.json_response({
                    "success": True,
                    "pending_count": pending_count,
                    "message": {
                        "id": row['id'],
                        "to": "+" + row['phone'] if not row['phone'].startswith('+') else row['phone'],
                        "message": row['message']
                    }
                })
            return web.json_response({"success": False, "pending_count": 0})
    except Exception as e:
        from aiohttp import web
        return web.json_response({"success": False, "error": str(e)})

async def api_sms_gateway_callback(request):
    from aiohttp import web
    import datetime
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        msg_id = data.get('id')
        status = data.get('status', 'SENT')

        if msg_id:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                now_str = datetime.datetime.utcnow().isoformat()
                await db.execute("UPDATE sms_queue SET status = ?, sent_at = ? WHERE id = ?", (status, now_str, msg_id))
                
                if status == 'SENT':
                    async with db.execute("SELECT student_id FROM sms_queue WHERE id = ?", (msg_id,)) as cur:
                        row = await cur.fetchone()
                    if row:
                        sid = row['student_id']
                        await db.execute("UPDATE academy_students SET sms_sent = 1, sms_sent_at = ? WHERE student_id = ?", (now_str, sid))
                        admin_name = "SMS Gateway"
                        note_text = f"[بواسطة: {admin_name}] [نوع: SYSTEM]\\nSMS automatique envoyé avec succès."
                        await db.execute(
                            "INSERT INTO student_logs (student_id, action_type, description, telegram_name) VALUES (?, ?, ?, ?)",
                            (sid, "SMS_SENT", note_text, admin_name)
                        )
                await db.commit()

        return web.json_response({"success": True})
    except Exception as e:
        import traceback; traceback.print_exc()
        from aiohttp import web
        return web.json_response({"success": False, "error": str(e)})

# ==========================================
"""

with io.open('main.py', 'r', encoding='utf-8') as f:
    main_c = f.read()

main_c = main_c.replace("async def api_admin_gateway_action(request: web.Request):", handlers_code + "\nasync def api_admin_gateway_action(request: web.Request):")

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_c)
print("Handlers injected!")
