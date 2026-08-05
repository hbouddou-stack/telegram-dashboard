import re

with open('.env', 'r', encoding='utf-8') as f:
    env = f.read()

# Mettre à jour WEBAPP_URL
env = re.sub(r'WEBAPP_URL=https://.*\.serveousercontent\.com', 'WEBAPP_URL=https://408a391a100886df-41-251-227-185.serveousercontent.com', env)

with open('.env', 'w', encoding='utf-8') as f:
    f.write(env)

print("Updated .env")

# Mettre à jour keyboards.py
with open('keyboards.py', 'r', encoding='utf-8') as f:
    js = f.read()

search = '''    if has_transcription:
        rows.append([InlineKeyboardButton(text="📝 قراءة التفريغ (PNG)", callback_data=f"rev_read_trans_start:{subject}:{lesson_num}")])
    else:'''

replace = '''    if has_transcription:
        rows.append([InlineKeyboardButton(text="📝 قراءة التفريغ (PNG)", callback_data=f"rev_read_trans_start:{subject}:{lesson_num}")])
        
        base_url = get_webapp_base_url()
        if base_url.startswith("https"):
            rows.append([InlineKeyboardButton(text="📖 وضع القراءة التفاعلي (Liseuse) 📱", web_app=WebAppInfo(url=f"{base_url}/reader.html?subject={subject}&lesson={lesson_num}"))])
    else:'''

if search in js:
    js = js.replace(search, replace)
    with open('keyboards.py', 'w', encoding='utf-8') as f:
        f.write(js)
    print("Updated keyboards.py successfully")
else:
    print("Could not find search string in keyboards.py")
