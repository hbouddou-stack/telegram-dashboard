import io, re
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()
m = re.search(r'function renderDashboardStats\(\).*?\}', c, re.DOTALL)
if m:
    print(m.group(0).encode('utf-8'))
