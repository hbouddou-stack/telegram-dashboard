import sqlite3
import time

db_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\backup_bot.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

def get_or_create_program(subject, name):
    c.execute('SELECT id FROM programs WHERE subject = ?', (subject,))
    row = c.fetchone()
    if row:
        return row[0]
    c.execute('INSERT INTO programs (subject, name) VALUES (?, ?)', (subject, name))
    return c.lastrowid

def get_or_create_node(program_id, title, level, parent_id):
    # Depending on level, parent_id might be null
    if parent_id is None:
        c.execute('SELECT id FROM thematic_nodes WHERE program_id = ? AND title = ? AND level = ? AND parent_id IS NULL', (program_id, title, level))
    else:
        c.execute('SELECT id FROM thematic_nodes WHERE program_id = ? AND title = ? AND level = ? AND parent_id = ?', (program_id, title, level, parent_id))
    
    row = c.fetchone()
    if row:
        return row[0]
    
    # Needs insertion (columns: id, program_id, parent_id, level, title, order_index)
    c.execute('INSERT INTO thematic_nodes (program_id, parent_id, level, title, order_index) VALUES (?, ?, ?, ?, ?)',
              (program_id, parent_id, level, title, 0))
    return c.lastrowid

name_map = {'fiqh': 'الفقه الميسر', 'aqeeda': 'العقيدة', 'sira': 'السيرة', 'nahw': 'النحو', 'tajweed': 'التجويد'}

c.execute('SELECT DISTINCT subject FROM questions WHERE theme IS NOT NULL AND theme != ""')
subjects = [row[0] for row in c.fetchall() if row[0]]

questions_updated = 0

for sub in subjects:
    p_name = name_map.get(sub, sub)
    prog_id = get_or_create_program(sub, p_name)
    
    c.execute('SELECT DISTINCT course_number, course_name FROM questions WHERE subject = ? AND theme IS NOT NULL AND theme != ""', (sub,))
    courses = c.fetchall()
    
    for course_num, course_name in courses:
        c_title = course_name if course_name else f"الدرس {course_num}"
        l2_id = get_or_create_node(prog_id, c_title, 2, None)
        
        c.execute('SELECT DISTINCT theme FROM questions WHERE subject = ? AND course_number = ? AND theme IS NOT NULL AND theme != ""', (sub, course_num))
        themes = [r[0] for r in c.fetchall() if r[0]]
        
        for th in themes:
            l3_id = get_or_create_node(prog_id, th, 3, l2_id)
            
            c.execute('SELECT DISTINCT sub_theme FROM questions WHERE subject = ? AND course_number = ? AND theme = ?', (sub, course_num, th))
            sub_themes = [r[0] for r in c.fetchall()]
            
            for sth in sub_themes:
                if sth and sth.strip():
                    l4_id = get_or_create_node(prog_id, sth, 4, l3_id)
                    c.execute('''UPDATE questions SET thematic_node_id = ? 
                                 WHERE subject = ? AND course_number = ? AND theme = ? AND sub_theme = ?''',
                              (l4_id, sub, course_num, th, sth))
                    questions_updated += c.rowcount
                else:
                    c.execute('''UPDATE questions SET thematic_node_id = ? 
                                 WHERE subject = ? AND course_number = ? AND theme = ? AND (sub_theme IS NULL OR sub_theme = "")''',
                              (l3_id, sub, course_num, th))
                    questions_updated += c.rowcount

conn.commit()
print(f"Migration successful! Updated {questions_updated} questions.")
conn.close()
