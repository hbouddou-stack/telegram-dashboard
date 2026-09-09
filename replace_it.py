import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

with io.open('new_js.txt', 'r', encoding='utf-8') as f:
    new_func = f.read()

idx1 = text.find('function openDuplicateScanner() {')
idx2 = text.find('async function toggleDuplicateExclude')

if idx1 != -1 and idx2 != -1:
    old_part = text[idx1:idx2]
    text = text.replace(old_part, new_func + '\n\n        ')
    
    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Replacement successful')
else:
    print('Could not find boundaries')
