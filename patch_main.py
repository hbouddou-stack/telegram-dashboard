import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''                        if current_first_name and real_first_name.lower() not in current_first_name.lower():
                            await log_student_action(student_id, 'NAME_VIOLATION_DETECTED', f'Prénom actuel: {current_first_name}')
                            try:
                                await bot.send_message(telegram_id, f'⚠️ Attention ! Ton prénom Telegram actuel est "{current_first_name}". Tu dois impérativement utiliser ton vrai prénom "{real_first_name}". Merci de le modifier dans tes paramètres Telegram.')
                            except Exception:
                                pass'''
if target in c:
    c = c.replace(target, '# Name enforcement disabled per user request')
    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Patched main.py")
else:
    print("Target not found")
