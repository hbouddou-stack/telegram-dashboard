# -*- coding: utf-8 -*-
"""
crm_sync.py - Module de synchronisation et miroir de secours pour Oswah CRM.
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

os.makedirs(BACKUP_DIR, exist_ok=True)

CSV_HEADERS = [
    "Date_Heure",
    "ID_Lead",
    "Nom",
    "Telephone",
    "Email",
    "Agent",
    "Resultat",
    "Detail_Statut",
    "Date_Prochaine",
    "Notes",
    "Prochaine_Action"
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
            data.get("date_prochaine", ""),
            data.get("note", ""),
            data.get("prochaine_action", "")
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
        
    return ""

def _sync_to_google_sheet_sync(sheet_id: str, row_data: list):
    try:
        import gspread
        if not os.path.exists(CREDENTIALS_FILE):
            logger.warning("[CRM_MIRROR] credentials.json introuvable pour synchronisation Google Sheet.")
            return False

        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0)
        
        existing = worksheet.row_values(1)
        if not existing:
            worksheet.append_row(CSV_HEADERS)
            
        worksheet.append_row(row_data)
        logger.info("[CRM_MIRROR] Ligne ajoutee avec succes sur Google Sheet Miroir (%s)", sheet_id)
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
            data.get("date_prochaine", ""),
            data.get("note", ""),
            data.get("prochaine_action", "")
        ]
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, _sync_to_google_sheet_sync, sheet_id, row)
