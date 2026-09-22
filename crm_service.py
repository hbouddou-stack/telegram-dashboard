#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crm_service.py — reads from the dedicated CRM Google Sheet.

The CRM sheet (1IR55QGybqsXG4Oxxg9OLdAWHQb4P3dbXBhGpfftv3rM) is separate from 
the master sheet (1yxaucGpT7lrLqHb10PRsii5qso2mPveiiU2424tKCEI). The CRM sheet 
has worksheets: CRM_Leads, CRM_Agents, CRM_Interactions.

NOTE: The paid count discrepancy (478 vs more) exists because the CRM sheet only
has data from 3 agents. The other agents' data from 'Appel 2026' has NOT been
imported into the CRM sheet. This is a data migration issue, not a code bug.
The solution is to import more data into CRM_Leads — NOT to change this service.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
import threading
import gspread

# Target Google Sheet for the CRM
CRM_SHEET_ID = '1IR55QGybqsXG4Oxxg9OLdAWHQb4P3dbXBhGpfftv3rM'
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), 'credentials.json')
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'crm_cache.json')

_cache_lock = threading.Lock()
_memory_cache = {
    "leads": [],
    "interactions": [],
    "agents": [],
    "last_sync": 0
}

# Paid status values (aligned with the rest of the app)
_PAID_STATUTS_CRM = {'Payé / Inscrit', 'Exempté', 'مسدد', 'Inscrit'}
_PAID_STATUT_PAIEMENT = {'مسدد', 'معفي', 'مسددة'}

def _is_lead_paid(lead: dict) -> bool:
    st = str(lead.get('Statut_CRM', '') or '').strip()
    sp = str(lead.get('Statut_Paiement', '') or '').strip()
    if st in _PAID_STATUTS_CRM:
        return True
    if sp in _PAID_STATUT_PAIEMENT:
        return True
    if 'مسدد' in sp and 'غير مسدد' not in sp:
        return True
    return False

def _has_history(lead: dict) -> bool:
    """Return True if this lead has been contacted before."""
    return bool(
        lead.get('Ancien_Commentaire') or
        lead.get('Dernier_Contact_Resultat') or
        lead.get('Dernier_Contact_Date')
    )

def _categorize_lead(lead: dict) -> str:
    if _is_lead_paid(lead):
        return 'paye'
    st = str(lead.get('Statut_CRM', '') or '').strip()
    if st in ('مغلق', 'Abandon') or 'غير مهتم' in st or 'رقم خاطئ' in st:
        return 'ferme'
    # "nouveau" only if the lead has NEVER been contacted
    if (not st or st in ('Nouveau', 'جديد')) and not _has_history(lead):
        return 'nouveau'
    # Everything else is "in progress"
    return 'relance'

def _get_gspread_client():
    if not os.path.exists(CREDENTIALS_PATH):
        return None
    return gspread.service_account(filename=CREDENTIALS_PATH)

def load_cache():
    global _memory_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                _memory_cache = json.load(f)
                return True
        except Exception as e:
            print(f"[CRM Service] Error reading cache file: {e}")
    return False

def save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_memory_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CRM Service] Error writing cache file: {e}")

def refresh_from_sheet():
    global _memory_cache
    gc = _get_gspread_client()
    if not gc:
        print("[CRM Service] No credentials found.")
        return False
    try:
        sh = gc.open_by_key(CRM_SHEET_ID)
        
        ws_leads = sh.worksheet('CRM_Leads')
        leads = ws_leads.get_all_records()
        
        ws_agents = sh.worksheet('CRM_Agents')
        agents = ws_agents.get_all_records()
        
        ws_inter = sh.worksheet('CRM_Interactions')
        interactions = ws_inter.get_all_records()

        with _cache_lock:
            _memory_cache["leads"] = leads
            _memory_cache["agents"] = agents
            _memory_cache["interactions"] = interactions
            _memory_cache["last_sync"] = datetime.now().timestamp()
            save_cache()
            
        print(f"[CRM Service] Refreshed {len(leads)} leads, {len(interactions)} interactions.")
        return True
    except Exception as e:
        print(f"[CRM Service] Error fetching from sheet: {e}")
        return False

# Initialize cache on module load
if not load_cache() or not _memory_cache.get("leads"):
    threading.Thread(target=refresh_from_sheet, daemon=True).start()

