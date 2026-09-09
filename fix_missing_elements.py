import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# FIX 1: Secure the two crashing lines in JS so they don't throw if element is missing
# Line: document.getElementById('profile-import-text').innerHTML = `...`
# Fix: const importEl = document.getElementById('profile-import-text'); if(importEl) importEl.innerHTML = ...

old_import = "document.getElementById('profile-import-text').innerHTML = `\U0001f4c5 ${createdAt} <br> \U0001f4c1 ${sourceFile}`;"
new_import = "const importEl = document.getElementById('profile-import-text'); if(importEl) importEl.innerHTML = `\U0001f4c5 ${createdAt} <br> \U0001f4c1 ${sourceFile}`;"

if old_import in c:
    c = c.replace(old_import, new_import)
    print("FIX 1 applied: profile-import-text secured")
else:
    print("FIX 1: pattern not found verbatim, trying alternative...")
    # Try with the actual bytes
    idx = c.find("profile-import-text").innerHTML")
    if idx != -1:
        print(f"Found at {idx}")

# FIX 2: The lvlBadge is already using getElementById with if(lvlBadge) - check if it's there
if "if(lvlBadge)" in c:
    print("FIX 2: lvlBadge already has null check - OK")
else:
    print("FIX 2: lvlBadge missing null check")
    old_lvl = "const lvlBadge = document.getElementById('profile-level-badge');\n            if(lvlBadge) {"
    print("Looking for lvlBadge usage...")
    idx = c.find("profile-level-badge")
    print(repr(c[idx-20:idx+200]))

# FIX 3: Add the missing HTML elements to the modal
# Find a good place to inject: near profile-name-text
if 'id="profile-import-text"' in c:
    print("FIX 3: profile-import-text already in HTML")
else:
    # Add it after profile-name section. Find profile-name-text span
    old_html = '<span id="profile-name-text"'
    if old_html in c:
        # Find the closing of that line/section and add after
        idx = c.find(old_html)
        # Find end of the containing div
        section = c[idx:idx+500]
        print("Context around name text:")
        print(repr(section[:300]))

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("\nSaved.")
