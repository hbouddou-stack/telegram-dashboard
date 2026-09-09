import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    "switchModalTab('general');\n}",
    "switchModalTab('general');\n    document.getElementById('logs-overlay').style.display = 'flex';\n}"
)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
