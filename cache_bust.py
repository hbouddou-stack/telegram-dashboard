with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("fetch('/api/admin/gateway/students')", "fetch('/api/admin/gateway/students?t=' + Date.now())")

with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
    f.write(text)
print("Cache bust applied!")
