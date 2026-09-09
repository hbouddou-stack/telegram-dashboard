import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Fix the corruption in archive student
bad_block = """            )
            elif action == 'log_sms':
                now_str = datetime.utcnow().isoformat()
                await db.execute("UPDATE academy_students SET sms_sent = 1, sms_sent_at = ? WHERE student_id = ?", (now_str, student_id))
                await log_student_action(student_id, 'SMS_SENT', "Lien direct envoyé par SMS.")
                
            await db.commit()"""
            
good_block = """            )
            await db.commit()"""

c = "".join(lines)
c = c.replace(bad_block, good_block)

# 2. Find api_admin_gateway_action and insert the log_sms handler
action_def = "async def api_admin_gateway_action(request: web.Request):"
start_idx = c.find(action_def)
if start_idx != -1:
    end_idx = c.find("return web.json_response({'success': True})", start_idx)
    if end_idx != -1:
        commit_idx = c.rfind("await db.commit()", start_idx, end_idx)
        if commit_idx != -1:
            log_sms_code = """            elif action == 'log_sms':
                now_str = datetime.utcnow().isoformat()
                await db.execute("UPDATE academy_students SET sms_sent = 1, sms_sent_at = ? WHERE student_id = ?", (now_str, student_id))
                await log_student_action(student_id, 'SMS_SENT', "Lien direct envoyé par SMS.")
                
            """
            c = c[:commit_idx] + log_sms_code + c[commit_idx:]
            
with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("main.py fixed!")
