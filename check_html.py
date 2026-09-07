import io
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

print("Actions target:", '<!-- Actions -->' in c)
print("Info email target:", "profile-email-text" in c)
