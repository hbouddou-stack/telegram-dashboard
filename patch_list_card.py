import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update List Card rendering in JS
old_list_render = r'''<div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="display:flex;align-items:center;gap:6px;font-weight:800;font-size:0.95rem;color:var(--text1);">
                            \$\{dot\} \$\{String\(s\.first_name \|\| ''\)\} \$\{String\(s\.last_name \|\| ''\)\}
                        </div>
                        \$\{payBadge\}
                    </div>
                    <div style="font-size:0.8rem;color:var(--text2);" dir="ltr">\$\{String\(s\.email \|\| ''\)\}</div>
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        \$\{acaId \? `<span style="font-size:0.72rem;background:rgba\(0,0,0,0.1\);color:var\(--text1\);padding:2px 8px;border-radius:10px;font-family:monospace;font-weight:bold;">ID: \$\{acaId\}</span>` : ''\}
                        \$\{yearAr \? `<span style="font-size:0.72rem;background:rgba\(255,159,10,0.15\);color:#ff9f0a;padding:2px 8px;border-radius:10px;font-weight:600;">\$\{yearAr\}</span>` : ''\}'''

new_list_render = r'''<div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div style="display:flex;flex-direction:column;gap:2px;">
                            <div style="display:flex;align-items:center;gap:6px;font-weight:800;font-size:0.95rem;color:var(--text1);">
                                ${dot} ${String(s.first_name || '')}
                            </div>
                            ${s.last_name ? `<div style="font-size:0.8rem;color:var(--text2);margin-right:16px;">${String(s.last_name)}</div>` : ''}
                        </div>
                        ${payBadge}
                    </div>
                    <div style="font-size:0.8rem;color:var(--text2); margin-top:4px;" dir="ltr">${String(s.email || '')}</div>
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap; margin-top:4px;">
                        ${acaId ? `<span style="font-size:0.72rem;background:rgba(52,199,89,0.15);color:#34c759;padding:2px 8px;border-radius:10px;font-weight:bold;">رقم الطالب: ${acaId}</span>` : ''}
                        ${s.year ? `<span style="font-size:0.72rem;background:var(--accent);color:white;padding:2px 8px;border-radius:10px;font-weight:bold;">السنة الدراسية: ${s.year}</span>` : ''}
                        ${s.school_level ? `<span style="font-size:0.72rem;background:#0088cc;color:white;padding:2px 8px;border-radius:10px;font-weight:bold;">المستوى الدراسي: ${s.school_level}</span>` : ''}'''

c = re.sub(old_list_render, new_list_render, c)


# 2. Revert the level badge in the Modal header!
# Find the chip with profile-name and strip out the profile-level-badge.
old_name_chip = r'''<div class="chip" id="profile-name" style="background:rgba\(10,132,255,0.15\); border-color:#0a84ff; color:#0a84ff; display:flex; justify-content:space-between; align-items:center; gap:8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        (.*?)<span id="profile-name-text" style="font-size:1.1rem; font-weight:bold;">(.*?)</span>
                    </div>
                    <div id="profile-level-badge" style="background:var\(--accent\); color:white; padding:4px 10px; border-radius:12px; font-size:0.8rem; font-weight:bold;">-</div>
                </div>
                <div class="chip" id="profile-foreign-name" style="background:var\(--surface\); display:flex; justify-content:flex-start; align-items:center; gap:8px;">
                    🌍 Nom étranger : <span id="profile-foreign-name-text" dir="ltr">-</span>
                </div>'''

new_name_chip = r'''<div class="chip" id="profile-name" style="background:rgba(10,132,255,0.15); border-color:#0a84ff; color:#0a84ff; display:flex; justify-content:flex-start; align-items:center; gap:8px;">
                    \1<span id="profile-name-text" style="font-size:1.1rem; font-weight:bold;">\2</span>
                </div>
                <div class="chip" id="profile-foreign-name" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">
                    🌍 الاسم باللغة الأجنبية : <span id="profile-foreign-name-text" dir="ltr">-</span>
                </div>'''
c = re.sub(old_name_chip, new_name_chip, c)


# 3. Move Year and School Level from General Tab to Academy Tab
old_general_chips = r'''<div class="chip" id="profile-year" style="background:rgba\(255,159,10,0.15\); border-color:#ff9f0a; color:#ff9f0a; display:flex; justify-content:flex-start; align-items:center; gap:8px;">🎓 Niveau / Année : <span id="profile-year-text" style="font-weight:bold;">-</span></div>
    <div class="chip" id="profile-school-level" style="background:var\(--surface\); display:flex; justify-content:flex-start; align-items:center; gap:8px;">🏫 Niveau scolaire : <span id="profile-school-level-text" style="font-weight:bold;">-</span></div>'''

c = re.sub(old_general_chips, '', c)

# Insert them into Academy Tab
academy_target = r'<div id="mcontent-academy" class="mcontent" style="overflow-y:auto; flex:1; padding-right:5px;">'
new_academy_chips = r'''<div id="mcontent-academy" class="mcontent" style="overflow-y:auto; flex:1; padding-right:5px;">
                <div class="chip" id="profile-year" style="background:rgba(255,159,10,0.15); border-color:#ff9f0a; color:#ff9f0a; display:flex; justify-content:flex-start; align-items:center; gap:8px;">🎓 السنة الدراسية : <span id="profile-year-text" style="font-weight:bold;">-</span></div>
                <div class="chip" id="profile-school-level" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">🏫 المستوى الدراسي : <span id="profile-school-level-text" style="font-weight:bold;">-</span></div>'''
c = c.replace(academy_target, new_academy_chips)


# Write changes
with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("SUCCESS")