def get_leads(agent_name=None, search=None, status_filter=None):
    with _cache_lock:
        leads = list(_memory_cache.get("leads", []))
        agents = list(_memory_cache.get("agents", []))
    
    # Filter by agent
    if agent_name and agent_name != "all":
        leads = [l for l in leads if str(l.get("Agent_Nom", "")).strip() == agent_name.strip()]

    # Filter by search term
    if search:
        s_lower = search.strip().lower()
        leads = [
            l for l in leads if
            s_lower in str(l.get("Nom", "")).lower() or
            s_lower in str(l.get("Telephone", "")).lower() or
            s_lower in str(l.get("Email", "")).lower() or
            s_lower in str(l.get("Pays", "")).lower() or
            s_lower in str(l.get("ID_Lead", "")).lower()
        ]

    # Categorize and compute stats
    stats = {"total": len(leads), "en_retard": 0, "aujourdhui": 0, "nouveaux": 0, "relances": 0, "payes": 0}

    for l in leads:
        cat = _categorize_lead(l)
        l["_category"] = cat
        if cat == 'paye':
            stats["payes"] += 1
        elif cat == 'nouveau':
            stats["nouveaux"] += 1
        elif cat == 'relance':
            stats["relances"] += 1

    # Filter by status
    if status_filter and status_filter != "all":
        leads = [l for l in leads if l.get("_category") == status_filter]

    return {
        "leads": leads,
        "agents": agents,
        "stats": stats,
        "last_sync": _memory_cache.get("last_sync", 0)
    }

def get_lead_details(lead_id):
    with _cache_lock:
        leads = _memory_cache.get("leads", [])
        interactions = _memory_cache.get("interactions", [])
    
    lead = next((l for l in leads if str(l.get("ID_Lead")).strip() == str(lead_id).strip()), None)
    lead_interactions = [i for i in interactions if str(i.get("ID_Lead")).strip() == str(lead_id).strip()]
    lead_interactions.reverse()
    
    return {"lead": lead, "interactions": lead_interactions}

def update_lead_status(lead_id, statut_crm, resultat, prochaine_action, date_prochaine, note, agent_email, canal="Téléphone"):
    today_str = datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    found_lead = None
    with _cache_lock:
        for l in _memory_cache.get("leads", []):
            if str(l.get("ID_Lead")).strip() == str(lead_id).strip():
                l["Statut_CRM"] = statut_crm
                l["Dernier_Contact_Date"] = today_str
                l["Dernier_Contact_Resultat"] = resultat
                l["Prochaine_Action"] = prochaine_action
                l["Date_Prochaine_Action"] = date_prochaine
                if note:
                    l["Ancien_Commentaire"] = note
                if statut_crm == 'مسدد':
                    l["Statut_Paiement"] = "مسدد"
                found_lead = l
                break
                
        new_inter_id = str(len(_memory_cache.get("interactions", [])) + 1)
        new_inter = {
            "ID_Interaction": new_inter_id,
            "ID_Lead": str(lead_id),
            "Date_Heure": now_str,
            "Agent_Email": agent_email or (found_lead.get("Agent_Email") if found_lead else ""),
            "Canal": canal,
            "Resultat": resultat,
            "Commentaire": note or resultat
        }
        _memory_cache.setdefault("interactions", []).append(new_inter)
        save_cache()

    threading.Thread(target=_sync_lead_to_sheet, args=(lead_id, found_lead, new_inter), daemon=True).start()
    return True

def _sync_lead_to_sheet(lead_id, lead_data, new_interaction):
    gc = _get_gspread_client()
    if not gc or not lead_data:
        return
    try:
        sh = gc.open_by_key(CRM_SHEET_ID)
        
        ws_leads = sh.worksheet('CRM_Leads')
        cell = ws_leads.find(str(lead_id))
        if cell:
            row_idx = cell.row
            update_vals = [
                lead_data.get("Statut_CRM", ""),
                lead_data.get("Dernier_Contact_Date", ""),
                lead_data.get("Dernier_Contact_Resultat", ""),
                lead_data.get("Prochaine_Action", ""),
                lead_data.get("Date_Prochaine_Action", "")
            ]
            ws_leads.update(range_name=f"I{row_idx}:M{row_idx}", values=[update_vals])
            if lead_data.get("Ancien_Commentaire"):
                ws_leads.update(range_name=f"N{row_idx}", values=[[lead_data.get("Ancien_Commentaire")]])
            if lead_data.get("Statut_Paiement"):
                ws_leads.update(range_name=f"O{row_idx}", values=[[lead_data.get("Statut_Paiement")]])
                
        ws_inter = sh.worksheet('CRM_Interactions')
        inter_vals = [
            new_interaction["ID_Interaction"],
            new_interaction["ID_Lead"],
            new_interaction["Date_Heure"],
            new_interaction["Agent_Email"],
            new_interaction["Canal"],
            new_interaction["Resultat"],
            new_interaction["Commentaire"]
        ]
        ws_inter.append_row(inter_vals)
        print(f"[CRM Service] Successfully synced lead {lead_id} to Google Sheet.")
    except Exception as e:
        print(f"[CRM Service] Failed to sync to Google Sheet: {e}")
