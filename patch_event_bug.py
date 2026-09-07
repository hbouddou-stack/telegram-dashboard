import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace event.currentTarget with document.getElementById
old = '''// Disable button to prevent double click
                const btn = event.currentTarget;
                const oldText = btn.innerHTML;
                btn.innerHTML = '⏳ جاري الحفظ...';
                btn.disabled = true;'''
new = '''// Disable button to prevent double click
                const btn = document.getElementById('btn-save-note');
                let oldText = '💾 حفظ الملاحظة وإرسال';
                if(btn) {
                    oldText = btn.innerHTML;
                    btn.innerHTML = '⏳ جاري الحفظ...';
                    btn.disabled = true;
                }'''
c = c.replace(old, new)

# Add ID to button
old_btn = '<button class="btn btn-primary" onclick="addCrmNote()"'
new_btn = '<button id="btn-save-note" class="btn btn-primary" onclick="addCrmNote()"'
c = c.replace(old_btn, new_btn)

# Enable button again
old_enable = '''const data = await res.json();
                btn.innerHTML = oldText;
                btn.disabled = false;'''
new_enable = '''const data = await res.json();
                if(btn) {
                    btn.innerHTML = oldText;
                    btn.disabled = false;
                }'''
c = c.replace(old_enable, new_enable)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
