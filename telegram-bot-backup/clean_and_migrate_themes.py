import sqlite3

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
    if parent_id is None:
        c.execute('SELECT id FROM thematic_nodes WHERE program_id = ? AND title = ? AND level = ? AND parent_id IS NULL', (program_id, title, level))
    else:
        c.execute('SELECT id FROM thematic_nodes WHERE program_id = ? AND title = ? AND level = ? AND parent_id = ?', (program_id, title, level, parent_id))
    
    row = c.fetchone()
    if row:
        return row[0]
    
    c.execute('INSERT INTO thematic_nodes (program_id, parent_id, level, title, order_index) VALUES (?, ?, ?, ?, ?)',
              (program_id, parent_id, level, title, 0))
    return c.lastrowid

name_map = {'fiqh': 'الفقه الميسر', 'aqeeda': 'العقيدة', 'sira': 'السيرة', 'nahw': 'النحو', 'tajweed': 'التجويد'}

# 1. Nettoyage total
c.execute("DELETE FROM thematic_nodes")
c.execute("UPDATE questions SET thematic_node_id = NULL")

# 2. Récupérer les sujets uniques qui ont des thèmes
c.execute("SELECT DISTINCT subject FROM questions WHERE theme IS NOT NULL AND theme != ''")
subjects = [row[0] for row in c.fetchall() if row[0]]

questions_updated = 0

for sub in subjects:
    p_name = name_map.get(sub, sub)
    prog_id = get_or_create_program(sub, p_name)
    
    # Récupérer les thèmes uniques pour ce sujet
    c.execute("SELECT DISTINCT theme FROM questions WHERE subject = ? AND theme IS NOT NULL AND theme != ''", (sub,))
    themes = [r[0] for r in c.fetchall() if r[0]]
    
    for th in themes:
        # Exclusion des thèmes poubelles du fiqh
        if sub == 'fiqh' and th in ['عبادات', 'معاملات']:
            continue
            
        l2_id = get_or_create_node(prog_id, th, 2, None)
        
        # Récupérer les sous-thèmes pour ce thème
        c.execute("SELECT DISTINCT sub_theme FROM questions WHERE subject = ? AND theme = ?", (sub, th))
        sub_themes = [r[0] for r in c.fetchall()]
        
        has_sub_themes = False
        for sth in sub_themes:
            if sth and sth.strip():
                has_sub_themes = True
                l3_id = get_or_create_node(prog_id, sth, 3, l2_id)
                # Assigner les questions à ce sous-thème
                c.execute('''UPDATE questions SET thematic_node_id = ? 
                             WHERE subject = ? AND theme = ? AND sub_theme = ?''',
                          (l3_id, sub, th, sth))
                questions_updated += c.rowcount
                
        # Assigner les questions qui n'ont pas de sous-thème (ou si le thème n'a aucun sous-thème) au niveau 2 (Thème)
        c.execute('''UPDATE questions SET thematic_node_id = ? 
                     WHERE subject = ? AND theme = ? AND (sub_theme IS NULL OR sub_theme = "")''',
                  (l2_id, sub, th))
        questions_updated += c.rowcount

conn.commit()
print(f"Migration successful! Updated {questions_updated} questions with clean hierarchy.")
conn.close()
