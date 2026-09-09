import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find where the JS tries to set profile-import-text
idx = c.find('profile-import-text')
print("JS context:")
print(repr(c[idx-80:idx+150]))
print()

# Find profile-level-badge in JS
idx2 = c.find('profile-level-badge')
print("Level badge JS context:")
print(repr(c[idx2-80:idx2+200]))
print()

# Find profile-name-text in HTML
idx3 = c.find('profile-name-text')
print("HTML context for name-text:")
print(repr(c[idx3-100:idx3+200]))
