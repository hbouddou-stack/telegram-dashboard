import io
import re

with io.open('main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

new_action_handler = '''async def api_admin_gateway_action(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    from database import log_student_action
    from datetime import datetime
    try:
        data = await request.json()
        action = data.get('action')
        student_id = data.get('student_id')
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM academy_students WHERE student_id = ?", (student_id,)) as cur:
                student = await cur.fetchone()
                
            if not student:
                return web.json_response({'success': False, 'error': 'Student not found'})
                
            if action == 'unlink':
                await db.execute("UPDATE academy_students SET telegram_id = NULL WHERE student_id = ?", (student_id,))
                await log_student_action(student_id, 'MANUAL_UNLINK', "L'administrateur a dissocié le compte manuellement.")
                
            elif action == 'send_email_1' or action == 'send_email_2':
                # Pour l'instant on utilise le template d'onboarding par défaut (à faire évoluer plus tard si on veut 2 templates différents)
                success, msg = await send_single_onboarding_email(student['email'], student['first_name'], student['student_id'], student['gender'])
                if success:
                    now_str = datetime.utcnow().isoformat()
                    await db.execute("UPDATE academy_students SET email_sent = 1, email_sent_at = ? WHERE student_id = ?", (now_str, student_id))
                    await log_student_action(student_id, 'EMAIL_SENT', f"Email de type {action} envoyé.")
                else:
                    return web.json_response({'success': False, 'error': msg})
                    
            elif action == 'log_wa_1' or action == 'log_wa_2':
                now_str = datetime.utcnow().isoformat()
                await db.execute("UPDATE academy_students SET whatsapp_sent = 1, whatsapp_sent_at = ? WHERE student_id = ?", (now_str, student_id))
                await log_student_action(student_id, 'WHATSAPP_SENT', f"Relance WhatsApp ({action}) effectuée.")
                
            await db.commit()
            
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})'''

# Replace old api_admin_gateway_action
old_action_handler_regex = re.compile(r'async def api_admin_gateway_action\(request: web\.Request\):.*?return web\.json_response\(\{\'success\': False, \'error\': str\(e\)\}\)', re.DOTALL)
main_code = old_action_handler_regex.sub(new_action_handler, main_code)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)
print("main.py patched successfully")
