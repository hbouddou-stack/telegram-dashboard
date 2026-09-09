import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Update CSS completely for modal-overlay
old_css = r"\.modal-overlay\s*\{[^}]+\}"
new_css = """.modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.85);
            z-index: 999999;
            align-items: center;
            justify-content: center;
        }"""
text = re.sub(old_css, new_css, text)

# Add alert explicitly for debugging one last time inside the function
# just to show it to the user so they know it runs.
text = text.replace('function openDuplicateScanner() {', 'function openDuplicateScanner() {\n            alert("Ouverture du scanner en cours (patientez quelques secondes)...");')

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed CSS and added alert')
