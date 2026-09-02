import gspread
import aiosqlite
import os
import json
import secrets
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

                
            async with db.execute("SELECT student_id FROM academy_students WHERE LOWER(email) = ? OR student_id = ?", (email, academic_id)) as cur:
                exists = await cur.fetchone()
                
            if exists:
                await db.execute("""
                    UPDATE academy_students 
                    SET first_name = ?, last_name = ?, phone = ?, gender = ?, payment_status = ?, dob = ?, year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?, school_level = ?, created_at = COALESCE(NULLIF(?, ''), created_at), source = 'google_sheets'
                    WHERE LOWER(email) = ? OR student_id = ?
                """, (first_name, last_name, phone, gender, payment_status, dob, year, profession, country, nationality, arabic_level, school_level, created_at_val, email, academic_id))
            else:
                await db.execute("""
                    INSERT INTO academy_students (student_id, academic_id, first_name, last_name, email, phone, gender, payment_status, dob, year, profession, country, nationality, arabic_level, school_level, source, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'google_sheets', 1, COALESCE(NULLIF(?, ''), datetime('now')))
                """, (academic_id, academic_id, first_name, last_name, email, phone, gender, payment_status, dob, year, profession, country, nationality, arabic_level, school_level, created_at_val))
                
            imported += 1
        await db.commit()
    return imported


async def export_students_to_sheets(sheet_id: str):
    """Export student tracking data to a dedicated Google Sheet (2nd sheet tab)."""
    client = get_gspread_client()
    try:
        spreadsheet = client.open_by_key(sheet_id)
    except Exception as e:
        raise Exception(f"Erreur d'accès Google Sheets: {e}")

    # Use or create a sheet tab named "Suivi Élèves"
    try:
        sheet = spreadsheet.worksheet("Suivi Élèves")
    except Exception:
        sheet = spreadsheet.add_worksheet(title="Suivi Élèves", rows=1000, cols=15)

    # Fetch data from DB
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT s.first_name, s.last_name, s.email,
                   s.telegram_id, s.telegram_username,
                   u.first_name as tg_first_name,
                   s.email_sent_at, s.email_opened_at, s.email_clicked_at,
                   s.folder_clicked_at, s.group_joined, s.joined_at,
                   s.excluded
            FROM academy_students s
            LEFT JOIN users u ON u.telegram_id = s.telegram_id
            ORDER BY s.first_name ASC
        """) as cur:
            rows = await cur.fetchall()

    def yn(val, date_val=None):
        if val:
            return date_val or "✅"
        return "❌"

    def status_label(s):
        if s['excluded']:
            return "⚫ مُقصى"
        if s['group_joined']:
            return "🟢 في المجموعة"
        if s['email_clicked_at'] or s['folder_clicked_at']:
            return "🟠 تفاعل / لم ينضم بعد"
        return "🔴 لم ينضم بعد"

    headers = [
        "الاسم", "اللقب", "البريد الإلكتروني",
        "ID Telegram", "@Username", "اسم Telegram",
        "تاريخ استلام الإيميل", "تاريخ فتح الإيميل", "تاريخ الضغط على زر الإيميل",
        "تاريخ الضغط على زر المجلد", "انضم للمجموعة", "تاريخ الانضمام",
        "الحالة"
    ]

    data = [headers]
    for s in rows:
        s = dict(s)
        data.append([
            s.get('first_name') or '',
            s.get('last_name') or '',
            s.get('email') or '',
            str(s.get('telegram_id') or ''),
            ('@' + s['telegram_username']) if s.get('telegram_username') else '',
            s.get('tg_first_name') or '',
            s.get('email_sent_at') or '',
            s.get('email_opened_at') or '',
            s.get('email_clicked_at') or '',
            s.get('folder_clicked_at') or '',
            yn(s.get('group_joined')),
            s.get('joined_at') or '',
            status_label(s),
        ])

    sheet.clear()
    sheet.update(data, value_input_option='USER_ENTERED')
    return len(data) - 1
