import io
import re

with io.open('handlers/auth.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_regex = r"clean_sid = re.sub(r'^(auth_|src_email_|src_wa_|src_web_|token_)', '', start_arg)"
new_regex = r"""
                # Determine source for statistics
                click_source = "Lien Inconnu"
                if start_arg.startswith('e1_'): click_source = 'Email 1'
                elif start_arg.startswith('e2_'): click_source = 'Email 2'
                elif start_arg.startswith('w1_'): click_source = 'WhatsApp 1'
                elif start_arg.startswith('w2_'): click_source = 'WhatsApp 2'
                elif start_arg.startswith('auth_'): click_source = 'Admin Dashboard'
                
                clean_sid = re.sub(r'^(auth_|src_email_|src_wa_|src_web_|token_|e1_|e2_|w1_|w2_)', '', start_arg)"""

c = c.replace(old_regex, new_regex.lstrip('\n'))

old_update = r"await db.execute(\"UPDATE academy_students SET telegram_id = ?, telegram_username = ?, joined_at = ?, group_joined = 0, magic_token = ? WHERE student_id = ?\", (user_id, username, now_str, new_token, s_id))"
new_update = r"await db.execute(\"UPDATE academy_students SET telegram_id = ?, telegram_username = ?, joined_at = ?, group_joined = 0, magic_token = ?, last_click_source = ? WHERE student_id = ?\", (user_id, username, now_str, new_token, click_source, s_id))"

c = c.replace(old_update, new_update)

with io.open('handlers/auth.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Patched auth.py regex and source')
