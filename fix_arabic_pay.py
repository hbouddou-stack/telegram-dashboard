import io

with io.open('database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "if payment_status in ['PAYE'" in l:
        lines[i] = l.replace("'مدفوع']:", "'مدفوع', 'مسدد']:")

with io.open('database.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)


with io.open('main.py', 'r', encoding='utf-8') as f:
    lines2 = f.readlines()

for i, l in enumerate(lines2):
    if "if pay_raw in ['PAID'" in l:
        lines2[i] = l.replace("'مدفوع']: payment_status", "'مدفوع', 'مسدد']: payment_status")

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines2)
