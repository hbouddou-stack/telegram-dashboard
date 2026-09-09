import io
import re
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

start = c.find('function displayStudents')
if start != -1:
    end = c.find('\n        function', start + 10)
    with io.open('display_func.js', 'w', encoding='utf-8') as out:
        out.write(c[start:end])
    print("Extracted to display_func.js")
