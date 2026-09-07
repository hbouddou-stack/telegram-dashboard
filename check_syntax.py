import re
with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

scripts = re.findall(r"<script>(.*?)</script>", text, re.DOTALL)
with open("temp.js", "w", encoding="utf-8") as f:
    f.write(scripts[0])
