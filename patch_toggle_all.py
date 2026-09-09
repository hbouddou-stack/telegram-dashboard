import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_func = r'function toggleAllStudents\(\) \{\s*const isChecked = document.getElementById\(\'selectAllCheckbox\'\).checked;\s*const checkboxes = document.querySelectorAll\(\'.student-select-cb\'\);\s*checkboxes.forEach\(cb => cb.checked = isChecked\);\s*updateMassSmsButton\(\);\s*\}'

new_func = """function toggleAllStudents() {
            const cb1 = document.getElementById('selectAllCheckbox');
            const cb2 = document.getElementById('selectAllGrid');
            // Find which one triggered it, or just use whichever is checked
            const isChecked = (cb1 && cb1.checked) || (cb2 && cb2.checked);
            
            // Sync them
            if (cb1) cb1.checked = isChecked;
            if (cb2) cb2.checked = isChecked;
            
            const checkboxes = document.querySelectorAll('.student-select-cb');
            checkboxes.forEach(cb => cb.checked = isChecked);
            updateMassSmsButton();
        }"""

text = re.sub(old_func, new_func, text)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed toggleAllStudents')
