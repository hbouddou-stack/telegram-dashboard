import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Change INVALID_LINK_ATTEMPT color to black
old_invalid = r"'INVALID_LINK_ATTEMPT': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '⛔', label: 'محاولة رابط غير صالح' }"
new_invalid = r"'INVALID_LINK_ATTEMPT': { bg: '#1a1a1a', border: '#333333', text: '#ffffff', icon: '🏴‍☠️', label: 'محاولة رابط غير صالح' }"

c = c.replace(old_invalid, new_invalid)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Patched invalid log color')
