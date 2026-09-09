import io, re

with io.open('database.py', 'r', encoding='utf-8') as f:
    db = f.read()

# Fix database.py
db = re.sub(
    r"payment_status = \(r\.get\('payment_status'\) or 'PAID'\)\.strip\(\)\.upper\(\)\s*# Normalisation du statut de paiement\s*if any\(k in payment_status for k in \['PAYE', 'PAID', 'YES', 'OUI', 'VALIDE', 'ACTIVE', 'COMPLETED', ' ', '', '1', 'TRUE'\]\):\s*payment_status = 'PAID'\s*else:\s*payment_status = 'PENDING'",
    r"""payment_status = (r.get('payment_status') or 'UNPAID').strip().upper()
                # Normalisation du statut de paiement
                if payment_status in ['PAYE', 'PAYÉ', 'PAID', 'YES', 'OUI', 'VALIDE', 'ACTIVE', 'COMPLETED', '1', 'TRUE', 'مدفوع']:
                    payment_status = 'PAID'
                else:
                    payment_status = 'UNPAID'""",
    db
)

with io.open('database.py', 'w', encoding='utf-8') as f:
    f.write(db)


with io.open('main.py', 'r', encoding='utf-8') as f:
    mn = f.read()
    
mn = re.sub(
    r'pay_raw = str\(row\[7\]\)\.upper\(\)\.strip\(\) if len\(row\) > 7 else \'\'\s*payment_status = \'UNPAID\'\s*if pay_raw in \["PAID", "PAYE", "VALIDE", "CONFIRME", "", ""\]: payment_status = \'PAID\'',
    r"""pay_raw = str(row[7]).upper().strip() if len(row) > 7 else ''
                payment_status = 'UNPAID'
                if pay_raw in ["PAID", "PAYE", "PAYÉ", "VALIDE", "CONFIRME", "OUI", "YES", "مدفوع"]: payment_status = 'PAID'""",
    mn
)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(mn)
