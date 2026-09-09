import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('function openDuplicateScanner() {', 'function openDuplicateScanner() {\n            alert("Clic reçu ! Analyse en cours...");')

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Alert injected')
