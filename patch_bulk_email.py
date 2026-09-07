import io
import re

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update run_email_dispatcher_task signature and body
old_dispatcher = r"async def run_email_dispatcher_task\(students_to_send\):(.*?)email_dispatch_state\[\"logs\"\].append\(f\"\[\{now_str\}\] .*?: \{email\}: \{err\}\"\)"
new_dispatcher = '''async def run_email_dispatcher_task(students_to_send, action_type="email_1"):
    global email_dispatch_state
    import aiosqlite
    from config import DATABASE_PATH
    import asyncio
    from datetime import datetime
    
    email_dispatch_state["is_running"] = True
    email_dispatch_state["total"] = len(students_to_send)
    email_dispatch_state["sent"] = 0
    email_dispatch_state["failed"] = 0
    email_dispatch_state["logs"] = []
    
    step_num = 1 if action_type == "email_1" else 2
    prefix = "e1" if action_type == "email_1" else "e2"
    
    for s in students_to_send:
        email = s.get('email', '').strip()
        first_name = s.get('first_name', '')
        sid = s.get('student_id', '')
        gender = s.get('gender', 'HOMME')
        
        email_dispatch_state["current_student"] = f"{first_name} ({email})"
        
        success, err = await send_single_onboarding_email(email, first_name, sid, gender, step_prefix=prefix)
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if success:
            email_dispatch_state["sent"] += 1
            email_dispatch_state["logs"].append(f"[{now_str}] Succès : {email}")
            # Mark in DB
            try:
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    await db.execute("UPDATE academy_students SET email_sent = ?, email_sent_at = ? WHERE student_id = ?", (step_num, now_str, sid))
                    await db.commit()
            except Exception:
                pass
        else:
            email_dispatch_state["failed"] += 1
            email_dispatch_state["logs"].append(f"[{now_str}] Echec {email}: {err}")'''

c = re.sub(old_dispatcher, new_dispatcher, c, flags=re.DOTALL)


# 2. Update api_admin_send_bulk_emails to accept filters and action_type
old_api = r"async def api_admin_send_bulk_emails\(request: web\.Request\):(.*?)return web\.json_response\(\{\"success\": False, \"error\": str\(e\)\}, status=500\)"
new_api = '''async def api_admin_send_bulk_emails(request: web.Request):
    global email_dispatch_state
    import aiosqlite
    from config import DATABASE_PATH
    import asyncio
    
    if email_dispatch_state["is_running"]:
        return web.json_response({"success": False, "error": "Un envoi est déjà en cours !"}, status=400)
        
    try:
        data = await request.json()
    except:
        data = {}
        
    action_type = data.get('action_type', 'email_1')
    target_ids = data.get('student_ids', [])
    
    if not target_ids:
        return web.json_response({"success": False, "error": "Aucun étudiant sélectionné."}, status=400)
        
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            placeholders = ','.join('?' for _ in target_ids)
            query = f"SELECT * FROM academy_students WHERE student_id IN ({placeholders})"
            async with db.execute(query, tuple(target_ids)) as cur:
                rows = await cur.fetchall()
                students = [dict(r) for r in rows]
                
        if not students:
            return web.json_response({"success": True, "count": 0, "message": "Aucun étudiant valide trouvé."})
            
        # Start background task
        asyncio.create_task(run_email_dispatcher_task(students, action_type))
        
        return web.json_response({"success": True, "count": len(students), "message": f"Envoi de {len(students)} emails en tâche de fond (Pause de 2s)."})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)'''

c = re.sub(old_api, new_api, c, flags=re.DOTALL)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Patched bulk email logic')
