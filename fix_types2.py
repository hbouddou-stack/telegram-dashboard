with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("let tgFullName = s.tg_first_name || '';", "let tgFullName = String(s.tg_first_name || '');")
text = text.replace("if (s.tg_last_name) tgFullName += ' ' + s.tg_last_name;", "if (s.tg_last_name) tgFullName += ' ' + String(s.tg_last_name);")
text = text.replace("const yrStr = String(s.year || '');", "const yrStr = String(s.year || '');")

with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
    f.write(text)
print("More type coercions applied!")
