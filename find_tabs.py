import io
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    for line in f:
        if 'class="mtab"' in line:
            print(line.strip().encode('utf-8'))
