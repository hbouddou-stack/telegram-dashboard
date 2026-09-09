import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

old = '<!-- SEARCH + SORT + VIEW CONTROLS -->'
new = """<!-- SEARCH + SORT + VIEW CONTROLS -->
        <div style="padding:4px 12px; display:flex; justify-content:space-between; align-items:center;">
            <label style="cursor:pointer; font-weight:bold; color:var(--text1); font-size:0.85rem;"><input type="checkbox" id="selectAllGrid" onclick="toggleAllStudents()" style="margin-left:8px; transform:scale(1.2);"> Tout sélectionner</label>
        </div>"""
text = text.replace(old, new)

# And update toggleAllStudents logic to use the new checkbox if the old one isn't there
old_toggle = """function toggleAllStudents() {
const isChecked = document.getElementById('selectAllCheckbox').checked;"""
new_toggle = """function toggleAllStudents() {
    const cb1 = document.getElementById('selectAllCheckbox');
    const cb2 = document.getElementById('selectAllGrid');
    const isChecked = (cb1 && cb1.checked) || (cb2 && cb2.checked);
    if (cb1) cb1.checked = isChecked;
    if (cb2) cb2.checked = isChecked;
"""
text = text.replace(old_toggle, new_toggle)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Added Select All to grid')
