import io

for filepath in ['sync_sheets.py', 'main.py']:
    with io.open(filepath, 'r', encoding='utf-8') as f:
        c = f.read()

    # Add school_level variable
    c = c.replace("nationality = ''\n            arabic_level = ''", "nationality = ''\n            arabic_level = ''\n            school_level = ''")
    c = c.replace("nationality = ''\n                arabic_level = ''", "nationality = ''\n                arabic_level = ''\n                school_level = ''")

    # Add exact column matching for year (Col 5) and school_level (Col 12)
    injection = """if len(row) > 5:
                y_val = str(row[5]).strip()
                if y_val and y_val.lower() not in ['moustawa', 'مستوى', 'niveau', 'year']: year = y_val
                
            if len(row) > 12:
                sl_val = str(row[12]).strip()
                if sl_val and sl_val.lower() not in ['niveau scolaire', 'مستوى دراسي']: school_level = sl_val
                
            if len(row) > 8:"""
            
    injection_main = injection.replace("if len", "    if len").replace("y_val = str", "    y_val = str").replace("sl_val = str", "    sl_val = str").replace("if y_val", "    if y_val").replace("if sl_val", "    if sl_val")

    c = c.replace("if len(row) > 8:", injection)
    c = c.replace("    if len(row) > 8:", injection_main)
    
    # Also we must make sure year is not blindly extracted from heuristic
    # "if c in ["1", "2", "3", "4", "5", "6"] and not year:" => "if c in ["1", "2", "3", "4", "5", "6"] and year == '1':"
    # Actually just remove or let it be overridden by Col F. Col F runs FIRST! Wait, heuristic runs AFTER and might override?
    # Ah! The heuristic loop runs AFTER the exact column extraction.
    # In heuristic: `if c in ["1", "2", "3", "4", "5", "6"] and year == '1': year = c`
    # Let's fix that so it doesn't overwrite.
    c = c.replace('if c in ["1", "2", "3", "4", "5", "6"]:\n                    year = c', 'if c in ["1", "2", "3", "4", "5", "6"] and year == "1":\n                    year = c')
    c = c.replace('if c in ["1", "2", "3", "4", "5", "6"]:\n                    year = c\n                    continue', 'if c in ["1", "2", "3", "4", "5", "6"] and year == "1":\n                    year = c\n                    continue')

    # Add school_level to SQL
    if filepath == 'sync_sheets.py':
        c = c.replace("year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?", "year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?, school_level = ?")
        c = c.replace("year, profession, country, nationality, arabic_level, email, academic_id", "year, profession, country, nationality, arabic_level, school_level, email, academic_id")
        
        c = c.replace("year, profession, country, nationality, arabic_level, source, is_active", "year, profession, country, nationality, arabic_level, school_level, source, is_active")
        c = c.replace("?, ?, 'google_sheets'", "?, ?, ?, 'google_sheets'")
        c = c.replace("year, profession, country, nationality, arabic_level))", "year, profession, country, nationality, arabic_level, school_level))")
    else:
        # main.py API select
        c = c.replace("s.country, s.nationality, s.arabic_level,", "s.country, s.nationality, s.arabic_level, s.school_level,")
        # SQL
        c = c.replace("year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?", "year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?, school_level = ?")
        c = c.replace("year, profession, country, nationality, arabic_level, email, student_id", "year, profession, country, nationality, arabic_level, school_level, email, student_id")
        
        c = c.replace("year, profession, country, nationality, arabic_level, source, magic_token", "year, profession, country, nationality, arabic_level, school_level, source, magic_token")
        c = c.replace("?, 'excel', ?", "?, ?, 'excel', ?")
        c = c.replace("year, profession, country, nationality, arabic_level, secrets.token_urlsafe(8)", "year, profession, country, nationality, arabic_level, school_level, secrets.token_urlsafe(8)")

    with io.open(filepath, 'w', encoding='utf-8') as f:
        f.write(c)
        
print("Patched DB injection logic")
