import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Fix the name rendering (JS side)
old_name_js = r"const first = String\(student\.first_name \|\| ''\)\.trim\(\);\s*const last = String\(student\.last_name \|\| ''\)\.trim\(\);\s*document\.getElementById\('profile-name-text'\)\.innerHTML = `\$\{last \|\| '-'} <span.*?</span>`;"
new_name_js = '''const arabicName = String(student.first_name || '').trim();
            const foreignName = String(student.last_name || '').trim();
            document.getElementById('profile-name-text').innerHTML = `${arabicName || '-'}`;
            const foreignNameEl = document.getElementById('profile-foreign-name-text');
            if (foreignNameEl) foreignNameEl.textContent = foreignName || '-';'''
c = re.sub(old_name_js, new_name_js, c, flags=re.DOTALL)

# 2. Add French name chip + Change ID text + Add Level Badge
# Let's find the General tab:
# <div class="chip" id="profile-name" ...>...</div>
# We will replace the whole profile-name chip to add the level badge, and then add the foreign name chip.

old_name_chip = r'<div class="chip" id="profile-name" style="background:rgba\(10,132,255,0\.15\); border-color:#0a84ff; color:#0a84ff; display:flex; justify-content:flex-start; align-items:center; gap:8px;">(.*?)<span id="profile-name-text">(.*?)</span></div>'
new_name_chip = r'''<div class="chip" id="profile-name" style="background:rgba(10,132,255,0.15); border-color:#0a84ff; color:#0a84ff; display:flex; justify-content:space-between; align-items:center; gap:8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        \1<span id="profile-name-text" style="font-size:1.1rem; font-weight:bold;">\2</span>
                    </div>
                    <div id="profile-level-badge" style="background:var(--accent); color:white; padding:4px 10px; border-radius:12px; font-size:0.8rem; font-weight:bold;">-</div>
                </div>
                <div class="chip" id="profile-foreign-name" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">
                    🌍 Nom étranger : <span id="profile-foreign-name-text" dir="ltr">-</span>
                </div>'''
c = re.sub(old_name_chip, new_name_chip, c)

# 3. Change "ID académique" to "Numéro Étudiant" and color it.
# It is located in the Academy tab probably, or maybe I moved it. Wait, the user said "toi tu as mis ID ... Tu mets juste le numéro étudiant ... Et tu changes de couleur"
c = c.replace('🎓 Num. Étudiant', '🎓 Numéro Étudiant')
c = c.replace('id="profile-studentid" style="background:var(--surface)', 'id="profile-studentid" style="background:rgba(52,199,89,0.15); border-color:#34c759; color:#34c759"')

# 4. Sheet Badge in source
old_src = r"const srcEl = document\.getElementById\('profile-source-text'\);\s*if\(srcEl\) srcEl\.textContent = student\.source \|\| ' ';"
new_src = '''const srcEl = document.getElementById('profile-source-text');
            if(srcEl) {
                const s = String(student.source || '').toLowerCase();
                if(s.includes('sheet') || s.includes('google')) {
                    srcEl.innerHTML = '<span style="background:#0f9d58; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:0.8rem;">Sheet</span>';
                } else if(s.includes('excel')) {
                    srcEl.innerHTML = '<span style="background:#107c41; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:0.8rem;">Excel</span>';
                } else {
                    srcEl.textContent = student.source || '-';
                }
            }'''
c = re.sub(old_src, new_src, c)

# Update level badge logic
level_logic = '''
            // Set level badge
            const yr = String(student.year || '').trim();
            const lvlBadge = document.getElementById('profile-level-badge');
            if(lvlBadge) {
                if(yr === '1') lvlBadge.textContent = '1ère Année';
                else if(yr === '2') lvlBadge.textContent = '2ème Année';
                else if(yr === '3') lvlBadge.textContent = '3ème Année';
                else if(yr === '4') lvlBadge.textContent = '4ème Année';
                else lvlBadge.textContent = 'Année: ' + yr;
            }
'''
if 'lvlBadge' not in c:
    c = c.replace("const g = String(student.gender || '').toLowerCase();", level_logic + "\n            const g = String(student.gender || '').toLowerCase();")


with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("SUCCESS: Profile fixes applied.")
