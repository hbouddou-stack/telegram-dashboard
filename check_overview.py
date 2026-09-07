import io, re
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()
m = re.search(r'<div id="tab-overview" class="tab-content">(.*?)<div id="tab-actions"', c, re.DOTALL)
if m:
    print(m.group(1).encode('utf-8')[:2000])
