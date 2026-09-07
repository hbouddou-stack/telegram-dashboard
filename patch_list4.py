import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. We replace the section from "// Source" down to "fragment.appendChild(div);"

pattern = re.compile(r'// Source\s*\n\s*const src = String\(s\.source \|\| .*?;\s*\n\s*// Telegram info\s*\n\s*let tgLine = .*?fragment\.appendChild\(div\);', re.DOTALL)

replacement = r'''// Source
                const srcStr = String(s.source || '').toLowerCase();
                let srcBadge = `<span style="font-size:0.72rem;color:var(--text2);">&#1605;. ${s.source || '-'}</span>`;
                if (srcStr.includes('sheet') || srcStr.includes('google')) {
                    srcBadge = `<span style="background:#0f9d58; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:0.72rem;">Sheet</span>`;
                } else if (srcStr.includes('excel')) {
                    srcBadge = `<span style="background:#107c41; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:0.72rem;">Excel</span>`;
                }

                // Telegram info
                let tgLine = '';
                if (linked) {
                    let tgName = String(s.tg_first_name || '');
                    if (s.tg_last_name) tgName += ' ' + String(s.tg_last_name);
                    const tgUser = s.telegram_username ? `@${s.telegram_username}` : '';
                    tgLine = `<div style="font-size:0.78rem;color:#0088cc;display:flex;align-items:center;gap:4px;">✈️ ${tgUser || tgName.trim() || 'مرتبط'}</div>`;
                }

                const acaId = String(s.academic_id || s.student_id || '').trim();
                
                div.innerHTML = `
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div style="display:flex;flex-direction:column;gap:2px;">
                            <div style="display:flex;align-items:center;gap:6px;font-weight:800;font-size:0.95rem;color:var(--text1);">
                                ${dot} ${String(s.first_name || '')}
                            </div>
                            ${s.last_name ? `<div style="font-size:0.8rem;color:var(--text2);margin-right:16px;">${String(s.last_name)}</div>` : ''}
                        </div>
                        ${payBadge}
                    </div>
                    <div style="font-size:0.8rem;color:var(--text2); margin-top:4px;" dir="ltr">${String(s.email || '')}</div>
                    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap; margin-top:4px;">
                        ${acaId ? `<span style="font-size:0.72rem;background:rgba(52,199,89,0.15);color:#34c759;padding:2px 8px;border-radius:10px;font-weight:bold;">رقم الطالب: ${acaId}</span>` : ''}
                        ${s.year ? `<span style="font-size:0.72rem;background:var(--accent);color:white;padding:2px 8px;border-radius:10px;font-weight:bold;">المستوى ${s.year}</span>` : ''}
                        ${srcBadge}
                    </div>
                    ${tgLine}
                `;
                fragment.appendChild(div);'''

if pattern.search(c):
    c = pattern.sub(replacement, c)
    print("SUCCESS: Found and replaced the block!")
else:
    print("ERROR: Regex did not match.")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
