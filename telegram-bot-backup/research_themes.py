import sqlite3
db_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\backup_bot.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM questions WHERE theme IS NOT NULL OR sub_theme IS NOT NULL')
print('Questions with text themes:', c.fetchone()[0])

c.execute('SELECT DISTINCT subject, course_number, theme FROM questions WHERE theme IS NOT NULL AND theme != ""')
print('Distinct themes (sample):', c.fetchall()[:10])

c.execute('SELECT DISTINCT subject, course_number, theme, sub_theme FROM questions WHERE sub_theme IS NOT NULL AND sub_theme != ""')
print('Distinct sub_themes (sample):', c.fetchall()[:10])
