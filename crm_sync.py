# -*- coding: utf-8 -*-
"""
crm_sync.py - Module de synchronisation et miroir de secours pour Oswah CRM.
Synchronise automatiquement chaque action et appel sur :
1. Un fichier local CSV persistant (data/crm_mirror_backup.csv)
2. La feuille Google Sheet miroir (1IR55QGybqsXG4Oxxg9OLdAWHQb4P3dbXBhGpfftv3rM)
   dans l'onglet unique avec entêtes en arabe 'Miroir_Interactions'.
"""
import os
import csv
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger("crm_sync")

BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BACKUP_CSV = os.path.join(BACKUP_DIR, "crm_mirror_backup.csv")
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")

# ID de la feuille Google Sheet Miroir fournie par l'utilisateur
DEFAULT_MIRROR_SHEET_ID = "1IR55QGybqsXG4Oxxg9OLdAWHQb4P3dbXBhGpfftv3rM"
MIRROR_TAB_NAME = "Miroir_Interactions"

os.makedirs(BACKUP_DIR, exist_ok=True)

CSV_HEADERS = [
    "التاريخ والوقت",
    "الرقم الأكاديمي",
    "الاسم الكامل",
    "رقم الهاتف",
    "البريد الإلكتروني",
    "الوكيل المسؤول",
    "نتيجة التواصل",
    "تفاصيل الموقف",
    "الخطوة التالية",
    "موعد المتابعة القادمة",
    "الملاحظات والتعليقات",
    "حالة السداد"
]

