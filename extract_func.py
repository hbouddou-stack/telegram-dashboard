import io, re
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()
m = re.search(r'function openStudentCard.*?\}', c, re.DOTALL)
if m:
    with open('temp_func.txt', 'wb') as out:
        out.write(m.group(0).encode('utf-8'))
