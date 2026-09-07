import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# --- 1. Inject the Style Selector UI ---
# Find search-input
search_input_pattern = r'<input class="search-box" type="text" id="search-input".*?>'
match = re.search(search_input_pattern, c)
if match and 'card-style-selector' not in c:
    selector_html = '''
        <div style="display:flex; justify-content:space-between; align-items:center; padding: 10px 15px; border-bottom: 1px solid var(--border);">
            <div style="font-weight: 800; color: var(--text1); font-size: 0.9rem;" id="students-count-display"></div>
            <select id="card-style-selector" onchange="changeCardStyle(this.value)" style="padding:4px 8px; border-radius:6px; border:1px solid var(--border); background:var(--bg); color:var(--text1); font-size:0.8rem; outline:none;">
                <option value="1">✨ النموذج 1 (كلاسيكي)</option>
                <option value="2">📋 النموذج 2 (حالة)</option>
                <option value="3">📱 النموذج 3 (مدمج)</option>
            </select>
        </div>
        <script>
            let currentCardStyle = localStorage.getItem('cardStyle') || '1';
            document.addEventListener("DOMContentLoaded", () => {
                const sel = document.getElementById('card-style-selector');
                if (sel) sel.value = currentCardStyle;
            });
            function changeCardStyle(style) {
                currentCardStyle = style;
                localStorage.setItem('cardStyle', style);
                filterStudents();
            }
        </script>'''
    
    # We also need to remove the old <div id="students-count-display"...> if it exists
    old_count_pattern = r'<div id="students-count-display".*?</div>'
    c = re.sub(old_count_pattern, '', c)
    
    c = c[:match.end()] + selector_html + c[match.end():]
    print("Injected Style Selector")

# --- 2. Update the list item rendering logic ---
render_block_pattern = re.compile(r'// Source\s*\n\s*const srcStr = .*?fragment\.appendChild\(div\);', re.DOTALL)

new_render_block = r'''// Extract Year correctly (avoid "Niveau Niveau")
                let yearNum = '';
                if (s.year) {
                    const yrMatch = String(s.year).match(/\d+/);
                    yearNum = yrMatch ? yrMatch[0] : '';
                }
                const yearBadgeHTML = yearNum ? `<span style="font-size:0.72rem;background:var(--accent);color:white;padding:2px 8px;border-radius:10px;font-weight:bold;">المستوى ${yearNum}</span>` : '';

                // Source Badge
                const srcStr = String(s.source || '').toLowerCase();
                let srcBadge = `<span style="font-size:0.72rem;color:var(--text2);">&#1605;. ${s.source || '-'}</span>`;
                if (srcStr.includes('sheet') || srcStr.includes('google')) {
                    srcBadge = `<span style="background:#0f9d58; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:0.72rem;">Sheet</span>`;
                } else if (srcStr.includes('excel')) {
                    srcBadge = `<span style="background:#107c41; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:0.72rem;">Excel</span>`;
                }

                // Colored Email
                const coloredEmail = s.email ? `<span style="font-size:0.8rem; color:#0a84ff; background:rgba(10,132,255,0.1); padding:2px 6px; border-radius:4px;" dir="ltr">${String(s.email)}</span>` : '';
                
                // Names
                const arName = String(s.first_name || '');
                const frNameHTML = s.last_name ? `<div style="font-size:0.85rem;color:var(--text2);">${String(s.last_name)}</div>` : '';

                // Telegram info
                let tgLine = '';
                if (linked) {
                    let tgName = String(s.tg_first_name || '');
                    if (s.tg_last_name) tgName += ' ' + String(s.tg_last_name);
                    const tgUser = s.telegram_username ? `@${s.telegram_username}` : '';
                    tgLine = `<div style="font-size:0.78rem;color:#0088cc;display:flex;align-items:center;gap:4px;">✈️ ${tgUser || tgName.trim() || 'مرتبط'}</div>`;
                }

                const acaId = String(s.academic_id || s.student_id || '').trim();
                
                // Templates
                const styleOpt = (typeof currentCardStyle !== 'undefined') ? currentCardStyle : '1';

                if (styleOpt === '2') {
                    // Template 2: Status Kanban Style
                    const isPaidColor = (paid && (paid.includes('PAID') || paid.includes('OUI') || paid.includes('مدفوع'))) ? '#16a34a' : '#ef4444';
                    // We don't overwrite the border completely if it's already set by gender, but let's just make it a clean card
                    div.innerHTML = `
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div style="font-weight:900;font-size:1.15rem;color:var(--text1);">
                                ${arName}
                            </div>
                            <div style="display:flex; gap:4px; align-items:center;">
                                ${payBadge}
                            </div>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                            ${frNameHTML}
                        </div>
                        <div style="margin-top:8px;">${coloredEmail}</div>
                        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap; margin-top:12px; background:rgba(255,255,255,0.03); padding:8px; border-radius:8px; border: 1px solid var(--border);">
                            ${dot} 
                            ${acaId ? `<span style="font-size:0.75rem;color:var(--text2);font-weight:bold;">رقم: ${acaId}</span>` : ''}
                            ${yearNum ? `<span style="font-size:0.75rem;color:var(--text2);font-weight:bold;">| المستوى ${yearNum}</span>` : ''}
                            ${srcBadge ? `<span style="font-size:0.75rem;color:var(--text2);font-weight:bold;">| ${srcBadge}</span>` : ''}
                        </div>
                        ${tgLine ? `<div style="margin-top:8px;">${tgLine}</div>` : ''}
                    `;
                } else if (styleOpt === '3') {
                    // Template 3: Dense and Compact
                    div.style.padding = '8px 12px'; // tighter padding
                    div.innerHTML = `
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div style="display:flex;align-items:center;gap:6px;font-weight:800;font-size:0.95rem;color:var(--text1);">
                                ${dot} ${arName} ${s.last_name ? `<span style="font-size:0.8rem;color:var(--text2);font-weight:normal;">(${String(s.last_name)})</span>` : ''}
                            </div>
                            <div style="display:flex;align-items:center;gap:4px;">
                                ${payBadge}
                                ${yearBadgeHTML}
                            </div>
                        </div>
                        <div style="display:flex;justify-content:space-between;align-items:center; margin-top:6px;">
                            ${coloredEmail}
                            ${tgLine}
                        </div>
                    `;
                } else {
                    // Template 1: Classic Enhanced (Default)
                    div.innerHTML = `
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div style="display:flex;flex-direction:column;gap:2px;">
                                <div style="display:flex;align-items:center;gap:6px;font-weight:900;font-size:1.15rem;color:var(--text1);">
                                    ${dot} ${arName}
                                </div>
                                ${frNameHTML}
                            </div>
                            ${payBadge}
                        </div>
                        <div style="margin-top:8px;">${coloredEmail}</div>
                        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap; margin-top:10px;">
                            ${acaId ? `<span style="font-size:0.72rem;background:rgba(52,199,89,0.15);color:#34c759;padding:2px 8px;border-radius:10px;font-weight:bold;">رقم الطالب: ${acaId}</span>` : ''}
                            ${yearBadgeHTML}
                            ${srcBadge}
                        </div>
                        ${tgLine ? `<div style="margin-top:8px;">${tgLine}</div>` : ''}
                    `;
                }
                
                fragment.appendChild(div);'''

if render_block_pattern.search(c):
    c = render_block_pattern.sub(new_render_block, c)
    print("Patched rendering logic")
else:
    print("Could not find rendering logic")

# In case the old code still had 'Niveau Niveau', let's check
with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
