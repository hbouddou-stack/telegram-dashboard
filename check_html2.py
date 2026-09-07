import io, re
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()
m = re.search(r'id="studentModal"(.*?)</dialog>', c, re.DOTALL)
if m:
    print(m.group(1)[:2000].encode('utf-8'))
