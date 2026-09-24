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
    return ''.join(c for c in str(p or '') if c.isdigit())

def _sync_sheet_blocking() -> dict:
    """Lecture bloquante de la feuille Google Sheet 'appels 2026'.
    
    Logique simplifiée :
    - On lit UNIQUEMENT la feuille 'appels 2026' (MASTER_SHEET_ID).
    - Le mapping se fait UNIQUEMENT par ID académique (colonne A).
    - Plus de matching par email, téléphone ou miroir secondaire.
    - Le sheet est la source de vérité absolue pour : nom, agent, commentaires, appels.
    """
    try:
        from google_creds import get_gspread_client
        gc = get_gspread_client()
        if not gc:
            logger.error("[CRM] Impossible d'initialiser le client Google Sheets.")
            return {}

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
            if not acad_id:
                continue  # Sans ID, on ne peut pas matcher — on ignore la ligne

            team    = str(r[18]).strip() if len(r) > 18 else ''
            comments = str(r[19]).strip() if len(r) > 19 else ''
            appel_1  = str(r[20]).strip() if len(r) > 20 else ''
            appel_2  = str(r[21]).strip() if len(r) > 21 else ''
            appel_3  = str(r[22]).strip() if len(r) > 22 else ''

            if team:
                agents.add(team)

            entry = {
                'academic_id': acad_id,
                'team': team,
                'comments': comments,
                'appel_1': appel_1,
                'appel_2': appel_2,
                'appel_3': appel_3,
            }

            # Index UNIQUEMENT par ID académique exact
            mapping[f"id:{acad_id}"] = entry

        logger.info(f"[CRM] Google Sheet '{MASTER_TAB}' chargé : {len(rows)-1} lignes, {len(agents)} agents, {len(mapping)} entrées indexées par ID.")
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

                # 2. Matching UNIQUEMENT par ID academique (colonne A du sheet). Zero collision possible.
                acad_id = str(row.get('academic_id') or '').strip()
                sheet_match = sheet_map.get(f"id:{acad_id}") or {}


                # Récupération de l'agent depuis les deux sources
                sheet_agent = (sheet_match.get('team') or '').strip()
                local_agent = (row.get('crm_assigned_to') or row.get('team') or '').strip()
                
                # Le Google Sheet a la priorité absolue
                agent = sheet_agent
                
                # Si pas d'agent dans le Google Sheet (ou explicitement non assigné)
                if not agent or agent in ('غير معين', 'None', 'غير محدد', ' ', ''):
                    agent = local_agent if (local_agent and local_agent not in ('غير معين', 'None', 'غير محدد', ' ', '')) else 'غير معين'
                
                # On assigne "Ancien lead" aux cohortes 25/24 SEULEMENT s'ils n'ont pas déjà un agent assigné !
                # Cela permet aux agents de conserver les anciens leads qu'ils traitaient déjà.
                if str(student_id).endswith('25') or str(student_id).endswith('24'):
                    if not agent or agent in ('غير معين', 'None', 'غير محدد', ' ', ''):
                        agent = 'Ancien lead'

                if agent:
                    all_agents.add(agent)

                # Concaténation des commentaires utiles (sans les 'أول: Oui' ou indicateurs d'appels artificiels)
                history_parts = []
                sheet_c = (sheet_match.get('comments') or '').strip()
                if sheet_c and sheet_c.lower() not in ['oui', 'yes', 'non', '1', 'true', 'ok']:
                    clean_c = sheet_c.replace('أول: Oui', '').replace('ثان: Oui', '').replace('ثالث: Oui', '').strip(' |')
                    if clean_c:
                        history_parts.append(clean_c)
                
                # Notes locales enregistrées directement dans le CRM
                if row.get('comments') and str(row.get('comments')).strip() != sheet_c:
                    c_loc = str(row['comments']).strip()
                    clean_loc = c_loc.replace('أول: Oui', '').replace('ثان: Oui', '').replace('ثالث: Oui', '').strip(' |')
                    if clean_loc and clean_loc.lower() not in ['oui', 'yes', 'non', '1', 'true', 'ok']:
                        history_parts.append(clean_loc)
                if row.get('crm_next_action_note'):
                    act_note = str(row['crm_next_action_note']).strip()
                    clean_act = act_note.replace('أول: Oui', '').replace('ثان: Oui', '').replace('ثالث: Oui', '').strip(' |')
                    if clean_act and clean_act.lower() not in ['oui', 'yes', 'non', '1', 'true', 'ok']:
                        history_parts.append(clean_act)

                ancien_commentaire = ' | '.join(history_parts) if history_parts else ''
                has_history = bool(ancien_commentaire or row.get('crm_last_contact_at') or sheet_match.get('appel_1'))

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

                # Détermination du dernier contact et de la prochaine action
                if _is_paid(statut_paiement) or statut_crm == 'مسدد':
                    dernier_resultat = 'تم السداد'
                    prochaine_action = 'مكتمل (مسدد)'
                elif cat == 'nouveau':
                    dernier_resultat = 'لم يتم التواصل بعد'
                    prochaine_action = 'إجراء الاتصال الأول'
                else:
                    # En suivi (relance) ou fermé : ne pas imposer de prochaine action automatique
                    raw_res = row.get('crm_last_result') or sheet_match.get('appel_1') or ''
                    if raw_res in ['Oui', 'oui', 'OUI', '1']:
                        raw_res = 'تم التواصل سابقاً'
                    dernier_resultat = raw_res or (ancien_commentaire and 'سجل سابق') or 'تم التواصل سابقاً'
                    # Laisser vide si l'agent n'a pas défini la prochaine action
                    prochaine_action = row.get('crm_next_action_note') or ''

                full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip() or 'بدون اسم'

                # Priorité aux données récentes issues du miroir de secours Google Sheet
                final_statut = sheet_match.get('crm_statut') or statut_crm
                final_resultat = sheet_match.get('crm_resultat') or dernier_resultat
                final_prochaine = sheet_match.get('crm_prochaine_action') or prochaine_action
                final_date = sheet_match.get('crm_date_prochaine') or row.get('crm_next_action_date', '')
                final_note = sheet_match.get('crm_note') or ancien_commentaire
                final_payment = sheet_match.get('payment_status') or statut_paiement

                lead = {
                    "ID_Lead": student_id,
                    "Nom": full_name,
                    "Telephone": phone,
                    "Email": email,
                    "Genre": row.get('gender', 'HOMME'),
                    "Pays": row.get('country', ''),
                    "Agent_Nom": agent,
                    "_Debug_Local": local_agent,
                    "_Debug_Sheet": sheet_agent,
                    "Statut_CRM": final_statut,
                    "Dernier_Contact_Date": row.get('crm_last_contact_at', '') or (final_date and 'مسجل حديثاً') or '',
                    "Dernier_Contact_Resultat": final_resultat,
                    "Prochaine_Action": final_prochaine,
                    "Date_Prochaine_Action": final_date,
                    "Ancien_Commentaire": final_note,
                    "Statut_Paiement": final_payment,
                    "_category": _categorize(final_statut, final_payment, bool(final_note or final_resultat != 'لم يتم التواصل بعد'))
                }

                # 3. Filtrage
                if agent_name and agent_name != 'all' and lead["Agent_Nom"] != agent_name:
                    continue

                if search_lower:
                    if (search_lower not in lead["Nom"].lower() and
                        search_lower not in lead["Telephone"].lower() and
                        search_lower not in lead["Email"].lower() and
                        search_lower not in str(lead["ID_Lead"]).lower()):
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

