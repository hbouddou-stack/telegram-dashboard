import io
with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for l in lines:
    if "student_id = s['student_id']" in l:
        new_lines.append(l)
        new_lines.append('                                note_text = "🔄 الهوية متغيرة في تيليجرام (Changement identite) :\\n" + "\\n".join(notes)\n')
        new_lines.append('                                await db_conn.execute(\n')
        new_lines.append('                                    "INSERT INTO student_logs (student_id, telegram_id, action_type, description, telegram_name, telegram_username) VALUES (?, ?, ?, ?, ?, ?)",\n')
        new_lines.append('                                    (student_id, telegram_id, "CRM_NOTE", f"[بواسطة: النظام - SYSTEM] [نوع: IDENTITE]\\n{note_text}", first_name, username)\n')
        new_lines.append('                                )\n')
        skip = True
        continue
    
    if skip:
        if 'await db_conn.commit()' in l:
            skip = False
            new_lines.append(l)
    else:
        new_lines.append(l)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
