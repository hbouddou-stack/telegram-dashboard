import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('function openDuplicateScanner() {')
idx2 = text.find('async function toggleDuplicateExclude')

old_part = text[idx1:idx2]

new_func = """function openDuplicateScanner() {
            const modal = document.getElementById('modal-duplicates');
            const container = document.getElementById('duplicates-container');
            
            if (!modal || !container) {
                alert("Erreur : elements introuvables.");
                return;
            }
            
            // KEY FIX: Move modal to document.body to escape any overflow:hidden or transform parent.
            // This is the standard fix for Telegram WebView position:fixed bugs.
            document.body.appendChild(modal);
            
            // Apply styles with !important via cssText to override anything
            modal.style.cssText = [
                'display: flex !important',
                'position: fixed !important',
                'top: 0 !important',
                'left: 0 !important',
                'right: 0 !important',
                'bottom: 0 !important',
                'width: 100% !important',
                'height: 100% !important',
                'z-index: 2147483647 !important',
                'background: rgba(0,0,0,0.88) !important',
                'align-items: flex-end !important',
                'justify-content: center !important',
                'margin: 0 !important',
                'padding: 0 !important',
                'box-sizing: border-box !important'
            ].join('; ');
            
            container.innerHTML = '<div style="text-align:center; padding:30px; font-weight:bold; font-size:1.1rem; color:var(--text1);">Analyse en cours...</div>';
            
            setTimeout(() => {
                try {
                    const groupsByName = {};
                    const groupsByEmail = {};
                    
                    allStudents.forEach(s => {
                        // By Name
                        let n = ((s.first_name || '') + ' ' + (s.last_name || '')).toLowerCase();
                        n = n.replace(/\\s+/g, '').replace(/[^\\u0600-\\u06FFa-z0-9-]/g, '');
                        if (n.length >= 3) {
                            if (!groupsByName[n]) groupsByName[n] = [];
                            groupsByName[n].push(s);
                        }
                        
                        // By Email
                        if (s.email && s.email.includes('@')) {
                            let e = s.email.toLowerCase().trim();
                            if (!groupsByEmail[e]) groupsByEmail[e] = [];
                            groupsByEmail[e].push(s);
                        }
                    });

                    const finalGroups = [];
                    const processedIds = new Set();
                    
                    Object.values(groupsByEmail).forEach(g => {
                        if (g.length > 1) {
                            finalGroups.push({ type: 'Email identique', students: g });
                            g.forEach(st => processedIds.add(st.student_id));
                        }
                    });
                    
                    Object.values(groupsByName).forEach(g => {
                        if (g.length > 1) {
                            const unhandled = g.filter(st => !processedIds.has(st.student_id));
                            if (unhandled.length > 1) {
                                finalGroups.push({ type: 'Nom identique', students: unhandled });
                                unhandled.forEach(st => processedIds.add(st.student_id));
                            }
                        }
                    });
                    
                    if (finalGroups.length === 0) {
                        container.innerHTML = '<div style="text-align:center; padding:40px; color:#10b981; font-weight:bold; font-size:1.2rem;">Aucun doublon detecte !</div>';
                        return;
                    }

                    let html = '';
                    finalGroups.forEach(groupObj => {
                        const group = groupObj.students;
                        group.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
                        const name = (group[0].first_name || '') + ' ' + (group[0].last_name || '');
                        
                        html += `<div style="border:1px solid var(--border); border-radius:12px; padding:12px; background:var(--bg); margin-bottom:10px;">
                            <h4 style="margin:0 0 10px 0; color:var(--text1); font-size:1rem;">${name} <span style="font-size:0.75rem; color:var(--text2);">(${group.length} comptes - ${groupObj.type})</span></h4>
                            <div style="display:flex; flex-direction:column; gap:8px;">`;
                        
                        group.forEach((s, idx) => {
                            const isNewest = (idx === 0);
                            const isExcluded = s.excluded == 1;
                            const dateStr = s.created_at ? new Date(s.created_at).toLocaleDateString('fr-FR') : '-';
                            const badgeColor = isExcluded ? '#64748b' : (isNewest ? '#10b981' : '#f59e0b');
                            const badgeText = isExcluded ? 'Exclu' : (isNewest ? 'Recent' : 'Ancien');
                            const opacity = isExcluded ? '0.5' : '1';
                            
                            html += `<div id="dup-row-${s.student_id}" style="display:flex; justify-content:space-between; align-items:center; padding:10px; background:var(--surface); border:1px solid var(--border); border-radius:8px; opacity:${opacity};">
                                <div style="flex:1; overflow:hidden;">
                                    <div style="font-size:0.85rem; font-weight:bold; color:var(--text1); word-break:break-all;">${s.email || '-'}</div>
                                    <div style="font-size:0.75rem; color:var(--text2); margin-top:4px;">${dateStr} | ${s.source_file || s.source || '-'} | ${s.payment_status === 'PAID' ? 'Paye' : 'Non Paye'}</div>
                                    <span style="font-size:0.7rem; background:${badgeColor}22; color:${badgeColor}; padding:2px 8px; border-radius:10px; font-weight:bold; display:inline-block; margin-top:4px;">${badgeText}</span>
                                </div>
                                <div style="margin-left:8px; flex-shrink:0;">
                                    ${isExcluded
                                        ? `<button onclick="toggleDuplicateExclude('${s.student_id}', 0)" style="background:var(--bg); border:1px solid var(--border); color:var(--text1); padding:6px 10px; border-radius:8px; cursor:pointer; font-size:0.8rem;">Reintegrer</button>`
                                        : `<button onclick="toggleDuplicateExclude('${s.student_id}', 1)" style="background:#ef4444; border:none; color:white; padding:6px 10px; border-radius:8px; cursor:pointer; font-size:0.8rem; font-weight:bold;">Exclure</button>`
                                    }
                                </div>
                            </div>`;
                        });
                        
                        html += `</div></div>`;
                    });
                    
                    container.innerHTML = html;
                } catch(err) {
                    alert("Erreur JS : " + err.message);
                    console.error(err);
                }
            }, 80);
        }

        """

text = text.replace(old_part, new_func)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Done - modal now appended to document.body on open')
