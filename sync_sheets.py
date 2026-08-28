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
        
    headers = list(records[0].keys())
    def get_idx(*names):
        for name in names:
            for h in headers:
                if h and name.lower() in str(h).lower():
                    return h
        return None
        
    email_h = get_idx('email', 'mail', 'courriel', 'البريد')
    dob_h = get_idx('dob', 'naissance', 'birth', 'date', 'تاريخ', 'الميلاد')
    fn_h = get_idx('first', 'prenom', 'prénom', 'الاسم')
    ln_h = get_idx('last', 'nom', 'النسب', 'العائلي')
    year_h = get_idx('year', 'annee', 'année', 'level', 'niveau', 'سنة', 'مستوى')
    gender_h = get_idx('gender', 'genre', 'sexe', 'جنس')
    phone_h = get_idx('phone', 'tel', 'téléphone', 'هاتف', 'رقم')
    created_h = get_idx('horodateur', 'timestamp', 'inscription')
    
    if not email_h or not dob_h:
        if len(headers) >= 2:
            email_h = headers[0]
            dob_h = headers[1]
        else:
            raise Exception("Les colonnes Email et Date de Naissance sont introuvables.")
        
    imported = 0
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for row in records:
            email = str(row.get(email_h, '')).strip().lower()
            dob = str(row.get(dob_h, '')).strip()
            
            if not email or not dob:
                continue
                
            first_name = str(row.get(fn_h, '')).strip() if fn_h else ''
            last_name = str(row.get(ln_h, '')).strip() if ln_h else ''
            year = str(row.get(year_h, '')).strip() if year_h else '1'
            gender = str(row.get(gender_h, '')).strip().lower() if gender_h else 'homme'
            phone = str(row.get(phone_h, '')).strip() if phone_h else ''
            created_at = str(row.get(created_h, '')).strip() if created_h else ''
            
            async with db.execute("SELECT student_id FROM academy_students WHERE email = ?", (email,)) as cur:
                exists = await cur.fetchone()
                if exists:
                    await db.execute("""
                        UPDATE academy_students 
                        SET dob = ?, first_name = ?, last_name = ?, year = ?, gender = ?, source = ?, phone = ?, created_at = ?
                        WHERE email = ?
                    """, (dob, first_name, last_name, year, gender, 'google_sheets', phone, created_at, email))
                else:
                    await db.execute("""
                        INSERT INTO academy_students (email, dob, first_name, last_name, year, gender, source, phone, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (email, dob, first_name, last_name, year, gender, 'google_sheets', phone, created_at))
            imported += 1
        await db.commit()
    return imported
