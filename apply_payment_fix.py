import io, unicodedata

with io.open('main.py', 'r', encoding='utf-8') as f:
    main_c = f.read()

# Remplacer la logique foireuse par la version bulletproof
old_logic = """                # RECHERCHE INTELLIGENTE DU PAIEMENT DANS TOUTE LA LIGNE
                payment_status = 'UNPAID'
                row_str = " ".join([str(x) for x in row]).upper()
                if 'غير مسدد' in row_str or 'UNPAID' in row_str:
                    payment_status = 'UNPAID'
                elif 'مسدد' in row_str or 'مدفوع' in row_str or 'PAID' in row_str or 'PAYÉ' in row_str or 'PAYE' in row_str:
                    payment_status = 'PAID'
                else:
                    # Fallback sur la colonne H (7) au cas où
                    pay_raw = str(row[7]).upper().strip() if len(row) > 7 else ''
                    if pay_raw in ['VALIDE', 'CONFIRME', 'OUI', 'YES', '1']:
                        payment_status = 'PAID'"""

new_logic = """                # DETECTION BULLETPROOF DU PAIEMENT
                # REGLE D'OR: tester UNPAID EN PREMIER
                # car 'مسدد' (paid) est une sous-chaine de 'غير مسدد' (unpaid) !
                def _clean(v):
                    import unicodedata as _ud
                    s = _ud.normalize('NFKC', str(v or '').strip())
                    for c in ['\\u200f','\\u200e','\\u200b','\\u200c','\\u200d','\\ufeff']:
                        s = s.replace(c, '')
                    return s.strip()

                _UNPAID = ['غير مسدد', 'UNPAID', 'NON PAYE', 'NON PAYÉ', 'غير مدفوع']
                _PAID   = ['مسدد', 'مدفوع', 'PAID', 'PAYÉ', 'PAYE', 'OUI', 'YES', 'VALIDE', 'CONFIRME', '1']
                _cells  = [_clean(c) for c in row]

                payment_status = 'UNPAID'  # defaut = non paye
                # 1) Chercher UNPAID en premier (prioritaire)
                _found = False
                for _cell in _cells:
                    for _w in _UNPAID:
                        if _w in _cell:
                            payment_status = 'UNPAID'
                            _found = True
                            break
                    if _found: break
                # 2) Seulement si aucun mot UNPAID trouve, chercher PAID
                if not _found:
                    for _cell in _cells:
                        for _w in _PAID:
                            if _w in _cell:
                                payment_status = 'PAID'
                                break
                        if payment_status == 'PAID': break"""

if old_logic in main_c:
    main_c = main_c.replace(old_logic, new_logic)
    print("Pattern found and replaced!")
else:
    print("ERROR: Pattern not found - searching for fallback...")
    # Fallback search
    idx = main_c.find("pay_raw = str(row[7]).upper().strip() if len(row) > 7 else ''")
    if idx > -1:
        print(f"Fallback found at char {idx}")
    else:
        print("Nothing found!")

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_c)
