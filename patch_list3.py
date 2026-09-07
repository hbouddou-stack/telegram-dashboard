import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

pattern = r'div\.innerHTML = `\s*<div style="display:flex;justify-content:space-between;align-items:center;">\s*<div style="display:flex;align-items:center;gap:6px;font-weight:800;font-size:0\.95rem;color:var\(--text1\);">\s*\$\{dot\} \$\{String\(s\.first_name \|\| \'\'\)\} \$\{String\(s\.last_name \|\| \'\'\)\}\s*</div>\s*\$\{payBadge\}\s*</div>\s*<div style="font-size:0\.8rem;color:var\(--text2\);" dir="ltr">\$\{String\(s\.email \|\| \'\'\)\}</div>\s*<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">.*?</div>\s*\$\{tgLine\}\s*`;'

new_list_render = r'''div.innerHTML = `
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
                        ${s.year ? `<span style="font-size:0.72rem;background:var(--accent);color:white;padding:2px 8px;border-radius:10px;font-weight:bold;">السنة الدراسية: ${s.year}</span>` : ''}
                        ${s.school_level ? `<span style="font-size:0.72rem;background:#0088cc;color:white;padding:2px 8px;border-radius:10px;font-weight:bold;">المستوى الدراسي: ${s.school_level}</span>` : ''}
                        <span style="font-size:0.72rem;color:var(--text2);">. ${src}</span>
                    </div>
                    ${tgLine}
                `;'''

c = re.sub(pattern, new_list_render, c, flags=re.DOTALL)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('SUCCESS')