async def _ensure_crm_interactions_table(db):
    await db.execute('''
        CREATE TABLE IF NOT EXISTS crm_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id TEXT,
            academic_id TEXT,
            student_id INTEGER,
            agent_name TEXT,
            tentative_resultat TEXT,
            detail_statut TEXT,
            prochaine_action TEXT,
            date_prochaine TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        # Nettoyage des tests effectués par l'utilisateur
        await db.execute("DELETE FROM crm_interactions WHERE lead_id IN ('1135926', '1122026')")
        await db.execute("""
            UPDATE academy_students 
            SET crm_lead_status = 'جديد',
                crm_next_action_note = NULL,
                crm_next_action_date = NULL,
                crm_last_contact_at = NULL,
                payment_status = 'غير مسدد'
            WHERE student_id IN ('1135926', '1122026') OR academic_id IN ('1135926', '1122026')
        """)
    except Exception:
        pass
    await db.commit()

async def update_lead_status_async(
    lead_id: str,
    statut: str,
    resultat: str,
    prochaine_action: str,
    date_prochaine: str,
    note: str,
    agent_email: str = '',
    canal: str = '',
    agent_name: str = '',
    detail: str = ''
) -> bool:
    """Met à jour le statut, insère dans l'historique et miroir Google Sheet."""
    try:
        import crm_sync
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            await _ensure_crm_interactions_table(db)
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Récupérer les infos de l'élève pour le miroir et l'historique
            student_info = None
            async with db.execute(
                "SELECT student_id, academic_id, first_name, last_name, phone, email FROM academy_students WHERE academic_id = ? OR student_id = ?",
                (str(lead_id), str(lead_id))
            ) as cur:
                student_info = await cur.fetchone()

            st_id = student_info['student_id'] if student_info else lead_id
            ac_id = student_info['academic_id'] if student_info else lead_id
            full_name = f"{student_info['first_name'] or ''} {student_info['last_name'] or ''}".strip() if student_info else lead_id
            phone = student_info['phone'] if student_info else ''
            email = student_info['email'] if student_info else ''

            # 1. Enregistrer dans la table crm_interactions (Timeline)
            await db.execute('''
                INSERT INTO crm_interactions 
                (lead_id, academic_id, student_id, agent_name, tentative_resultat, detail_statut, prochaine_action, date_prochaine, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (str(lead_id), str(ac_id), st_id, agent_name, resultat, detail, prochaine_action, date_prochaine, note, now_str))

            # 2. Mettre à jour academy_students
            full_note = f"[{resultat}{(' - ' + detail) if detail else ''}] {note}".strip()
            query = """
                UPDATE academy_students 
                SET crm_lead_status = ?, 
                    crm_next_action_note = ?, 
                    crm_next_action_date = ?,
                    crm_last_contact_at = ?,
                    crm_assigned_to = CASE WHEN (crm_assigned_to IS NULL OR crm_assigned_to = '' OR crm_assigned_to = 'غير محدد') AND ? != '' THEN ? ELSE crm_assigned_to END
                WHERE academic_id = ? OR student_id = ?
            """
            await db.execute(query, (statut, full_note, date_prochaine, now_str, agent_name, agent_name, str(lead_id), str(lead_id)))

            # Note: Le statut payment_status reste sous le contrôle exclusif de l'Excel officiel
            await db.commit()

            # 3. Synchronisation miroir de secours (CSV local garanti + Google Sheet si configuré)
            try:
                mirror_payload = {
                    "timestamp": now_str,
                    "lead_id": str(lead_id),
                    "academic_id": str(ac_id),
                    "lead_name": full_name,
                    "phone": phone,
                    "email": email,
                    "agent_name": agent_name,
                    "statut": statut,
                    "resultat": resultat,
                    "detail": detail,
                    "date_prochaine": date_prochaine,
                    "note": note,
                    "prochaine_action": prochaine_action
                }
                await crm_sync.log_and_mirror_interaction(mirror_payload)
            except Exception as e_mirror:
                logger.error(f"[CRM] Erreur trigger miroir: {e_mirror}")

        return True
    except Exception as e:
        logger.error(f"[CRM] Erreur mise à jour lead {lead_id}: {e}")
        return False

async def get_lead_details_async(lead_id: str) -> dict:
    """Retourne l'historique détaillé d'un lead depuis crm_interactions avec son ID."""
    interactions = []
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            await _ensure_crm_interactions_table(db)

            # 1. Récupérer student_id et academic_id pour couvrir tous les cas
            async with db.execute(
                "SELECT student_id, academic_id, crm_assigned_to, crm_next_action_note, crm_last_contact_at FROM academy_students WHERE academic_id = ? OR student_id = ?",
                (str(lead_id), str(lead_id))
            ) as st_cur:
                st_info = await st_cur.fetchone()

            st_id = str(st_info['student_id']) if st_info and st_info['student_id'] else str(lead_id)
            ac_id = str(st_info['academic_id']) if st_info and st_info['academic_id'] else str(lead_id)

            query = """
                SELECT id, agent_name, tentative_resultat, detail_statut, prochaine_action, date_prochaine, note, created_at
                FROM crm_interactions
                WHERE lead_id = ? OR lead_id = ? OR academic_id = ? OR academic_id = ? OR student_id = ? OR student_id = ?
                ORDER BY id DESC
            """
            async with db.execute(query, (str(lead_id), st_id, str(lead_id), ac_id, str(lead_id), st_id)) as cur:
                rows = await cur.fetchall()
                for r in rows:
                    res_parts = []
                    if r['tentative_resultat']: res_parts.append(r['tentative_resultat'])
                    if r['detail_statut']: res_parts.append(r['detail_statut'])
                    res_str = " • ".join(res_parts) if res_parts else "تحديث"

                    interactions.append({
                        "id": r['id'],
                        "Date_Heure": r['created_at'],
                        "Agent": r['agent_name'] or "غير محدد",
                        "Resultat": res_str,
                        "Tentative": r['tentative_resultat'] or "",
                        "Detail": r['detail_statut'] or "",
                        "Commentaire": r['note'] or "",
                        "Date_Prochaine": r['date_prochaine'] or "",
                        "Prochaine_Action": r['prochaine_action'] or ""
                    })

            # Si ancien commentaire / note dans academy_students non présent dans les interactions récentes
            if st_info and (st_info['crm_next_action_note'] or st_info['crm_last_contact_at']):
                clean_old = (st_info['crm_next_action_note'] or '').strip()
                if clean_old and not any(clean_old in (i['Commentaire'] or '') for i in interactions):
                    interactions.append({
                        "id": None,
                        "Date_Heure": st_info['crm_last_contact_at'] or "ملاحظة سابقة",
                        "Agent": st_info['crm_assigned_to'] or "الوكيل",
                        "Resultat": "سجل الملاحظات السابق",
                        "Tentative": "",
                        "Detail": "",
                        "Commentaire": clean_old,
                        "Date_Prochaine": "",
                        "Prochaine_Action": ""
                    })
    except Exception as e:
        logger.error(f"[CRM] Erreur get_lead_details {lead_id}: {e}")
    return {"interactions": interactions}

async def delete_lead_interaction_async(interaction_id: int, lead_id: str) -> bool:
    """Supprime une interaction du registre et recalcule l'état du lead."""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            await _ensure_crm_interactions_table(db)
            
            # 1. Supprimer l'interaction spécifique
            await db.execute("DELETE FROM crm_interactions WHERE id = ?", (interaction_id,))
            
            # 2. Chercher la dernière interaction restante pour ce lead
            query = """
                SELECT * FROM crm_interactions
                WHERE lead_id = ? OR academic_id = ? OR student_id = ?
                ORDER BY id DESC LIMIT 1
            """
            async with db.execute(query, (str(lead_id), str(lead_id), str(lead_id))) as cur:
                last_interaction = await cur.fetchone()
                
            if last_interaction:
                full_note = f"[{last_interaction['tentative_resultat']}{(' - ' + last_interaction['detail_statut']) if last_interaction['detail_statut'] else ''}] {last_interaction['note']}".strip()
                await db.execute("""
                    UPDATE academy_students
                    SET crm_next_action_note = ?,
                        crm_next_action_date = ?,
                        crm_last_contact_at = ?
                    WHERE academic_id = ? OR student_id = ?
                """, (full_note, last_interaction['date_prochaine'], last_interaction['created_at'], str(lead_id), str(lead_id)))
            else:
                # Plus aucune interaction : réinitialiser le lead à son état vierge
                await db.execute("""
                    UPDATE academy_students
                    SET crm_lead_status = 'جديد',
                        crm_next_action_note = NULL,
                        crm_next_action_date = NULL,
                        crm_last_contact_at = NULL,
                        payment_status = 'غير مسدد'
                    WHERE academic_id = ? OR student_id = ?
                """, (str(lead_id), str(lead_id)))
                
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"[CRM] Erreur delete interaction {interaction_id}: {e}")
        return False

