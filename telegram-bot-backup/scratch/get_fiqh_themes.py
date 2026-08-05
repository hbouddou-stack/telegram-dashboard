import sqlite3
import json

db_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\backup_bot.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT DISTINCT theme FROM questions WHERE subject='fiqh' AND theme IS NOT NULL AND theme != ''")
themes = [r[0] for r in c.fetchall()]

c.execute("SELECT DISTINCT course_name FROM questions WHERE subject='fiqh' AND course_name IS NOT NULL AND course_name != ''")
courses = [r[0] for r in c.fetchall()]

data = {
    "themes": themes,
    "course_names": courses
}

with open(r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\scratch\fiqh_themes.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
