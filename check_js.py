import re
with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    html = f.read()
scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
with open("temp.js", "w", encoding="utf-8") as f:
    for s in scripts:
        f.write(s + "\n")
