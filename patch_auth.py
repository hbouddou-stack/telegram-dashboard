import io

with io.open('handlers/auth.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''                    await log_student_action(0, 'INVALID_LINK_ATTEMPT', f"محاولة رابط غير صالح: {start_arg}", telegram_id=user_id, telegram_name=first_name, telegram_username=username)'''
replacement = target + '''
                    try:
                        from config import TELEGRAM_SUPPORT_GROUP_ID
                        await message.bot.send_message(
                            TELEGRAM_SUPPORT_GROUP_ID,
                            f"🚨 <b>تنبيه أمني: محاولة دخول غير مصرح بها</b>\\n\\n"
                            f"الرابط المستخدم: <code>{start_arg}</code>\\n"
                            f"الشخص: {first_name} (@{username})\\n"
                            f"ID: <code>{user_id}</code>",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print("Alert error:", e)'''

if target in c:
    c = c.replace(target, replacement)
    with io.open('handlers/auth.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Patched auth.py alert')
else:
    print('Target not found in auth.py')
