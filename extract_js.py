import re
with open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    content = f.read()

scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
with open('temp_script.js', 'w', encoding='utf-8') as out:
    for script in scripts:
        out.write(script)
        out.write('\n\n')
