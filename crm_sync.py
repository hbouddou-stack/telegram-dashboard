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

def _sync_to_google_sheet_sync(sheet_id: str, row_data: list, lead_dict: dict = None):
    try:
        import gspread
        if not os.path.exists(CREDENTIALS_FILE):
            logger.warning("[CRM_MIRROR] credentials.json introuvable pour synchronisation Google Sheet.")
            return False

        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sh = gc.open_by_key(sheet_id)
        
        try:
            worksheet = sh.worksheet(MIRROR_TAB_NAME)
        except Exception:
            worksheet = sh.get_worksheet(0)
            
        worksheet.append_row(row_data)
        logger.info("[CRM_MIRROR] Ligne ajoutee avec succes sur Google Sheet Miroir (%s / %s)", sheet_id, MIRROR_TAB_NAME)
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
