import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Action "essaie d un lien invalide" (APP_OPENED_UNLINKED / LINK_FAILED / etc.) -> red
# (We already changed APP_OPENED_UNLINKED to red, but what if they meant LINK_FAILED? Let's make sure it's red).
# And let's update LOG_RULES for the filters at the top of logs.

# 2. Log filters at the top:
log_filters_old = '''<div class="chip active" id="filter-log-all" onclick="setLogFilter('ALL')">الكل</div>
            <div class="chip" id="filter-log-success" onclick="setLogFilter('SUCCESS')">الربط الناجح</div>
            <div class="chip" id="filter-log-fail" onclick="setLogFilter('FAIL')">فشل الربط</div>
            <div class="chip" id="filter-log-app" onclick="setLogFilter('APP')">دخول المنصة</div>
            <div class="chip" id="filter-log-tuto" onclick="setLogFilter('TUTO')">الشروحات</div>'''
log_filters_new = '''<div class="chip active" id="filter-log-all" onclick="setLogFilter('ALL')">الكل</div>
            <div class="chip" id="filter-log-success" onclick="setLogFilter('SUCCESS')">🟢 نجاح (الربط)</div>
            <div class="chip" id="filter-log-fail" onclick="setLogFilter('FAIL')">🔴 فشل / رفض</div>
            <div class="chip" id="filter-log-app" onclick="setLogFilter('APP')">🔵 التصفح والدراسة</div>
            <div class="chip" id="filter-log-comm" onclick="setLogFilter('COMM')">🟠 المراسلات (إيميل/واتساب)</div>'''
c = c.replace(log_filters_old, log_filters_new)

setLogFilter_old = '''if (currentLogFilter === 'SUCCESS') {
                filteredLogs = filteredLogs.filter(l => l.action_type === 'LINK_SUCCESS' || l.action_type === 'ACCOUNT_LINKED');
            } else if (currentLogFilter === 'FAIL') {
                filteredLogs = filteredLogs.filter(l => l.action_type === 'LINK_FAILED');
            } else if (currentLogFilter === 'APP') {
                filteredLogs = filteredLogs.filter(l => l.action_type === 'APP_OPENED' || l.action_type === 'APP_OPENED_UNLINKED');
            } else if (currentLogFilter === 'TUTO') {
                filteredLogs = filteredLogs.filter(l => l.action_type === 'TUTO_OPENED');
            }'''

setLogFilter_new = '''if (currentLogFilter === 'SUCCESS') {
                filteredLogs = filteredLogs.filter(l => getLogStyle(l.action_type).text === '#16a34a' || l.action_type.includes('SUCCESS'));
            } else if (currentLogFilter === 'FAIL') {
                filteredLogs = filteredLogs.filter(l => getLogStyle(l.action_type).text === '#dc2626' || l.action_type.includes('FAILED') || l.action_type.includes('UNLINKED'));
            } else if (currentLogFilter === 'APP') {
                filteredLogs = filteredLogs.filter(l => getLogStyle(l.action_type).text === '#2563eb' || l.action_type.includes('OPEN') || l.action_type.includes('CLICK') || l.action_type.includes('QUIZ'));
            } else if (currentLogFilter === 'COMM') {
                filteredLogs = filteredLogs.filter(l => getLogStyle(l.action_type).text === '#d97706' || l.action_type.includes('SENT'));
            }'''
c = c.replace(setLogFilter_old, setLogFilter_new)


# 3. Le filtre niveau qui ne fonctionne pas
matchLevel_old = '''const yr = String(s.year || '');
                const matchYr = yr.match(/\d+/);
                const yrNum = matchYr ? matchYr[0] : yr;
                const matchLevel = filters.level === 'all' || yrNum === filters.level || yr.includes(filters.level);'''
matchLevel_new = '''const yr = String(s.year || '');
                const yrLower = yr.toLowerCase();
                const matchLevel = filters.level === 'all' 
                    || yrLower.includes(filters.level)
                    || (filters.level === '1' && (yrLower.includes('أول') || yrLower.includes('1')))
                    || (filters.level === '2' && (yrLower.includes('ثاني') || yrLower.includes('2')))
                    || (filters.level === '3' && (yrLower.includes('ثالث') || yrLower.includes('3')))
                    || (filters.level === '4' && (yrLower.includes('رابع') || yrLower.includes('4')));'''
