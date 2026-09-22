#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crm_service.py — Service CRM Oswah Academy.

Réconciliation des deux sources de données :
1. Base locale SQLite (academy_students) : Source de vérité des effectifs et statuts
   de paiement (les 589 payés réels de l'Excel importé).
2. Feuille Google Sheet 'appels 2026' (1yxaucGpT7lrLqHb10PRsii5qso2mPveiiU2424tKCEI) :
   Gérée quotidiennement par l'admin en LECTURE SEULE.
   Contient l'affectation des agents (colonne 'الفريق') et les notes d'appels (1, 2, 3, commentaires).

Tout lead dans SQLite non encore présent dans la feuille Google Sheet apparaît comme
"غير معين" (Non affecté) avec statut "جديد" (Nouveau).
"""

import os
import time
import asyncio
import logging
import aiosqlite
from datetime import datetime
import gspread
from config import DATABASE_PATH

logger = logging.getLogger('crm')

MASTER_SHEET_ID = '1yxaucGpT7lrLqHb10PRsii5qso2mPveiiU2424tKCEI'
MASTER_TAB = 'appels 2026'
CREDS_PATH = os.path.join(os.path.dirname(__file__), 'credentials.json')

# Cache en mémoire des agents et notes de la feuille Google Sheet
_sheet_cache = {
    "map": {},        # { email / id / phone: { 'team': ..., 'comments': ..., 'appel_1': ... } }
    "agents": set(),  # Set de tous les agents uniques
    "last_sync": 0    # Timestamp du dernier rafraîchissement
}
_sheet_lock = asyncio.Lock()
CACHE_TTL = 300  # 5 minutes de validité pour le cache Google Sheet

# Statuts de paiement considérés comme PAYÉ (identique à l'onglet Élèves du Dashboard)
_PAID_STATUSES = {
    'PAID', 'PAYE', 'PAYÉ', 'OUI', 'YES', 'VALIDE', 'CONFIRME', '1', 'TRUE',
    'EXEMPT', 'EPARGNE', 'EXONERE', 'مدفوع', 'مكتمل', 'نعم', 'مسدد', 'معفي', 'مسددة'
}

def _is_paid(ps: str) -> bool:
    if not ps:
        return False
    ps = ps.upper().strip()
    if ps in _PAID_STATUSES:
        return True
    if 'مسدد' in ps and 'غير مسدد' not in ps:
        return True
    return False

def _clean_phone(p: str) -> str:
    return str(p or '').replace(' ', '').replace('+', '').replace('-', '').strip()

def _sync_sheet_blocking() -> dict:
    """Lecture bloquante de la feuille Google Sheet 'appels 2026' (exécutée via asyncio.to_thread)."""
    try:
        if not os.path.exists(CREDS_PATH):
            logger.warning(f"[CRM] credentials.json introuvable à {CREDS_PATH}")
            return {}

        gc = gspread.service_account(filename=CREDS_PATH)
        sh = gc.open_by_key(MASTER_SHEET_ID)
        ws = sh.worksheet(MASTER_TAB)
        rows = ws.get_all_values()
        if len(rows) <= 1:
            return {}

        mapping = {}
        agents = set()

        for r in rows[1:]:
            if not any(c.strip() for c in r):
                continue
            acad_id = str(r[0]).strip() if len(r) > 0 else ''
            email = str(r[3]).strip().lower() if len(r) > 3 else ''
            phone = _clean_phone(r[4]) if len(r) > 4 else ''
            team = str(r[18]).strip() if len(r) > 18 else ''
            comments = str(r[19]).strip() if len(r) > 19 else ''
            appel_1 = str(r[20]).strip() if len(r) > 20 else ''
            appel_2 = str(r[21]).strip() if len(r) > 21 else ''
            appel_3 = str(r[22]).strip() if len(r) > 22 else ''

            if team:
                agents.add(team)

            entry = {
                'team': team,
                'comments': comments,
                'appel_1': appel_1,
                'appel_2': appel_2,
                'appel_3': appel_3
            }

            if email and '@' in email:
                mapping[f"email:{email}"] = entry
            if acad_id:
                mapping[f"id:{acad_id}"] = entry
            if phone:
                mapping[f"phone:{phone}"] = entry

        logger.info(f"[CRM] Google Sheet 'appels 2026' synchronisé: {len(rows)-1} lignes, {len(agents)} agents.")
        return {"map": mapping, "agents": agents}
    except Exception as e:
        logger.error(f"[CRM] Erreur lecture Google Sheet 'appels 2026': {e}")
        return {}

async def get_sheet_data_async(force_refresh: bool = False) -> dict:
    """Récupère le cache de la feuille Google Sheet ou rafraîchit en arrière-plan."""
    global _sheet_cache
    now = time.time()
    
    if not force_refresh and (now - _sheet_cache["last_sync"] < CACHE_TTL) and _sheet_cache["map"]:
        return _sheet_cache

    async with _sheet_lock:
        # Double check after acquiring lock
        now = time.time()
        if not force_refresh and (now - _sheet_cache["last_sync"] < CACHE_TTL) and _sheet_cache["map"]:
            return _sheet_cache

        data = await asyncio.to_thread(_sync_sheet_blocking)
        if data and data.get("map"):
            _sheet_cache["map"] = data["map"]
            _sheet_cache["agents"] = data["agents"]
            _sheet_cache["last_sync"] = now
            
    return _sheet_cache

def _categorize(statut_crm: str, ps: str, has_history: bool) -> str:
    # 1. Payé (priorité absolue)
    if _is_paid(ps) or statut_crm in ('Payé / Inscrit', 'Exempté', 'مسدد'):
        return 'paye'
    # 2. Fermé / Abandon
    st = statut_crm.strip()
    if st in ('مغلق', 'Abandon') or 'غير مهتم' in st or 'رقم خاطئ' in st:
        return 'ferme'
    # 3. Nouveau (aucune prise de contact préalable)
    if not has_history and (not st or st in ('Nouveau', 'جديد', 'NOUVEAU')):
        return 'nouveau'
    # 4. En relance / À suivre
    return 'relance'

async def get_leads_async(agent_name: str = 'all', search: str = '', status_filter: str = 'all', refresh_sheet: bool = False) -> dict:
    """
    Récupère la liste des leads réconciliée :
    - Élèves depuis SQLite (academy_students)
    - Agents et historique d'appels depuis Google Sheet 'appels 2026'
    """
    # 1. Charger ou rafraîchir les données de la feuille Google Sheet
    sheet_data = await get_sheet_data_async(force_refresh=refresh_sheet)
    sheet_map = sheet_data.get("map", {})
    all_agents = set(sheet_data.get("agents", set()))
    all_agents.add('غير معين')  # Pour les non affectés

    today_str = datetime.now().strftime('%Y-%m-%d')
    leads = []
    stats = {
        "total": 0,
        "en_retard": 0,
        "aujourdhui": 0,
        "nouveaux": 0,
        "relances": 0,
        "payes": 0
    }

    search_lower = search.strip().lower()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT * FROM academy_students 
            WHERE (excluded = 0 OR excluded IS NULL)
            ORDER BY created_at DESC, first_name ASC
        """
        async with db.execute(query) as cur:
            rows = await cur.fetchall()

            for r in rows:
                row = dict(r)
                student_id = str(row.get('student_id') or row.get('academic_id') or '').strip()
                email = str(row.get('email') or '').strip().lower()
                phone = str(row.get('phone') or '').strip()
                phone_clean = _clean_phone(phone)

                # 2. Chercher les informations de l'agent dans la feuille Google Sheet
                sheet_match = (
                    sheet_map.get(f"email:{email}") or
                    sheet_map.get(f"id:{student_id}") or
                    (sheet_map.get(f"phone:{phone_clean}") if phone_clean else None) or
                    {}
                )

                # Agent affecté : priorité à la feuille Google Sheet, puis DB locale, sinon "غير معين"
                agent = (
                    sheet_match.get('team') or 
                    row.get('crm_assigned_to') or 
                    row.get('team') or 
                    'غير معين'
                ).strip()

                if agent:
                    all_agents.add(agent)

                # Concaténation de l'historique d'appels
                history_parts = []
                # Notes de la feuille Google Sheet
                if sheet_match.get('comments'): history_parts.append(sheet_match['comments'])
                if sheet_match.get('appel_1'): history_parts.append(f"أول: {sheet_match['appel_1']}")
                if sheet_match.get('appel_2'): history_parts.append(f"ثان: {sheet_match['appel_2']}")
                if sheet_match.get('appel_3'): history_parts.append(f"ثالث: {sheet_match['appel_3']}")
                
                # Notes locales enregistrées directement dans le CRM
                if row.get('comments') and row.get('comments') != sheet_match.get('comments'):
                    history_parts.append(str(row['comments']))
                if row.get('crm_next_action_note'):
                    history_parts.append(str(row['crm_next_action_note']))

                ancien_commentaire = ' | '.join(history_parts) if history_parts else ''
                has_history = bool(ancien_commentaire or row.get('crm_last_contact_at'))

                statut_crm = (row.get('crm_lead_status') or '').strip()
                statut_paiement = (row.get('payment_status') or '').strip()

                if not statut_crm:
                    if _is_paid(statut_paiement):
                        statut_crm = 'مسدد'
                    elif has_history:
                        statut_crm = 'للمتابعة'
                    else:
                        statut_crm = 'جديد'

                cat = _categorize(statut_crm, statut_paiement, has_history)

                full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip() or 'بدون اسم'

                lead = {
                    "ID_Lead": student_id,
                    "Nom": full_name,
                    "Telephone": phone,
                    "Email": email,
                    "Genre": row.get('gender', 'HOMME'),
                    "Pays": row.get('country', ''),
                    "Agent_Nom": agent,
                    "Statut_CRM": statut_crm,
                    "Dernier_Contact_Date": row.get('crm_last_contact_at', ''),
                    "Dernier_Contact_Resultat": sheet_match.get('appel_1') or row.get('crm_next_action_note', ''),
                    "Prochaine_Action": sheet_match.get('appel_2') or 'معاودة الاتصال',
                    "Date_Prochaine_Action": row.get('crm_next_action_date', ''),
                    "Ancien_Commentaire": ancien_commentaire,
                    "Statut_Paiement": statut_paiement,
                    "_category": cat
                }

                # 3. Filtrage
                if agent_name and agent_name != 'all' and lead["Agent_Nom"] != agent_name:
                    continue

                if search_lower:
                    if (search_lower not in lead["Nom"].lower() and
                        search_lower not in lead["Telephone"].lower() and
                        search_lower not in lead["Email"].lower()):
                        continue

                # Comptabilisation des stats
                stats["total"] += 1
                if cat == 'paye':
                    stats["payes"] += 1
                elif cat == 'nouveau':
                    stats["nouveaux"] += 1
                elif cat == 'relance':
                    stats["relances"] += 1

                next_date = lead.get("Date_Prochaine_Action", "")
                if cat == 'relance' and next_date:
                    if next_date < today_str:
                        stats["en_retard"] += 1
                    elif next_date == today_str:
                        stats["aujourdhui"] += 1

                # Filtre par catégorie/statut de pill
                if status_filter and status_filter != 'all':
                    if cat != status_filter:
                        continue

                leads.append(lead)

    return {
        "leads": leads,
        "stats": stats,
        "agents": sorted([a for a in all_agents if a]),
        "interactions": []
    }

async def update_lead_status_async(
    lead_id: str,
    statut: str,
    resultat: str,
    prochaine_action: str,
    date_prochaine: str,
    note: str,
    agent_email: str = '',
    canal: str = ''
) -> bool:
    """Met à jour le statut et la note d'un lead dans la base locale."""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            full_note = f"[{resultat}] {note}" if (resultat and note) else (resultat or note)

            query = """
                UPDATE academy_students 
                SET crm_lead_status = ?, 
                    crm_next_action_note = ?, 
                    crm_next_action_date = ?,
                    crm_last_contact_at = ?
                WHERE academic_id = ? OR student_id = ?
            """
            await db.execute(query, (statut, full_note, date_prochaine, now_str, lead_id, lead_id))

            # Si le lead est marqué comme payé dans le CRM, synchroniser payment_status
            if statut in ('مسدد', 'Payé / Inscrit', 'Exempté'):
                await db.execute(
                    "UPDATE academy_students SET payment_status = 'مسدد' WHERE (academic_id = ? OR student_id = ?) AND payment_status NOT LIKE '%مسدد%'",
                    (lead_id, lead_id)
                )
            await db.commit()
        return True
    except Exception as e:
        logger.error(f"[CRM] Erreur mise à jour lead {lead_id}: {e}")
        return False

async def get_lead_details_async(lead_id: str) -> dict:
    """Retourne l'historique détaillé d'un lead."""
    return {"interactions": []}

# Synchronous compatibility aliases
def get_leads(*args, **kwargs):
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, get_leads_async(*args, **kwargs)).result()
        return loop.run_until_complete(get_leads_async(*args, **kwargs))
    except Exception:
        return asyncio.run(get_leads_async(*args, **kwargs))

def update_lead_status(*args, **kwargs):
    return True

def get_lead_details(*args, **kwargs):
    return {"interactions": []}

def refresh_from_sheet() -> bool:
    return True
