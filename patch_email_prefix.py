import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update function signature
old_sig = 'async def send_single_onboarding_email(email, first_name, student_id, gender):'
new_sig = 'async def send_single_onboarding_email(email, first_name, student_id, gender, step_prefix="auth"):'
c = c.replace(old_sig, new_sig)

# 2. Update link inside function
old_link = 'direct_tg_link = f"https://t.me/{bot_username}?start=auth_{student_id}"'
new_link = 'direct_tg_link = f"https://t.me/{bot_username}?start={step_prefix}_{student_id}"'
c = c.replace(old_link, new_link)

# 3. Update call in send_bulk_emails (Default mass mailing via UI uses e1)
old_call1 = "success, err = await send_single_onboarding_email(email, first_name, sid, gender)"
new_call1 = 'success, err = await send_single_onboarding_email(email, first_name, sid, gender, step_prefix="e1")'
c = c.replace(old_call1, new_call1)

# 4. Update call in api_admin_gateway_action
old_call2 = "success, msg = await send_single_onboarding_email(student['email'], student['first_name'], student['student_id'], student['gender'])"
new_call2 = '''step_prefix = 'e1' if action == 'send_email_1' else 'e2'
                success, msg = await send_single_onboarding_email(student['email'], student['first_name'], student['student_id'], student['gender'], step_prefix=step_prefix)'''
c = c.replace(old_call2, new_call2)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Patched emails link prefixes')
