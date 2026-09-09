import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('inset: 0;', 'top: 0; left: 0; right: 0; bottom: 0;')
text = text.replace('inset:0;', 'top: 0; left: 0; right: 0; bottom: 0;')
text = text.replace('alert("Clic reçu ! Analyse en cours...");', '')

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed CSS inset bug')
