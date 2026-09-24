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
    from google_creds import get_gspread_client
    import aiosqlite
    
    # 1. Lecture DIRECTE depuis Google Sheets (Source de verite des eleves)
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key('1yxaucGpT7lrLqHb10PRsii5qso2mPveiiU2424tKCEI')
        ws = sh.worksheet('appels 2026')
        all_rows = ws.get_all_values()
    except Exception as e:
        logger.error(f"Google Sheet fetch error: {e}")
        return {"data": [], "stats": {}, "agents": {}, "interactions": {}}
        
    # 2. Lecture de la Memoire CRM (SQLite)
    db_status_map = {}
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT academic_id, crm_lead_status, crm_next_action_note FROM academy_students WHERE crm_lead_status IS NOT NULL") as cur:
                rows = await cur.fetchall()
                for r in rows:
                    if r['academic_id']:
                        db_status_map[str(r['academic_id']).strip()] = r
    except Exception as e:
        logger.error(f"CRM SQLite fetch error: {e}")
        
    leads = []
    agent_counts = {}
    stats = {'total': 0, 'nouveau': 0, 'en_cours': 0, 'paye': 0, 'ferme': 0}
    interactions_stats = {'today': 0, 'week': 0, 'month': 0}
    
    for row in all_rows[1:]:
        if not row: continue
        student_id = str(row[0]).strip() if len(row) > 0 else ''
        if not student_id: continue
        
        first_name = str(row[2]).strip() if len(row) > 2 else ''
        last_name = str(row[15]).strip() if len(row) > 15 else ''
        full_name = f"{first_name} {last_name}".strip()
        
        email = str(row[3]).strip() if len(row) > 3 else ''
        phone = str(row[4]).strip() if len(row) > 4 else ''
        gender = str(row[6]).strip() if len(row) > 6 else 'HOMME'
        country = str(row[8]).strip() if len(row) > 8 else ''
        payment_status = str(row[7]).strip() if len(row) > 7 else ''
        
        agent = str(row[18]).strip() if len(row) > 18 else ''
        if not agent:
            agent = "Non assigné"
            
        gs_comment = str(row[19]).strip() if len(row) > 19 else ''
        appel_1 = str(row[20]).strip() if len(row) > 20 else ''
        appel_2 = str(row[21]).strip() if len(row) > 21 else ''
        appel_3 = str(row[22]).strip() if len(row) > 22 else ''
        
        # 3. STATUT INTELLIGENT (Croisement GS + CRM Memoire)
        is_paid = _is_paid(payment_status) or payment_status.lower() in ['payé / inscrit', 'exempté', 'validé']
        
        db_record = db_status_map.get(student_id)
        crm_status = db_record['crm_lead_status'] if db_record else ''
        crm_note = (db_record['crm_next_action_note'] or gs_comment or '') if db_record else gs_comment
        
        if is_paid:
            cat = 'paye'
            final_statut = 'Payé / Inscrit'
        else:
            if crm_status:
                # Memoire CRM detectee !
                final_statut = crm_status
                if 'ferm' in crm_status.lower() or 'exclu' in crm_status.lower():
                    cat = 'ferme'
                else:
                    cat = 'relance'
            elif gs_comment:
                # Pas en base, mais commentaire manuel sur GS
                cat = 'relance'
                final_statut = 'En cours'
            else:
                cat = 'nouveau'
                final_statut = 'Nouveau'
                
        # Filtrage
        if agent_name != 'all' and agent != agent_name:
            continue
        if status_filter != 'all' and cat != status_filter:
            continue
        if search:
            search_lower = search.lower()
            if search_lower not in full_name.lower() and search_lower not in phone and search_lower not in email.lower() and search_lower not in student_id:
                continue
                
        # Format attendu par le frontend
        lead_dict = {
            "ID_Lead": student_id,
            "Nom": full_name,
            "Telephone": phone,
            "Email": email,
            "Genre": gender,
            "Pays": country,
            "Agent_Nom": agent,
            "Statut_CRM": final_statut,
            "Dernier_Resultat": crm_note[:50] + "..." if len(crm_note) > 50 else crm_note,
            "Prochaine_Action": "À appeler" if cat != 'paye' and cat != 'ferme' else "",
            "Date_Prochaine_Action": None,
            "Ancien_Commentaire": crm_note,
            "Appel_1": appel_1,
            "Appel_2": appel_2,
            "Appel_3": appel_3,
            "is_paid": 1 if is_paid else 0,
            "_Debug_Sheet": agent
        }
        leads.append(lead_dict)
        
        # Stats globales
        stats['total'] += 1
        if cat == 'relance':
            stats['en_cours'] += 1
        else:
            stats[cat] = stats.get(cat, 0) + 1
            
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
    return {
        "leads": leads,
        "stats": stats,
        "agents": agent_counts,
        "interactions": interactions_stats
    }



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
    """Met à jour le statut, insère dans l'historique et sauvegarde dans la mémoire du CRM + Miroir."""
    try:
        import crm_sync
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            await _ensure_crm_interactions_table(db)
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Recuperer les infos existantes s'il y en a
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

            # 2. Mettre à jour la mémoire du CRM (academy_students)
            parts = []
            if resultat: parts.append(f"[{resultat}{(' - ' + detail) if detail else ''}]")
            if prochaine_action: parts.append(f"(Action: {prochaine_action})")
            if note: parts.append(note)
            full_note = " ".join(parts).strip()
            
            # Si le lead n'existe pas en base locale (ex: nouvel ajout direct dans Google Sheet)
            if not student_info:
                await db.execute("INSERT OR IGNORE INTO academy_students (academic_id, student_id, first_name) VALUES (?, ?, ?)", (str(lead_id), str(lead_id), 'Lead CRM'))
                
            query = """
                UPDATE academy_students
                SET crm_lead_status = ?,
                    crm_next_action_note = ?,
                    crm_next_action_date = ?,
                    crm_last_contact_at = ?,
                    crm_assigned_to = CASE WHEN (crm_assigned_to IS NULL OR crm_assigned_to = '' OR crm_assigned_to = ' ') AND ? != '' THEN ? ELSE crm_assigned_to END
                WHERE academic_id = ? OR student_id = ?
            """
            await db.execute(query, (statut, full_note, date_prochaine, now_str, agent_name, agent_name, str(lead_id), str(lead_id)))
            await db.commit()
            
            # 3. Synchronisation miroir de secours (Backup Excel)
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
