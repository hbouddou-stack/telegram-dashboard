#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_to_crm_sheet.py
=======================
Reads ALL leads from the master Google Sheet (ALL agent tabs) and pushes
MISSING ones into the CRM_Leads worksheet of the CRM Google Sheet.

Master sheet (READ-ONLY): 1yxaucGpT7lrLqHb10PRsii5qso2mPveiiU2424tKCEI
CRM sheet   (READ+WRITE):  1IR55QGybqsXG4Oxxg9OLdAWHQb4P3dbXBhGpfftv3rM

Existing leads are identified by their ID or email.
Only missing leads are appended — no duplicates.
"""

import gspread
import hashlib
import time

# ---- CONFIG ----
MASTER_SHEET_ID = '1yxaucGpT7lrLqHb10PRsii5qso2mPveiiU2424tKCEI'
CRM_SHEET_ID    = '1IR55QGybqsXG4Oxxg9OLdAWHQb4P3dbXBhGpfftv3rM'

# Tabs to scan from the master sheet (all agent/lead tabs)
MASTER_TABS = [
    'appels 2026',
    'mariam MAraqi',
    'NAJOUA',
    'ZAYNAB',
    'database lead',
    'liste des anciens leads',
    'Copy of appels 2026 1',
    'Copy of appels 2026',
]

CRM_TAB    = 'CRM_Leads'
CREDS_PATH = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\credentials.json'

# ---- Payment classification ----
_UNPAID_WORDS = ['غير مسدد', 'UNPAID', 'NON PAYE', 'NON PAYÉ', 'غير مدفوع']
_PAID_WORDS   = ['مسدد', 'مسددة', 'معفي', 'مدفوع', 'PAID', 'PAYÉ', 'PAYE',
                 'OUI', 'YES', 'VALIDE', 'CONFIRME', '1']

def classify_payment(raw):
    r = str(raw).upper().strip()
    for w in _UNPAID_WORDS:
        if w in r:
            return 'غير مسدد'
    for w in _PAID_WORDS:
        if w in r.upper():
            return 'مسدد'
    return 'غير مسدد'

def crm_status(pay_raw, comments, appel_1):
    if classify_payment(pay_raw) == 'مسدد':
        return 'Payé / Inscrit'
    if appel_1 or comments:
        return 'En cours'
    return 'Nouveau'

def make_id(academic_id, email):
    if academic_id:
        return str(academic_id)
    return str(int(hashlib.md5(email.encode()).hexdigest()[:6], 16))[:6]

def gender_display(raw):
    r = str(raw).upper().strip()
    if r in ('FEMME', 'FEMALE', 'FILLE', 'F', 'أنثى'):
        return 'Femme'
    return 'Homme'

def safe_get(row, idx, default=''):
    if idx is not None and idx < len(row):
        return str(row[idx]).strip()
    return default

def find_col(header, *names):
    for n in names:
        for i, h in enumerate(header):
            if h.strip().lower() == n.lower():
                return i
    return None

def main():
    print("Connecting to Google Sheets...")
    gc = gspread.service_account(filename=CREDS_PATH)

    # 1. Open master sheet (READ-ONLY)
    print(f"\nOpening master sheet: {MASTER_SHEET_ID}")
    master_sh = gc.open_by_key(MASTER_SHEET_ID)
    all_tabs_in_master = {ws.title: ws for ws in master_sh.worksheets()}
    print(f"  Available tabs: {list(all_tabs_in_master.keys())}")

    # 2. Open CRM sheet and load existing IDs + emails (to prevent duplicates)
    print(f"\nOpening CRM sheet: {CRM_SHEET_ID}")
    crm_sh = gc.open_by_key(CRM_SHEET_ID)
    crm_ws = crm_sh.worksheet(CRM_TAB)

    print("  Loading existing CRM leads...")
    existing_rows = crm_ws.get_all_values()
    existing_ids    = set()
    existing_emails = set()
    if len(existing_rows) > 1:
        for row in existing_rows[1:]:
            if row and row[0]:
                existing_ids.add(str(row[0]).strip())
            if len(row) > 3 and row[3]:
                existing_emails.add(str(row[3]).strip().lower())
    print(f"  Existing leads in CRM_Leads: {len(existing_ids)}")

    # CRM_Leads column order:
    # ID_Lead|Nom|Telephone|Email|Genre|Pays|Agent_Nom|Agent_Email|
    # Statut_CRM|Dernier_Contact_Date|Dernier_Contact_Resultat|
    # Prochaine_Action|Date_Prochaine_Action|Ancien_Commentaire|Statut_Paiement

    # 3. Process each tab
    all_new_rows = []

    for tab_name in MASTER_TABS:
        if tab_name not in all_tabs_in_master:
            print(f"\n  ⚠  Tab '{tab_name}' not found — skipping.")
            continue

        print(f"\n  Tab '{tab_name}'...")
        ws   = all_tabs_in_master[tab_name]
        rows = ws.get_all_values()

        if len(rows) <= 1:
            print("     Empty — skipping.")
            continue
        print(f"     {len(rows)-1} data rows found")

        header = rows[0]

        # Auto-detect column positions
        COL_ID      = 0
        COL_NAME    = find_col(header, 'الإسم الكامل', 'nom', 'name', 'prenom') or 2
        COL_EMAIL   = find_col(header, 'البريد الإلكتروني', 'email', 'mail') or 3
        COL_PHONE   = find_col(header, 'رقم الهاتف', 'telephone', 'phone', 'tel') or 4
        COL_GENDER  = find_col(header, 'الجنس', 'genre', 'gender', 'sexe') or 6
        COL_PAY     = find_col(header, 'وضعية الحساب', 'statut', 'paye', 'paiement', 'payment') or 7
        COL_COUNTRY = find_col(header, 'دولة الإقامة', 'pays', 'country') or 8
        COL_LNAME   = find_col(header, 'الإسم الكامل باللغة الأجنبية', 'nom complet', 'last name') or 15
        COL_TEAM    = find_col(header, 'الفريق', 'team', 'agent') or 18
        COL_COMMENT = find_col(header, 'commentaires', 'commentaire', 'notes') or 19
        COL_APPEL1  = find_col(header, 'appel 1', 'appel1') or 20
        COL_APPEL2  = find_col(header, 'appel 2', 'appel2') or 21
        COL_APPEL3  = find_col(header, 'appel 3', 'appel3') or 22

        tab_new = 0
        tab_exists = 0
        tab_skip = 0

        for row in rows[1:]:
            if not any(c.strip() for c in row):
                continue

            academic_id = safe_get(row, COL_ID)
            first_name  = safe_get(row, COL_NAME)
            email       = safe_get(row, COL_EMAIL).lower()
            phone       = safe_get(row, COL_PHONE)
            gender_raw  = safe_get(row, COL_GENDER)
            pay_raw     = safe_get(row, COL_PAY)
            country     = safe_get(row, COL_COUNTRY)
            last_name   = safe_get(row, COL_LNAME)
            team        = safe_get(row, COL_TEAM) or tab_name
            comments    = safe_get(row, COL_COMMENT)
            appel_1     = safe_get(row, COL_APPEL1)
            appel_2     = safe_get(row, COL_APPEL2)
            appel_3     = safe_get(row, COL_APPEL3)

            # Skip header-like or totally empty rows
            if email in ('email', 'بريد', 'البريد الإلكتروني'):
                tab_skip += 1
                continue
            if (not email or '@' not in email) and not academic_id:
                tab_skip += 1
                continue

            lead_id = make_id(academic_id, email)

            # Deduplicate
            if lead_id in existing_ids or (email and email in existing_emails):
                tab_exists += 1
                continue

            full_name = f"{first_name} {last_name}".strip() or 'بدون اسم'
            statut_paiement = classify_payment(pay_raw)
            statut_crm_val  = crm_status(pay_raw, comments, appel_1)

            history = [p for p in [comments, appel_1, appel_2, appel_3] if p]
            ancien_commentaire = ' | '.join(history)

            crm_row = [
                lead_id,
                full_name,
                phone,
                email,
                gender_display(gender_raw),
                country,
                team,
                '',              # Agent_Email
                statut_crm_val,
                '',              # Dernier_Contact_Date
                appel_1,        # Dernier_Contact_Resultat
                appel_2 or 'معاودة الاتصال',
                '',              # Date_Prochaine_Action
                ancien_commentaire,
                statut_paiement
            ]

            all_new_rows.append(crm_row)
            existing_ids.add(lead_id)
            if email:
                existing_emails.add(email)
            tab_new += 1

        print(f"     -> {tab_new} new leads | {tab_exists} already existed | {tab_skip} skipped")

    # 4. Batch append to CRM_Leads
    print(f"\n{'='*55}")
    print(f"Total new leads to add: {len(all_new_rows)}")

    if not all_new_rows:
        print("\nNothing to add — CRM is already complete!")
        return

    BATCH_SIZE  = 200
    total_added = 0

    print(f"Appending in batches of {BATCH_SIZE}...")
    for i in range(0, len(all_new_rows), BATCH_SIZE):
        batch = all_new_rows[i:i + BATCH_SIZE]
        crm_ws.append_rows(batch, value_input_option='USER_ENTERED')
        total_added += len(batch)
        print(f"  Added {total_added}/{len(all_new_rows)}")
        time.sleep(2)

    print(f"\nDone! Added {total_added} new leads to CRM_Leads.")
    print(f"Total in CRM now: ~{len(existing_ids)}")

if __name__ == '__main__':
    main()