def _ensure_csv_headers():
    if not os.path.exists(BACKUP_CSV) or os.path.getsize(BACKUP_CSV) == 0:
        with open(BACKUP_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def append_local_csv(data: dict):
    try:
        _ensure_csv_headers()
        row = [
            data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("lead_id", ""),
            data.get("lead_name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("agent_name", ""),
            data.get("resultat", ""),
            data.get("detail", ""),
            data.get("prochaine_action", ""),
            data.get("date_prochaine", ""),
            data.get("note", ""),
            data.get("statut", "")
        ]
        with open(BACKUP_CSV, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        logger.info("[CRM_MIRROR] Action enregistree en local pour lead %s", data.get("lead_id"))
    except Exception as e:
        logger.error("[CRM_MIRROR] Erreur ecriture CSV local: %s", e)

async def get_mirror_sheet_id() -> str:
    sheet_id = os.getenv("CRM_MIRROR_SHEET_ID", "").strip()
    if sheet_id:
        return sheet_id
        
    try:
        import aiosqlite
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT value FROM settings WHERE key = 'crm_mirror_sheet_id'") as cur:
                row = await cur.fetchone()
                if row and row[0]:
                    return row[0].strip()
    except Exception as e:
        logger.debug("[CRM_MIRROR] Erreur lecture setting crm_mirror_sheet_id: %s", e)
        
    return DEFAULT_MIRROR_SHEET_ID

TAB_UNPAID = "المتابعات_والاتصالات"
TAB_PAID = "الطلاب_المسددون"

def _get_gspread_client():
    import json
    import gspread
    creds_env = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if os.path.exists(CREDENTIALS_FILE):
        return gspread.service_account(filename=CREDENTIALS_FILE)
    elif os.path.exists('credentials.json'):
        return gspread.service_account(filename='credentials.json')
    elif creds_env:
        try:
            creds_info = json.loads(creds_env)
            return gspread.service_account_from_dict(creds_info)
        except Exception as e:
            logger.error("[CRM_MIRROR] Erreur décodage GOOGLE_SERVICE_ACCOUNT_JSON: %s", e)
            return None
    logger.warning("[CRM_MIRROR] Aucune clé Google trouvée (ni credentials.json ni GOOGLE_SERVICE_ACCOUNT_JSON).")
    return None

def _sync_to_google_sheet_sync(sheet_id: str, row_data: list, lead_dict: dict = None):
    try:
        gc = _get_gspread_client()
        if not gc:
            return False

        sh = gc.open_by_key(sheet_id)
        
        try:
            ws_unpaid = sh.worksheet(TAB_UNPAID)
        except Exception:
            ws_unpaid = sh.get_worksheet(0)
            
        try:
            ws_paid = sh.worksheet(TAB_PAID)
        except Exception:
            ws_paid = None

        if not lead_dict:
            ws_unpaid.append_row(row_data)
            return True

        target_id = str(lead_dict.get("academic_id") or lead_dict.get("lead_id") or "").strip()
        statut = str(lead_dict.get("statut") or "").strip()
        is_paid = (statut in ('مسدد', 'Payé / Inscrit', 'Exempté'))

        res_summary = f"{lead_dict.get('resultat', '')} - {lead_dict.get('detail', '')}".strip(" -")
        next_act = lead_dict.get("prochaine_action") or "معاودة الاتصال"
        agent = lead_dict.get("agent_name", "")
        date_proch = lead_dict.get("date_prochaine", "")
        note = lead_dict.get("note", "")

        # Chercher dans la feuille des impayés (المتابعات_والاتصالات)
        cell = None
        if target_id:
            try:
                cell = ws_unpaid.find(target_id, in_column=1)
            except Exception as e_find:
                logger.debug("[CRM_MIRROR] Erreur recherche cellule ID %s: %s", target_id, e_find)

        if is_paid:
            if cell and ws_paid:
                row_num = cell.row
                existing_values = ws_unpaid.row_values(row_num)
                ws_unpaid.delete_rows(row_num)
                while len(existing_values) < 12:
                    existing_values.append("")
                if agent:
                    existing_values[5] = agent
                existing_values[6] = "مسدد"
                existing_values[7] = res_summary or "تم السداد"
                existing_values[8] = "مكتمل (مسدد)"
                existing_values[9] = date_proch
                existing_values[10] = f"{existing_values[10]} | {note}".strip(" |") if note else existing_values[10]
                existing_values[11] = "مسدد"
                ws_paid.append_row(existing_values)
                logger.info("[CRM_MIRROR] Lead %s déplacé vers الطلاب_المسددون", target_id)
            elif ws_paid:
                paid_row = [
                    target_id,
                    lead_dict.get("lead_name", ""),
                    lead_dict.get("phone", ""),
                    lead_dict.get("email", ""),
                    "",
                    agent,
                    "مسدد",
                    res_summary or "تم السداد",
                    "مكتمل (مسدد)",
                    date_proch,
                    note,
                    "مسدد"
                ]
                ws_paid.append_row(paid_row)
                logger.info("[CRM_MIRROR] Lead %s ajouté directement dans الطلاب_المسددون", target_id)
        else:
            if next_act in ['مكتمل', 'مكتمل (مسدد)']:
                next_act = 'معاودة الاتصال'
            if cell:
                row_num = cell.row
                updated_fields = [
                    agent,
                    statut or "مستمر",
                    res_summary,
                    next_act,
                    date_proch,
                    note
                ]
                ws_unpaid.update(f"F{row_num}:K{row_num}", [updated_fields])
                logger.info("[CRM_MIRROR] Ligne %s mise à jour pour lead %s dans %s", row_num, target_id, TAB_UNPAID)
            else:
                new_lead_row = [
                    target_id,
                    lead_dict.get("lead_name", ""),
                    lead_dict.get("phone", ""),
                    lead_dict.get("email", ""),
                    "",
                    agent,
                    statut or "جديد",
                    res_summary,
                    next_act,
                    date_proch,
                    note,
                    "غير مسدد"
                ]
                ws_unpaid.append_row(new_lead_row)
                logger.info("[CRM_MIRROR] Nouveau lead %s inséré dans %s", target_id, TAB_UNPAID)

        return True
    except Exception as e:
        logger.error("[CRM_MIRROR] Erreur ecriture Google Sheet Miroir: %s", e)
        return False

async def log_and_mirror_interaction(data: dict):
    append_local_csv(data)
    sheet_id = await get_mirror_sheet_id()
    if sheet_id:
        row = [
            data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("lead_id", ""),
            data.get("lead_name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("agent_name", ""),
            data.get("resultat", ""),
            data.get("detail", ""),
            data.get("prochaine_action", ""),
            data.get("date_prochaine", ""),
            data.get("note", ""),
            data.get("statut", "")
        ]
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, _sync_to_google_sheet_sync, sheet_id, row, data)
