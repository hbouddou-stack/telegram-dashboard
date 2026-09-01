import gspread
import aiosqlite
import os
import json
import re
import hashlib
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
    except Exception as e:
        raise Exception(f"Erreur d'accès Google Sheets: {e}")
    
    all_values = sheet.get_all_values()
    if not all_values:
        return 0
        
    imported = 0
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for row in all_values[1:]:
            if not any(row):
                continue
                
            email = None
            for cell in row:
                c = str(cell).strip().lower()
                if '@' in c and '.' in c and len(c) > 5:
                    email = c
                    break
                    
            if not email or email.startswith('email') or email.startswith('mail') or email.startswith('البريد'):
                continue
                
            first_name = 'طالب'
            last_name = ''
            phone = ''
            gender = 'HOMME'
            payment_status = 'PAID'
            academic_id = ''
            dob = ''
            year = '1'
            created_at = ''
            
            # Row-level cell scanning
            text_candidates = []
            for cell in row:
                c = str(cell).strip()
                if not c or c.lower() == email:
                    continue
                c_up = c.upper()
                if any(k in c_up for k in ['FEMME', 'FEMALE', 'أنث', 'نساء', 'F']):
                    gender = 'FEMME'
                    continue
                elif any(k in c_up for k in ['HOMME', 'MALE', 'ذك', 'رجال', 'M']):
                    gender = 'HOMME'
                    continue
                if any(k in c_up for k in ['UNPAID', 'NON', 'ATTENTE', 'PENDING', 'غير مدفوع']):
                    payment_status = 'UNPAID'
                    continue
                if (c.startswith('+') or (c.isdigit() and len(c) >= 9 and len(c) <= 15)) and not phone:
                    phone = c
                    continue
                if (c.isdigit() and len(c) >= 4 and len(c) <= 8) and not academic_id:
                    academic_id = c
                    continue
                if len(c) >= 2 and not any(ch.isdigit() for ch in c):
                    text_candidates.append(c)
                    
            if text_candidates:
                if len(text_candidates) == 1:
                    parts = text_candidates[0].split(None, 1)
                    first_name = parts[0]
                    last_name = parts[1] if len(parts) > 1 else ''
                else:
                    first_name = text_candidates[0]
                    last_name = ' '.join(text_candidates[1:])
                    
            if not academic_id:
                academic_id = str(int(hashlib.md5(email.encode()).hexdigest()[:6], 16))[:6]
                
            async with db.execute("SELECT student_id FROM academy_students WHERE LOWER(email) = ? OR student_id = ?", (email, academic_id)) as cur:
                exists = await cur.fetchone()
                
            if exists:
                await db.execute("""
                    UPDATE academy_students 
                    SET first_name = ?, last_name = ?, phone = ?, gender = ?, payment_status = ?, dob = ?, year = ?, source = 'google_sheets'
                    WHERE LOWER(email) = ? OR student_id = ?
                """, (first_name, last_name, phone, gender, payment_status, dob, year, email, academic_id))
            else:
                await db.execute("""
                    INSERT INTO academy_students (student_id, academic_id, first_name, last_name, email, phone, gender, payment_status, dob, year, source, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'google_sheets', 1, datetime('now'))
                """, (academic_id, academic_id, first_name, last_name, email, phone, gender, payment_status, dob, year))
                
            imported += 1
        await db.commit()
    return imported
