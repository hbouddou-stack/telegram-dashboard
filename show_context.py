import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find and show context
idx = c.find("switchModalTab('general');")
with io.open('context.txt', 'w', encoding='utf-8') as f:
    f.write(repr(c[idx-50:idx+300]))
print("Saved to context.txt")
