import io
import re

with io.open('sync_sheets.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add new variables
c = c.replace("dob = ''\n            year = '1'", "dob = ''\n            year = '1'\n            profession = ''\n            country = ''\n            nationality = ''\n            arabic_level = ''")

# Add exact column extraction
injection = """if len(row) > 9 and not dob:
                d_val = str(row[9]).strip()
                if d_val and d_val.lower() not in ['dob', 'date de naissance']: dob = d_val
                
            if len(row) > 8:
                c_val = str(row[8]).strip()
                if c_val and c_val.lower() not in ['pays', 'country']: country = c_val
                
            if len(row) > 14:
                pro_val = str(row[14]).strip()
                if pro_val and pro_val.lower() not in ['profession', 'métier']: profession = pro_val
                
            if len(row) > 16:
                nat_val = str(row[16]).strip()
                if nat_val and nat_val.lower() not in ['nationalité', 'nationality']: nationality = nat_val
                
            if len(row) > 17:
                ar_val = str(row[17]).strip()
                if ar_val and ar_val.lower() not in ['niveau', 'arabe', 'arabic']: arabic_level = ar_val
"""
c = c.replace("if len(row) > 9 and not dob:\n                d_val = str(row[9]).strip()\n                if d_val and d_val.lower() not in ['dob', 'date de naissance']: dob = d_val", injection)

# Update the SQL queries
c = c.replace("SET first_name = ?, last_name = ?, phone = ?, gender = ?, payment_status = ?, dob = ?, year = ?, source = 'google_sheets'",
              "SET first_name = ?, last_name = ?, phone = ?, gender = ?, payment_status = ?, dob = ?, year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?, source = 'google_sheets'")
c = c.replace("(first_name, last_name, phone, gender, payment_status, dob, year, email, academic_id)",
              "(first_name, last_name, phone, gender, payment_status, dob, year, profession, country, nationality, arabic_level, email, academic_id)")

c = c.replace("gender, payment_status, dob, year, source, is_active, created_at)",
              "gender, payment_status, dob, year, profession, country, nationality, arabic_level, source, is_active, created_at)")
c = c.replace("?, ?, ?, ?, ?, ?, 'google_sheets', 1, datetime('now'))",
              "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'google_sheets', 1, datetime('now'))")
c = c.replace("email, phone, gender, payment_status, dob, year))",
              "email, phone, gender, payment_status, dob, year, profession, country, nationality, arabic_level))")

with io.open('sync_sheets.py', 'w', encoding='utf-8') as f:
    f.write(c)

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

# main.py API endpoint SELECT
c = c.replace("SELECT s.student_id, s.academic_id, s.first_name, s.last_name, s.email, s.telegram_id,",
              "SELECT s.student_id, s.academic_id, s.first_name, s.last_name, s.email, s.telegram_id, s.profession, s.country, s.nationality, s.arabic_level,")

# Add new variables
c = c.replace("dob = ''\n                year = '1'", "dob = ''\n                year = '1'\n                profession = ''\n                country = ''\n                nationality = ''\n                arabic_level = ''")

c = c.replace("if len(row) > 9 and not dob:\n                    d_val = str(row[9]).strip()\n                    if d_val and d_val.lower() not in ['dob', 'date de naissance']: dob = d_val", injection.replace("if len(row)", "    if len(row)"))

# Update SQL in main.py
c = c.replace("SET first_name = ?, last_name = ?, phone = ?, gender = ?, payment_status = ?, dob = ?, year = ?, source = 'excel'",
              "SET first_name = ?, last_name = ?, phone = ?, gender = ?, payment_status = ?, dob = ?, year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?, source = 'excel'")
c = c.replace("(first_name, last_name, phone, gender, payment_status, dob, year, email, student_id)",
              "(first_name, last_name, phone, gender, payment_status, dob, year, profession, country, nationality, arabic_level, email, student_id)")

c = c.replace("payment_status, dob, year, source, magic_token, is_active, created_at)",
              "payment_status, dob, year, profession, country, nationality, arabic_level, source, magic_token, is_active, created_at)")
c = c.replace("?, ?, ?, ?, ?, 'excel', ?, 1, datetime('now'))",
              "?, ?, ?, ?, ?, ?, ?, ?, ?, 'excel', ?, 1, datetime('now'))")
c = c.replace("email, phone, gender, payment_status, dob, year, secrets.token_urlsafe(8))",
              "email, phone, gender, payment_status, dob, year, profession, country, nationality, arabic_level, secrets.token_urlsafe(8))")

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("Done!")
