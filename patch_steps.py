import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

target1 = 'await db.execute("UPDATE academy_students SET email_sent = 1, email_sent_at = ? WHERE student_id = ?", (now_str, student_id))'
repl1 = '''step_num = 1 if action == 'send_email_1' else 2
                    await db.execute("UPDATE academy_students SET email_sent = ?, email_sent_at = ? WHERE student_id = ?", (step_num, now_str, student_id))'''

target2 = 'await db.execute("UPDATE academy_students SET whatsapp_sent = 1, whatsapp_sent_at = ? WHERE student_id = ?", (now_str, student_id))'
repl2 = '''step_wa = 1 if action == 'log_wa_1' else 2
                  await db.execute("UPDATE academy_students SET whatsapp_sent = ?, whatsapp_sent_at = ? WHERE student_id = ?", (step_wa, now_str, student_id))'''

if target1 in c:
    c = c.replace(target1, repl1)
    print("Patched target1")
if target2 in c:
    c = c.replace(target2, repl2)
    print("Patched target2")

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
