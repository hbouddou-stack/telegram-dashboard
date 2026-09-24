# -*- coding: utf-8 -*-
"""
crm_sync.py - Module de synchronisation et miroir de secours pour Oswah CRM.
Synchronise automatiquement chaque action et appel sur :
1. Un fichier local CSV persistant (data/crm_mirror_backup.csv)
2. La feuille Google Sheet miroir (1IR55QGybqsXG4Oxxg9OLdAWHQb4P3dbXBhGpfftv3rM)
   dans l'onglet dédié 'Miroir_Interactions'.
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
        
    return DEFAULT_MIRROR_SHEET_ID

def _sync_to_google_sheet_sync(sheet_id: str, row_data: list, lead_dict: dict = None):
    try:
        import gspread
        if not os.path.exists(CREDENTIALS_FILE):
            logger.warning("[CRM_MIRROR] credentials.json introuvable pour synchronisation Google Sheet.")
            return False

        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sh = gc.open_by_key(sheet_id)
        
        # 1. Écriture dans l'onglet Miroir_Interactions
        try:
            worksheet = sh.worksheet(MIRROR_TAB_NAME)
        except Exception:
            try:
                worksheet = sh.add_worksheet(title=MIRROR_TAB_NAME, rows=1000, cols=len(CSV_HEADERS))
                worksheet.append_row(CSV_HEADERS)
            except Exception:
                worksheet = sh.get_worksheet(0)
        
        existing = worksheet.row_values(1)
        if not existing:
            worksheet.append_row(CSV_HEADERS)
            
        worksheet.append_row(row_data)
        logger.info("[CRM_MIRROR] Ligne ajoutee avec succes sur Google Sheet Miroir (%s / %s)", sheet_id, MIRROR_TAB_NAME)

        # 2. Mise à jour facultative dans CRM_Leads si présent
        if lead_dict:
            try:
                ws_leads = sh.worksheet("CRM_Leads")
                lead_id_target = str(lead_dict.get("lead_id", "")).strip()
                if lead_id_target:
                    cell = ws_leads.find(lead_id_target)
                    if cell and cell.row > 1:
                        r_idx = cell.row
                        agent_val = lead_dict.get("agent_name", "")
                        resultat_val = f"{lead_dict.get('resultat', '')} • {lead_dict.get('detail', '')}".strip()
                        date_heure = lead_dict.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        updates = [
                            {"range": f"G{r_idx}", "values": [[agent_val]]},
                            {"range": f"J{r_idx}", "values": [[date_heure]]},
                            {"range": f"K{r_idx}", "values": [[resultat_val]]},
                            {"range": f"L{r_idx}", "values": [[lead_dict.get("prochaine_action", "")]]},
                            {"range": f"M{r_idx}", "values": [[lead_dict.get("date_prochaine", "")]]},
                        ]
                        if lead_dict.get("note"):
                            updates.append({"range": f"N{r_idx}", "values": [[lead_dict.get("note")]]})
                        ws_leads.batch_update(updates)
                        logger.info("[CRM_MIRROR] Lead #%s mis a jour dans CRM_Leads (ligne %s)", lead_id_target, r_idx)
            except Exception as e_up:
                logger.debug("[CRM_MIRROR] Note: Pas de mise a jour dans CRM_Leads: %s", e_up)

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
        loop.run_in_executor(None, _sync_to_google_sheet_sync, sheet_id, row, data)
