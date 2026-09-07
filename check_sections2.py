import io
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    for l in f:
        if 'tab-content' in l:
            print(l.strip())
