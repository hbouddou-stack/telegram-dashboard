import io, re

# 1. FIX MAIN.PY EXCEL PARSING LOGIC
with io.open('main.py', 'r', encoding='utf-8') as f:
    main_c = f.read()

bad_pay_logic = """                pay_raw = str(row[7]).upper().strip() if len(row) > 7 else ''
                payment_status = 'UNPAID'
                if pay_raw in ['PAID', 'PAYE', 'PAYÉ', 'VALIDE', 'CONFIRME', 'OUI', 'YES', 'مدفوع', 'مسدد']: payment_status = 'PAID'"""

good_pay_logic = """                # RECHERCHE INTELLIGENTE DU PAIEMENT DANS TOUTE LA LIGNE
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

main_c = main_c.replace(bad_pay_logic, good_pay_logic)
with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_c)


# 2. FIX DASHBOARD HTML FOR UNPAID FILTERS
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_options = """<option value="linked">✅ مربوط (Linked)</option>
                        <option value="unlinked">❌ غير مربوط (Unlinked)</option>"""

new_options = """<option value="linked">🔗 مربوط بتليجرام</option>
                        <option value="unlinked">⏳ غير مربوط بتليجرام</option>
                        <option value="paid">✅ مسدد (Payé)</option>
                        <option value="unpaid">❌ غير مسدد (Non Payé)</option>"""

html = html.replace(old_options, new_options)

old_filter_logic = """                const linked = !!s.telegram_id;
                const matchStatus = filters.status === 'all'
                    || (filters.status === 'linked' && linked)
                    || (filters.status === 'unlinked' && !linked);"""

new_filter_logic = """                const linked = !!s.telegram_id;
                const isPaid = String(s.payment_status || '').toUpperCase() === 'PAID';
                const matchStatus = filters.status === 'all'
                    || (filters.status === 'linked' && linked)
                    || (filters.status === 'unlinked' && !linked)
                    || (filters.status === 'paid' && isPaid)
                    || (filters.status === 'unpaid' && !isPaid);"""

html = html.replace(old_filter_logic, new_filter_logic)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Logic fixed!")
