import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

with io.open('contexts.txt', 'w', encoding='utf-8') as out:
    # Find profile-import-text in JS
    idx = c.find('profile-import-text')
    out.write("=== profile-import-text JS context ===\n")
    out.write(repr(c[idx-80:idx+150]) + "\n\n")
    
    # Find profile-level-badge
    idx2 = c.find('profile-level-badge')
    out.write("=== profile-level-badge context ===\n")
    out.write(repr(c[idx2-80:idx2+200]) + "\n\n")
    
    # Find where modal HTML is - look for profile-name-text
    idx3 = c.find('profile-name-text')
    out.write("=== profile-name-text HTML context ===\n")
    out.write(repr(c[idx3-100:idx3+200]) + "\n\n")

print("Saved to contexts.txt")
