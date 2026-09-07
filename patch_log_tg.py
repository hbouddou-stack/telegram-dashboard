import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = "elif action == 'log_wa_1' or action == 'log_wa_2':"
new = '''elif action == 'log_tg_1':
                await log_student_action(student_id, 'TELEGRAM_CONTACT', f"Contact Telegram direct ({action}) effectué.")
                
            elif action == 'log_wa_1' or action == 'log_wa_2':'''

if target in c:
    c = c.replace(target, new)
    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Patched main.py for TG')
else:
    print('Target not found')
