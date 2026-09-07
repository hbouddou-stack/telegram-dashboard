import io

def get_new_logic():
    return """
            academic_id = str(row[0]).strip() if len(row) > 0 else ''
            first_name = str(row[2]).strip() if len(row) > 2 else ''
            email = str(row[3]).strip().lower() if len(row) > 3 else ''
            
            if not email or '@' not in email or email in ['email', 'بريد']:
                continue
                
            phone = str(row[4]).strip() if len(row) > 4 else ''
            year = str(row[5]).strip() if len(row) > 5 else '1'
            
            gender_raw = str(row[6]).upper().strip() if len(row) > 6 else ''
            gender = 'HOMME'
            if gender_raw in ["FEMME", "FEMALE", "FILLE", "F", "أنثى"]: gender = 'FEMME'
            elif gender_raw in ["HOMME", "MALE", "GARCON", "M", "ذكر"]: gender = 'HOMME'
            
            pay_raw = str(row[7]).upper().strip() if len(row) > 7 else ''
            payment_status = 'UNPAID'
            if pay_raw in ["PAID", "PAYE", "VALIDE", "CONFIRME", "مدفوع", "نعم"]: payment_status = 'PAID'
            
            country = str(row[8]).strip() if len(row) > 8 else ''
            dob = str(row[9]).strip() if len(row) > 9 else ''
            school_level = str(row[12]).strip() if len(row) > 12 else ''
            created_at_val = str(row[13]).strip() if len(row) > 13 else ''
            profession = str(row[14]).strip() if len(row) > 14 else ''
            last_name = str(row[15]).strip() if len(row) > 15 else ''
            nationality = str(row[16]).strip() if len(row) > 16 else ''
            arabic_level = str(row[17]).strip() if len(row) > 17 else ''
            
            if not academic_id:
                import hashlib
                academic_id = str(int(hashlib.md5(email.encode()).hexdigest()[:6], 16))[:6]
"""

# Patch sync_sheets.py
with io.open('sync_sheets.py', 'r', encoding='utf-8') as f:
    c = f.read()

start_marker = "            email = None\n            for cell in row:\n"
end_marker = "            if not academic_id:\n                academic_id = str(int(hashlib.md5(email.encode()).hexdigest()[:6], 16))[:6]"

if start_marker in c and end_marker in c:
    s_idx = c.find(start_marker)
    e_idx = c.find(end_marker) + len(end_marker)
    c = c[:s_idx] + get_new_logic() + c[e_idx:]
    
    # Update created_at in SQL
    c = c.replace("year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?, school_level = ?, source = 'google_sheets'",
                  "year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?, school_level = ?, created_at = COALESCE(NULLIF(?, ''), created_at), source = 'google_sheets'")
    c = c.replace("year, profession, country, nationality, arabic_level, school_level, email, academic_id",
                  "year, profession, country, nationality, arabic_level, school_level, created_at_val, email, academic_id")
    
    c = c.replace("datetime('now')", "COALESCE(NULLIF(?, ''), datetime('now'))")
    c = c.replace("arabic_level, school_level))", "arabic_level, school_level, created_at_val))")
    
    with io.open('sync_sheets.py', 'w', encoding='utf-8') as f:
        f.write(c)

# Patch main.py
def get_new_logic_main():
    return get_new_logic().replace("            ", "                ")

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

start_marker_main = "                email = None\n                for cell in row:\n"
end_marker_main = "                if not student_id:\n                    student_id = str(int(hashlib.md5(email.encode()).hexdigest()[:6], 16))[:6]"

if start_marker_main in c and end_marker_main in c:
    s_idx = c.find(start_marker_main)
    e_idx = c.find(end_marker_main) + len(end_marker_main)
    # student_id instead of academic_id in main
    logic_main = get_new_logic_main().replace("academic_id", "student_id")
    c = c[:s_idx] + logic_main + c[e_idx:]
    
    # Update created_at in SQL
    c = c.replace("year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?, school_level = ?, source = 'excel'",
                  "year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?, school_level = ?, created_at = COALESCE(NULLIF(?, ''), created_at), source = 'excel'")
    c = c.replace("year, profession, country, nationality, arabic_level, school_level, email, student_id",
                  "year, profession, country, nationality, arabic_level, school_level, created_at_val, email, student_id")
    
    c = c.replace("datetime('now')", "COALESCE(NULLIF(?, ''), datetime('now'))")
    c = c.replace("arabic_level, school_level, secrets.token_urlsafe(8))", "arabic_level, school_level, secrets.token_urlsafe(8), created_at_val)")
    
    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write(c)

print("Imports refactored and fixed")