c = c.replace(matchLevel_old, matchLevel_new)


# 4. Carte étudiant (Entièrement coloré bleu ou rose + Numéro étudiant)
card_gender_old = '''const g = String(s.gender || '').toLowerCase();
                if (g.startsWith('h') || g === 'm' || g === 'male' || g.includes('ذكر')) {
                    div.style.borderRight = '5px solid #0084ff';
                } else if (g.startsWith('f') || g === 'female' || g === 'fille' || g.includes('أنثى')) {
                    div.style.borderRight = '5px solid #ec4899';
                }'''
card_gender_new = '''const g = String(s.gender || '').toLowerCase();
                if (g.startsWith('h') || g === 'm' || g === 'male' || g.includes('ذكر')) {
                    div.style.borderRight = '5px solid #0084ff';
                    div.style.background = 'rgba(0, 132, 255, 0.06)';
                } else if (g.startsWith('f') || g === 'female' || g === 'fille' || g.includes('أنثى')) {
                    div.style.borderRight = '5px solid #ec4899';
                    div.style.background = 'rgba(236, 72, 153, 0.06)';
                }'''
c = c.replace(card_gender_old, card_gender_new)

# Add Academic ID to card
card_inner_old = '''div.innerHTML = `
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="display:flex;align-items:center;gap:6px;font-weight:800;font-size:0.95rem;color:var(--text1);">
                            ${dot} ${String(s.first_name || '')} ${String(s.last_name || '')}
                        </div>
                        ${payBadge}
                    </div>
                    <div style="font-size:0.8rem;color:var(--text2);" dir="ltr">${String(s.email || '')}</div>
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        ${yearAr ? `<span style="font-size:0.72rem;background:rgba(255,159,10,0.15);color:#ff9f0a;padding:2px 8px;border-radius:10px;font-weight:600;">${yearAr}</span>` : ''}
                        <span style="font-size:0.72rem;color:var(--text2);">م. ${src}</span>
                    </div>
                    ${tgLine}
                `;'''
card_inner_new = '''
                const acaId = String(s.academic_id || s.student_id || '').trim();
                div.innerHTML = `
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="display:flex;align-items:center;gap:6px;font-weight:800;font-size:0.95rem;color:var(--text1);">
                            ${dot} ${String(s.first_name || '')} ${String(s.last_name || '')}
                        </div>
                        ${payBadge}
                    </div>
                    <div style="font-size:0.8rem;color:var(--text2);" dir="ltr">${String(s.email || '')}</div>
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        ${acaId ? `<span style="font-size:0.72rem;background:rgba(0,0,0,0.1);color:var(--text1);padding:2px 8px;border-radius:10px;font-family:monospace;font-weight:bold;">ID: ${acaId}</span>` : ''}
                        ${yearAr ? `<span style="font-size:0.72rem;background:rgba(255,159,10,0.15);color:#ff9f0a;padding:2px 8px;border-radius:10px;font-weight:600;">${yearAr}</span>` : ''}
                        <span style="font-size:0.72rem;color:var(--text2);">م. ${src}</span>
                    </div>
                    ${tgLine}
                `;'''
# Wait, my regex might fail if `م.` is slightly different.
# Let's do a strict find/replace for the innerHTML part:
# Or just find `div.innerHTML = \`` and the end \`;`
card_inner_pattern = r"div\.innerHTML = `.*?`;"
# Wait, if I do this, it will match all `div.innerHTML = ` ! There's only one in that block though.
# Better to use re.sub cautiously.

import re
c = re.sub(r'div\.innerHTML = `\s*<div style="display:flex;justify-content:space-between;align-items:center;">.*?`;', card_inner_new.replace('div.innerHTML = `', 'div.innerHTML = `').strip(), c, flags=re.DOTALL)


# Also ensure LOG_RULES includes any variations of LINK_FAILED in red
link_failed_patch = r"'LINK_FAILED': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '❌', label: 'فشل الربط' },"
link_failed_replacement = link_failed_patch + r"\n            'LINK_INVALID': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '⛔', label: 'رابط غير صالح' },"
c = c.replace(link_failed_patch, link_failed_replacement)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Updates applied")
