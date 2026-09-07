
import io, re
with io.open('sync_sheets.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = re.sub(r'if c_up in \[\"UNPAID\".*?\):', 'if c_up in [\'UNPAID\', \'NON\', \'ATTENTE\', \'PENDING\', \'??? ?????\', \'???\']:', c)
with io.open('sync_sheets.py', 'w', encoding='utf-8') as f:
    f.write(c)

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = re.sub(r'if c_up in \[\"UNPAID\".*?\):', 'if c_up in [\'UNPAID\', \'NON\', \'ATTENTE\', \'PENDING\', \'??? ?????\', \'???\']:', c)
c = re.sub(r'elif c_up in \[\"PAID\".*?\):', 'elif c_up in [\'PAID\', \'PAYE\', \'VALIDE\', \'CONFIRME\', \'?????\', \'???\']:', c)
with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)