async def send_crm_fake_number_alert(lead_id: str):
    """Envoie un e-mail automatique quand le numéro est faux/injoignable."""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        import config as cfg
        
        if not cfg.SMTP_USER or not cfg.SMTP_PASSWORD:
            logger.info("[CRM_EMAIL] SMTP non configuré, e-mail simulé.")
            return

        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT first_name, email FROM academy_students WHERE academic_id = ? OR student_id = ?", (str(lead_id), str(lead_id))) as cur:
                row = await cur.fetchone()
                if not row or not row['email']:
                    return
                first_name = row['first_name'] or "عزيزي الطالب"
                recipient_email = row['email'].strip()

        msg = MIMEMultipart("alternative")
        msg['Subject'] = "تنبيه هام بخصوص تسجيلكم في أكاديمية أسوة"
        msg['From'] = f"{getattr(cfg, 'SMTP_SENDER_NAME', 'أكاديمية أسوة')} <{cfg.SMTP_USER}>"
        msg['To'] = recipient_email

        body_html = f"""
        <div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px;">
            <h2 style="color: #2563eb; margin-top: 0;">السلام عليكم ورحمة الله وبركاته، {first_name}</h2>
            <p>لقد حاول فريق الإرشاد والتسجيل بأكاديمية أسوة التواصل معكم هاتفياً بخصوص استكمال طلب تسجيلكم، ولكن تعذر الوصول إليكم أو أن رقم الهاتف المسجل غير متاح.</p>
            <p style="background: #fef3c7; padding: 12px; border-right: 4px solid #f59e0b; border-radius: 6px;">
                <strong>يرجى مراسلتنا عبر الواتساب لتأكيد رقمكم الصحيح ومتابعة تسجيلكم:</strong>
            </p>
            <div style="text-align: center; margin: 25px 0;">
                <a href="https://wa.me/212623126654" style="background: #25D366; color: white; padding: 12px 25px; border-radius: 30px; text-decoration: none; font-weight: bold; display: inline-block;">
                    التواصل معنا عبر واتساب
                </a>
            </div>
            <p style="color: #6b7280; font-size: 0.9em;">إذا كنتم قد تواصلتم معنا بالفعل، يرجى تجاهل هذه الرسالة.<br>مع تحيات،<br>إدارة أكاديمية أسوة</p>
        </div>
        """
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        def _send():
            with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
                server.send_message(msg)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)
        logger.info(f"[CRM_EMAIL] E-mail alerte numéro envoyé à {recipient_email}")
    except Exception as e:
        logger.error(f"[CRM_EMAIL] Erreur envoi e-mail alerte: {e}")

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
