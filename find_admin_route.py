with open('main.py', 'r', encoding='utf-8') as f:
    for i, l in enumerate(f):
        if 'admin_gateway.html' in l:
            print(f'{i+1}: {l.strip()[:120]}')
