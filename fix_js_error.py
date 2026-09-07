import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# We need to find the OLD phoneEl block and remove it.
old_phone_block = """            // Phone - fix RTL, put + on the left
            const phoneEl = document.getElementById('profile-phone-text');
            if(phoneEl) {
                let phone = String(student.phone || '').trim();
                if (phone && !phone.startsWith('+')) phone = '+' + phone;
                phoneEl.textContent = phone || 'لا يتوفر';
            }"""

c = c.replace(old_phone_block, "")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Removed duplicate phoneEl declaration")
