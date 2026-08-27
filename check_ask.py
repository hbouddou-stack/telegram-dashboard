import json
import re

with open(r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\dashboard\ask.html', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r"selectTheme\('([^']+)'\)", text)
print('HTML Themes:', matches)

js_keys = re.findall(r'"([^"]+)": \[', text)
print('JS Keys:', js_keys)
