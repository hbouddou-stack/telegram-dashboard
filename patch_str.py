import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

target = 'color:#34c759\"; display:flex;'
c = c.replace(target, 'color:#34c759; display:flex;')

c = c.replace('🎓 Num. Étudiant', '🎓 Numéro Étudiant')
c = c.replace('ID académique', 'Numéro Étudiant')

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
