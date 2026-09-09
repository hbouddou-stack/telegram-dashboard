import io, re

def update_main():
    with io.open('main.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # 1. SELECT query
    if 's.sms_sent' not in c:
        c = c.replace(
            "s.whatsapp_sent, s.whatsapp_sent_at, s.whatsapp_clicked_at, s.last_click_source,",
            "s.whatsapp_sent, s.whatsapp_sent_at, s.whatsapp_clicked_at, s.sms_sent, s.sms_sent_at, s.last_click_source,"
        )
    
    # 2. Return bot_username
    if "'bot_username'" not in c:
        old_resp = "return web.json_response({'success': True, 'students': students})"
        new_resp = """import config as cfg
        bot_user = getattr(cfg, 'MAIN_BOT_USERNAME', 'alsirahquizz_bot') or 'alsirahquizz_bot'
        return web.json_response({'success': True, 'students': students, 'bot_username': bot_user})"""
        c = c.replace(old_resp, new_resp)

    # 3. Action handling
    if "elif action == 'log_sms':" not in c:
        c = c.replace(
            "await db.commit()\n            \n        return web.json_response({'success': True})",
            """elif action == 'log_sms':
                now_str = datetime.utcnow().isoformat()
                await db.execute("UPDATE academy_students SET sms_sent = 1, sms_sent_at = ? WHERE student_id = ?", (now_str, student_id))
                await log_student_action(student_id, 'SMS_SENT', "Lien direct envoyé par SMS.")
                
            await db.commit()
            
        return web.json_response({'success': True})"""
        )

    # 4. Migrations
    if "ADD COLUMN sms_sent" not in c:
        old_mig = "await db_conn.execute(\"ALTER TABLE academy_students ADD COLUMN excluded INTEGER DEFAULT 0\")"
        new_mig = """await db_conn.execute("ALTER TABLE academy_students ADD COLUMN excluded INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                await db_conn.execute("ALTER TABLE academy_students ADD COLUMN sms_sent INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                await db_conn.execute("ALTER TABLE academy_students ADD COLUMN sms_sent_at TEXT")"""
        c = c.replace(old_mig, new_mig)

    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("main.py updated.")

def update_auth():
    with io.open('handlers/auth.py', 'r', encoding='utf-8') as f:
        c = f.read()

    if "'sms_'" not in c:
        c = c.replace(
            "elif start_arg.startswith('w2_'): click_source = 'WhatsApp 2'\n                elif start_arg.startswith('auth_'):",
            "elif start_arg.startswith('w2_'): click_source = 'WhatsApp 2'\n                elif start_arg.startswith('sms_'): click_source = 'SMS'\n                elif start_arg.startswith('auth_'):"
        )
        c = c.replace(
            "e1_|e2_|w1_|w2_)",
            "e1_|e2_|w1_|w2_|sms_)"
        )
        with io.open('handlers/auth.py', 'w', encoding='utf-8') as f:
            f.write(c)
        print("auth.py updated.")
    else:
        print("auth.py already has sms_")

update_main()
update_auth()
