import io

with io.open('database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if "payment_status = (r.get(" in l:
        lines[i] = l.replace("or 'PAID'", "or 'UNPAID'")
    if "if any(k in payment_status for k in" in l:
        lines[i] = "                if payment_status in ['PAYE', 'PAYÉ', 'PAID', 'YES', 'OUI', 'VALIDE', 'ACTIVE', 'COMPLETED', '1', 'TRUE', 'مدفوع']:\n"
    if "payment_status = 'PENDING'" in l:
        lines[i] = l.replace("PENDING", "UNPAID")
with io.open('database.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'if pay_raw in ["PAID", "PAYE"' in l:
        lines[i] = "                if pay_raw in ['PAID', 'PAYE', 'PAYÉ', 'VALIDE', 'CONFIRME', 'OUI', 'YES', 'مدفوع']: payment_status = 'PAID'\n"
with io.open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
