#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crm_service.py — Reads directly from the local SQLite database (academy_students)
so that it perfectly matches the dashboard's "Students" (élèves) tab.
"""

import os
import aiosqlite
from datetime import datetime
from config import DATABASE_PATH

# Define paid payment statuses matching the dashboard
_PAID_STATUSES = [
    'PAID', 'PAYE', 'PAYÉ', 'OUI', 'YES', 'VALIDE', 'CONFIRME', '1', 'TRUE', 
    'EXEMPT', 'EPARGNE', 'EXONERE', 'مدفوع', 'مكتمل', 'نعم', 'مسدد', 'معفي', 'مسددة'
]

def _is_paid(ps: str) -> bool:
    if not ps:
        return False
    ps = ps.upper().strip()
    if ps in _PAID_STATUSES:
        return True
    if 'مسدد' in ps and 'غير مسدد' not in ps:
        return True
    return False

def _has_history(lead: dict) -> bool:
    return bool(lead.get('Ancien_Commentaire') or lead.get('Dernier_Contact_Resultat') or lead.get('crm_last_contact_at'))

def _categorize_lead(lead: dict) -> str:
    # 1. Paid
    if _is_paid(lead.get('Statut_Paiement', '')):
        return 'paye'
    # 2. Closed
    st = str(lead.get('Statut_CRM', '') or '').strip()
    if st in ('مغلق', 'Abandon') or 'غير مهتم' in st or 'رقم خاطئ' in st:
        return 'ferme'
    # 3. Nouveau (no history)
    if not _has_history(lead) and (not st or st in ('Nouveau', 'جديد', 'NOUVEAU')):
        return 'nouveau'
    # 4. In progress
    return 'relance'

async def get_leads_async():
    leads = []
    agents = set()
    stats = {
        "total": 0,
        "en_retard": 0,
        "aujourdhui": 0,
        "nouveaux": 0,
        "relances": 0,
        "payes": 0
    }
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Get all students, excluding deleted/ghosts
        query = """
            SELECT * FROM academy_students 
            WHERE (excluded = 0 OR excluded IS NULL)
        """
        async with db.execute(query) as cur:
            rows = await cur.fetchall()
            
            for r in rows:
                row = dict(r)
                
                # Combine call histories
                history_parts = [p for p in [row.get('comments'), row.get('appel_1'), row.get('appel_2'), row.get('appel_3')] if p]
                ancien_commentaire = ' | '.join(history_parts) if history_parts else ''
                
                # Format for CRM UI
                lead = {
                    "ID_Lead": row.get('academic_id') or row.get('student_id'),
                    "Nom": f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                    "Telephone": row.get('phone', ''),
                    "Email": row.get('email', ''),
                    "Genre": row.get('gender', ''),
                    "Pays": row.get('country', ''),
                    "Agent_Nom": row.get('crm_assigned_to') or row.get('team') or 'بدون وكيل',
                    "Statut_CRM": row.get('crm_lead_status') or 'Nouveau',
                    "Dernier_Contact_Date": row.get('crm_last_contact_at', ''),
                    "Dernier_Contact_Resultat": row.get('crm_next_action_note', ''),
                    "Prochaine_Action": row.get('crm_next_action_note', ''),
                    "Date_Prochaine_Action": row.get('crm_next_action_date', ''),
                    "Ancien_Commentaire": ancien_commentaire,
                    "Statut_Paiement": row.get('payment_status', '')
                }
                
                cat = _categorize_lead(lead)
                lead["_category"] = cat
                
                stats["total"] += 1
                if cat == 'paye': stats["payes"] += 1
                elif cat == 'ferme': pass # Not tracked in pills
                elif cat == 'nouveau': stats["nouveaux"] += 1
                else: stats["relances"] += 1
                
                # Overdue / Today logic
                next_date = lead.get("Date_Prochaine_Action", "")
                if cat == 'relance' and next_date:
                    if next_date < today_str:
                        stats["en_retard"] += 1
                    elif next_date == today_str:
                        stats["aujourdhui"] += 1
                
                leads.append(lead)
                agents.add(lead["Agent_Nom"])
                
    return {
        "leads": leads,
        "stats": stats,
        "agents": sorted(list(agents)),
        "interactions": []  # Not pulling full history for now to keep it fast
    }

def get_leads(agent_name: str = 'all', search: str = '', status_filter: str = 'all') -> dict:
    """Wrapper for synchronous calls if needed, though main.py is async."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    data = loop.run_until_complete(get_leads_async())
    
    # Filter leads if needed
    leads = data["leads"]
    if agent_name and agent_name != 'all':
        leads = [l for l in leads if l["Agent_Nom"] == agent_name]
    
    if search:
        search = search.lower()
        leads = [l for l in leads if search in l["Nom"].lower() or search in l["Telephone"].lower() or search in l["Email"].lower()]
        
    if status_filter and status_filter != 'all':
        leads = [l for l in leads if l["_category"] == status_filter]
        
    data["leads"] = leads
    
    # Recompute stats based on filtered list
    stats = {"total": len(leads), "en_retard": 0, "aujourdhui": 0, "nouveaux": 0, "relances": 0, "payes": 0}
    today_str = datetime.now().strftime('%Y-%m-%d')
    for l in leads:
        cat = l["_category"]
        if cat == 'paye': stats["payes"] += 1
        elif cat == 'nouveau': stats["nouveaux"] += 1
        elif cat == 'relance': stats["relances"] += 1
        
        next_date = l.get("Date_Prochaine_Action", "")
        if cat == 'relance' and next_date:
            if next_date < today_str:
                stats["en_retard"] += 1
            elif next_date == today_str:
                stats["aujourdhui"] += 1
                
    data["stats"] = stats
    return data

async def update_lead_status_async(lead_id: str, statut: str, resultat: str, prochaine_action: str, date_prochaine: str, note: str, agent_email: str = '', canal: str = '') -> bool:
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            query = """
                UPDATE academy_students 
                SET crm_lead_status = ?, 
                    crm_next_action_note = ?, 
                    crm_next_action_date = ?,
                    crm_last_contact_at = ?
                WHERE academic_id = ? OR student_id = ?
            """
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # combine resultat and note
            full_note = f"[{resultat}] {note}" if resultat else note
            
            await db.execute(query, (statut, full_note, date_prochaine, now_str, lead_id, lead_id))
            
            # If they are marked as paid in CRM, also update payment_status
            if statut in ('مسدد', 'Payé / Inscrit', 'Exempté'):
                await db.execute(
                    "UPDATE academy_students SET payment_status = 'مسدد' WHERE (academic_id = ? OR student_id = ?) AND payment_status NOT LIKE '%مسدد%'", 
                    (lead_id, lead_id)
                )
            await db.commit()
        return True
    except Exception as e:
        print(f"Error updating lead {lead_id}: {e}")
        return False

def update_lead_status(lead_id: str, statut: str, resultat: str, prochaine_action: str, date_prochaine: str, note: str, agent_email: str = '', canal: str = '') -> bool:
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(update_lead_status_async(lead_id, statut, resultat, prochaine_action, date_prochaine, note, agent_email, canal))

async def get_lead_details_async(lead_id: str) -> dict:
    # Return minimal details since interactions are stored in the main row
    # In a full implementation, you would query an interactions table
    return {"interactions": []}

def get_lead_details(lead_id: str) -> dict:
    import asyncio
    return asyncio.run(get_lead_details_async(lead_id))

def refresh_from_sheet() -> bool:
    # No-op since we read from DB
    return True
