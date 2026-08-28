import gspread
import aiosqlite
import os
import json
from config import DATABASE_PATH

def get_gspread_client():
    creds_file = 'credentials.json'
    if os.path.exists(creds_file):
        return gspread.service_account(filename=creds_file)
    elif os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'):
        creds_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'))
        return gspread.service_account_from_dict(creds_info)
    else:
        raise Exception("Aucune clé Google (credentials.json) n'a été trouvée.")

async def run_google_sheets_sync(sheet_id: str):
    client = get_gspread_client()
    try:
        sheet = client.open_by_key(sheet_id).sheet1
    except gspread.exceptions.APIError as e:
        if "permission" in str(e).lower() or e.response.status_code in [403, 404]:
            raise Exception("Le bot n'a pas accès au fichier Google Sheets. Avez-vous bien partagé le fichier avec l'adresse e-mail du bot (en tant que Lecteur) ?")
        raise Exception(f"Erreur API Google: {e}")
    except Exception as e:
        if "PermissionError" in type(e).__name__:
            raise Exception("Le bot n'a pas accès au fichier Google Sheets. Vérifiez le partage.")
        raise
    
    records = sheet.get_all_records()
    if not records:
        return 0
        
    imported = 0
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for row_list in sheet.get_all_values()[1:]: # Skip header row
            if len(row_list) < 14:
                continue
                
            student_id = str(row_list[0]).strip() # Col A: الرقم الأكاديمي
            full_name = str(row_list[2]).strip()  # Col C: الإسم الكامل
            email = str(row_list[3]).strip().lower() # Col D: البريد الإلكتروني
            phone = str(row_list[4]).strip()      # Col E: رقم الهاتف
            year = str(row_list[5]).strip()       # Col F: المستوى
            gender = str(row_list[6]).strip().lower() # Col G: الجنس
            payment_status = str(row_list[7]).strip() # Col H: وضعية الحساب
            dob = str(row_list[9]).strip()        # Col J: تاريخ الميلاد
            created_at = str(row_list[13]).strip() # Col N: ﺗﺎرﻳﺦ اﻟﺘﺴﺠﻴﻞ
            
            if not email or not dob:
                continue
                
            parts = full_name.split(' ', 1)
            first_name = parts[0] if len(parts) > 0 else ''
            last_name = parts[1] if len(parts) > 1 else ''
            
            if not year: year = '1'
            if not gender: gender = 'homme'
            
            async with db.execute("SELECT student_id FROM academy_students WHERE email = ?", (email,)) as cur:
                exists = await cur.fetchone()
                if exists:
                    await db.execute("""
                        UPDATE academy_students 
                        SET dob = ?, first_name = ?, last_name = ?, year = ?, gender = ?, source = ?, phone = ?, created_at = ?, payment_status = ?
                        WHERE email = ?
                    """, (dob, first_name, last_name, year, gender, 'google_sheets', phone, created_at, payment_status, email))
                else:
                    try:
                        # Attempt to insert with the specific student_id from Sheets if it's a number
                        s_id_int = int(student_id)
                        await db.execute("""
                            INSERT INTO academy_students (student_id, email, dob, first_name, last_name, year, gender, source, phone, created_at, payment_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (s_id_int, email, dob, first_name, last_name, year, gender, 'google_sheets', phone, created_at, payment_status))
                    except ValueError:
                        # Fallback if student_id is not a valid integer
                        await db.execute("""
                            INSERT INTO academy_students (email, dob, first_name, last_name, year, gender, source, phone, created_at, payment_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (email, dob, first_name, last_name, year, gender, 'google_sheets', phone, created_at, payment_status))
            imported += 1
        await db.commit()
    return imported
