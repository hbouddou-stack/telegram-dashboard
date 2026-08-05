import sqlite3

db_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\backup_bot.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get all subjects
c.execute('SELECT DISTINCT subject FROM questions WHERE theme IS NOT NULL AND theme != ""')
subjects = [row[0] for row in c.fetchall() if row[0]]

md_lines = []
md_lines.append("# Arborescence Proposée pour la Migration")
md_lines.append("\nVoici la structure extraite de vos anciennes thématiques textuelles. Si vous validez cette structure, le script créera ces dossiers et y placera automatiquement les questions correspondantes.\n")

for sub in subjects:
    if sub == 'fiqh':
        name = 'الفقه الميسر'
    elif sub == 'aqeeda':
        name = 'العقيدة'
    elif sub == 'sira':
        name = 'السيرة'
    elif sub == 'nahw':
        name = 'النحو'
    elif sub == 'tajweed':
        name = 'التجويد'
    else:
        name = sub

    md_lines.append(f"## 📚 {name} ({sub})")
    
    c.execute('SELECT DISTINCT course_number, course_name FROM questions WHERE subject = ? ORDER BY course_number', (sub,))
    courses = c.fetchall()
    
    for course_num, course_name in courses:
        title = course_name if course_name else f'الدرس {course_num}'
        md_lines.append(f"- **[Leçon {course_num}]** {title}")
        
        c.execute('SELECT DISTINCT theme FROM questions WHERE subject = ? AND course_number = ? AND theme IS NOT NULL AND theme != ""', (sub, course_num))
        themes = [r[0] for r in c.fetchall()]
        
        for th in themes:
            md_lines.append(f"  - 📂 {th}")
            
            c.execute('SELECT DISTINCT sub_theme FROM questions WHERE subject = ? AND course_number = ? AND theme = ? AND sub_theme IS NOT NULL AND sub_theme != ""', (sub, course_num, th))
            sub_themes = [r[0] for r in c.fetchall()]
            for sth in sub_themes:
                md_lines.append(f"    - 📄 {sth}")
                
    md_lines.append("\n---\n")

with open(r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\scratch\tree_export.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

print("Markdown tree generated.")
