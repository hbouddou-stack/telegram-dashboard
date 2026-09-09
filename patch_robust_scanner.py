import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Completely rewrite the openDuplicateScanner function
old_func_regex = r"function openDuplicateScanner\(\) \{.*?\n        \}\n\n        async function toggleDuplicateExclude"
new_func = """function openDuplicateScanner() {
            const container = document.getElementById('duplicates-container');
            const modal = document.getElementById('modal-duplicates');
            
            if(!container || !modal) {
                alert("Erreur critique : la fenêtre modale est introuvable dans le code HTML.");
                return;
            }

            container.innerHTML = '<div style="text-align:center; padding:20px; font-weight:bold; font-size:1.2rem;">Analyse en cours...</div>';
            
            // Force styles just in case CSS fails
            modal.style.display = 'flex';
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.right = '0';
            modal.style.bottom = '0';
            modal.style.zIndex = '999999';
            modal.style.background = 'rgba(0,0,0,0.85)';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';

            setTimeout(() => {
                try {
                    const groupsByName = {};
                    const groupsByEmail = {};
                    
                    // Group by normalized name AND email
                    allStudents.forEach(s => {
                        // 1. By Name
                        let n = ((s.first_name || '') + ' ' + (s.last_name || '')).toLowerCase();
                        n = n.replace(/\s+/g, '').replace(/[^a-z0-9\u0600-\u06FF-]/g, ''); // Keep Arabic and letters
                        if (n.length >= 3) {
                            if (!groupsByName[n]) groupsByName[n] = [];
                            groupsByName[n].push(s);
                        }
                        
                        // 2. By Email
                        if (s.email && s.email.includes('@')) {
                            let e = s.email.toLowerCase().trim();
                            if (!groupsByEmail[e]) groupsByEmail[e] = [];
                            groupsByEmail[e].push(s);
                        }
                    });

                    // Merge groups
                    const finalGroups = [];
                    const processedIds = new Set();
                    
                    // Add email duplicates first
                    Object.values(groupsByEmail).forEach(g => {
                        if (g.length > 1) {
                            finalGroups.push({ type: 'Email identique', students: g });
                            g.forEach(st => processedIds.add(st.student_id));
                        }
                    });
                    
                    // Add name duplicates (excluding those already caught by email)
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
                        container.innerHTML = '<div style="text-align:center; padding:40px; color:#10b981; font-weight:bold; font-size:1.2rem;">✅ Aucun doublon détecté !</div>';
                        return;
                    }

                    let html = '';
                    finalGroups.forEach(groupObj => {
                        const group = groupObj.students;
                        // Sort group by date descending (newest first)
                        group.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
                        
                        const name = (group[0].first_name || '') + ' ' + (group[0].last_name || '');
                        
                        html += `<div style="border:1px solid var(--border); border-radius:12px; padding:12px; background:var(--bg);">
                            <h4 style="margin:0 0 10px 0; color:var(--text1); font-size:1rem;">🧑‍🎓 ${name} <span style="font-size:0.75rem; color:var(--text2);">(${group.length} comptes - ${groupObj.type})</span></h4>
                            <div style="display:flex; flex-direction:column; gap:8px;">`;
                        
                        group.forEach((s, idx) => {
                            const isNewest = (idx === 0);
                            const isExcluded = s.excluded == 1;
                            const dateStr = s.created_at ? new Date(s.created_at).toLocaleDateString('fr-FR') : '-';
                            const badgeColor = isExcluded ? '#64748b' : (isNewest ? '#10b981' : '#f59e0b');
                            const badgeText = isExcluded ? 'Exclu 👻' : (isNewest ? 'Le plus récent ⭐' : 'Ancien');
                            const opacity = isExcluded ? '0.5' : '1';
                            
                            html += `
                                <div id="dup-row-${s.student_id}" style="display:flex; justify-content:space-between; align-items:center; padding:10px; background:var(--surface); border:1px solid var(--border); border-radius:8px; opacity:${opacity};">
                                    <div>
                                        <div style="font-size:0.85rem; font-weight:bold; color:var(--text1);">${s.email || '-'}</div>
                                        <div style="font-size:0.75rem; color:var(--text2); margin-top:4px;">
                                            📅 ${dateStr} | 📂 Source: ${s.source_file || s.source || '-'} | 💳 ${s.payment_status === '' || s.payment_status === 'PAID' ? 'Payé' : 'Non Payé'}
                                        </div>
                                        <div style="margin-top:6px;">
                                            <span style="font-size:0.7rem; background:${badgeColor}22; color:${badgeColor}; padding:2px 8px; border-radius:10px; font-weight:bold;">${badgeText}</span>
                                        </div>
                                    </div>
                                    <div>
                                        ${isExcluded 
                                            ? `<button onclick="toggleDuplicateExclude('${s.student_id}', 0)" style="background:var(--bg); border:1px solid var(--border); color:var(--text1); padding:6px 10px; border-radius:8px; cursor:pointer; font-size:0.8rem;">🔄 Réintégrer</button>`
                                            : `<button onclick="toggleDuplicateExclude('${s.student_id}', 1)" style="background:#ef4444; border:none; color:white; padding:6px 10px; border-radius:8px; cursor:pointer; font-size:0.8rem; font-weight:bold;">👻 Exclure</button>`
                                        }
                                    </div>
                                </div>
                            `;
                        });
                        
                        html += `</div></div>`;
                    });
                    
                    container.innerHTML = html;
                } catch(err) {
                    alert("Erreur JS interne : " + err.message);
                    console.error(err);
                    container.innerHTML = '<div style="color:red; padding:20px;">Erreur critique.</div>';
                }
            }, 50);
        }

        async function toggleDuplicateExclude"""

text = re.sub(old_func_regex, new_func, text, flags=re.DOTALL)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Rewrote openDuplicateScanner')
