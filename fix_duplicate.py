import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

bad_block = """            elif action == 'log_sms':
                now_str = datetime.utcnow().isoformat()
                await db.execute("UPDATE academy_students SET sms_sent = 1, sms_sent_at = ? WHERE student_id = ?", (now_str, student_id))
                await log_student_action(student_id, 'SMS_SENT', "Lien direct envoyé par SMS.")
                
                        elif action == 'log_sms':
                now_str = datetime.utcnow().isoformat()
                await db.execute("UPDATE academy_students SET sms_sent = 1, sms_sent_at = ? WHERE student_id = ?", (now_str, student_id))
                await log_student_action(student_id, 'SMS_SENT', "Lien direct envoyé par SMS.")
                
            await db.commit()"""
            
good_block = """            elif action == 'log_sms':
                now_str = datetime.utcnow().isoformat()
                await db.execute("UPDATE academy_students SET sms_sent = 1, sms_sent_at = ? WHERE student_id = ?", (now_str, student_id))
                await log_student_action(student_id, 'SMS_SENT', "Lien direct envoyé par SMS.")
                
            await db.commit()"""

c = c.replace(bad_block, good_block)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("Duplicate log_sms fixed!")
