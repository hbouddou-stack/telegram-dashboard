import io, re

# Fix database.py
with io.open('database.py', 'r', encoding='utf-8') as f:
    db_c = f.read()

bad_db = """                payment_status = (r.get('payment_status') or 'PAID').strip().upper()
                # Normalisation du statut de paiement
                if any(k in payment_status for k in ['PAYE', 'PAID', 'YES', 'OUI', 'VALIDE', 'ACTIVE', 'COMPLETED', ' ', '', '1', 'TRUE']):
                    payment_status = 'PAID'
                else:
                    payment_status = 'PENDING'"""
                    
good_db = """                payment_status = (r.get('payment_status') or 'UNPAID').strip().upper()
                # Normalisation du statut de paiement
                if payment_status in ['PAYE', 'PAYÉ', 'PAID', 'YES', 'OUI', 'VALIDE', 'ACTIVE', 'COMPLETED', '1', 'TRUE', 'مدفوع']:
                    payment_status = 'PAID'
                else:
                    payment_status = 'UNPAID'"""
                    
db_c = db_c.replace(bad_db, good_db)
with io.open('database.py', 'w', encoding='utf-8') as f:
    f.write(db_c)
print("database.py fixed")


# Fix main.py
with io.open('main.py', 'r', encoding='utf-8') as f:
    main_c = f.read()

bad_main = """                pay_raw = str(row[7]).upper().strip() if len(row) > 7 else ''
                payment_status = 'UNPAID'
                if pay_raw in ["PAID", "PAYE", "VALIDE", "CONFIRME", "", ""]: payment_status = 'PAID'"""
                
good_main = """                pay_raw = str(row[7]).upper().strip() if len(row) > 7 else ''
                payment_status = 'UNPAID'
                if pay_raw in ["PAID", "PAYE", "PAYÉ", "VALIDE", "CONFIRME", "OUI", "YES", "مدفوع"]: payment_status = 'PAID'"""

main_c = main_c.replace(bad_main, good_main)
with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_c)
print("main.py fixed")
