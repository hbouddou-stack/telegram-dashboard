with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

import re

# Fix all lowerCase bugs
text = text.replace("const name = (s.first_name || '').toLowerCase();", "const name = String(s.first_name || '').toLowerCase();")
text = text.replace("const lname = (s.last_name || '').toLowerCase();", "const lname = String(s.last_name || '').toLowerCase();")
text = text.replace("const email = (s.email || '').toLowerCase();", "const email = String(s.email || '').toLowerCase();")
text = text.replace("const source = (s.source || '').toLowerCase();", "const source = String(s.source || '').toLowerCase();")
text = text.replace("const dob = (s.dob || '').toLowerCase();", "const dob = String(s.dob || '').toLowerCase();")
text = text.replace("const tgFirstName = (s.tg_first_name || '').toLowerCase();", "const tgFirstName = String(s.tg_first_name || '').toLowerCase();")
text = text.replace("const g = (s.gender || '').toLowerCase();", "const g = String(s.gender || '').toLowerCase();")
text = text.replace("const g = (student.gender || '').toLowerCase();", "const g = String(student.gender || '').toLowerCase();")

with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
    f.write(text)
print("Type coercion applied!")
