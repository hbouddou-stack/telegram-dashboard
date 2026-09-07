import io
with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'note_text = "' in l and 'Changement identite' in l:
        # Reconstruct the line properly
        lines[i] = '                                note_text = "🔄 الهوية متغيرة في تيليجرام (Changement identite) :\\n" + "\\n".join(notes)\n'
    if 'f"[بواسطة' in l and 'IDENTITE' in l:
        lines[i] = '                                    (student_id, telegram_id, "CRM_NOTE", f"[بواسطة: النظام - SYSTEM] [نوع: IDENTITE]\\n{note_text}", first_name, username)\n'

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
