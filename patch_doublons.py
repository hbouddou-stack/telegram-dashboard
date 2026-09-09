import io
import re

# 1. Update Backend (main.py)
with io.open('main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

endpoint_code = """
async def api_admin_gateway_toggle_exclude(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        student_id = data.get('student_id')
        excluded = int(data.get('excluded', 1))
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("UPDATE academy_students SET excluded = ? WHERE student_id = ?", (excluded, student_id))
            await db.commit()
        return web.json_response({"success": True})
    except Exception as e:
        import logging
        logging.getLogger('main').error(f"Error in toggle_exclude: {e}")
        return web.json_response({"success": False, "error": str(e)})
"""

if 'api_admin_gateway_toggle_exclude' not in main_code:
    main_code = main_code.replace("async def api_admin_gateway_students", endpoint_code + "\nasync def api_admin_gateway_students")

if '/api/admin/gateway/toggle_exclude' not in main_code:
    main_code = main_code.replace(
        "app.router.add_get('/api/admin/gateway/students', api_admin_gateway_students)",
        "app.router.add_get('/api/admin/gateway/students', api_admin_gateway_students)\n    app.router.add_post('/api/admin/gateway/toggle_exclude', api_admin_gateway_toggle_exclude)"
    )

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)


# 2. Update Frontend (admin_gateway.html)
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 2a. Add the "Scanner" button next to the search box
search_html_old = """<input class="search-box" type="text" id="search-input" """
search_html_new = """<div style="display:flex; gap:8px;">
                <input style="flex:1;" class="search-box" type="text" id="search-input" """
html = html.replace(search_html_old, search_html_new)

# Close the flex div and add the scanner button right after the sort button logic
if 'id="view-toggle-btn"' in html:
    # We will inject the button before the view toggle
    btn_html = """<button onclick="openDuplicateScanner()" style="background:#8b5cf6; color:white; border:none; border-radius:12px; padding:8px 12px; font-weight:bold; cursor:pointer;" title="Scanner les doublons">🔍 Doublons</button>"""
    html = html.replace('<button id="view-toggle-btn"', btn_html + '\n                <button id="view-toggle-btn"')
    
    # close the flex container
    html = html.replace('</div>\n        <!-- STUDENTS GRID/LIST -->', '</div>\n            </div>\n        <!-- STUDENTS GRID/LIST -->')


# 2b. Add the Modal HTML
modal_html = """
    <!-- MODAL DOUBLONS -->
    <div id="modal-duplicates" class="modal-overlay">
        <div style="background:var(--surface); width:100%; max-width:650px; max-height:85vh; border-radius:20px 20px 0 0; padding:20px; overflow-y:auto; display:flex; flex-direction:column;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <h3 style="margin:0; font-size:1.2rem; color:var(--text1);">🔍 Scanner de Doublons</h3>
                <button onclick="document.getElementById('modal-duplicates').style.display='none'; fetchStudents();" style="background:var(--bg); border:1px solid var(--border); color:var(--text1); padding:5px 12px; border-radius:8px; cursor:pointer;">Fermer</button>
            </div>
            <p style="font-size:0.85rem; color:var(--text2); margin-top:0;">Les élèves avec un prénom et nom identiques (ou très similaires) sont regroupés ci-dessous. Excluez les anciens profils pour nettoyer votre base.</p>
            <div id="duplicates-container" style="display:flex; flex-direction:column; gap:15px; margin-top:10px;">
                <!-- Content injected via JS -->
            </div>
        </div>
    </div>
"""
if 'modal-duplicates' not in html:
    html = html.replace('</body>', modal_html + '\n</body>')


# 2c. Add the JS logic
js_logic = """
        // ===== DUPLICATE SCANNER =====
        function openDuplicateScanner() {
            const container = document.getElementById('duplicates-container');
            container.innerHTML = '<div style="text-align:center; padding:20px;">Analyse en cours...</div>';
            document.getElementById('modal-duplicates').style.display = 'flex';

            setTimeout(() => {
                const groups = {};
                
                // Group by normalized name
                allStudents.forEach(s => {
                    let n = ((s.first_name || '') + ' ' + (s.last_name || '')).toLowerCase();
                    // Remove common titles, spaces, and special chars to match closely
                    n = n.replace(/[^a-z0-9أ-ي]/g, '');
                    if (n.length < 3) return; // ignore too short names
                    
                    if (!groups[n]) groups[n] = [];
                    groups[n].push(s);
                });

                // Filter groups with > 1 student
                const duplicates = Object.values(groups).filter(g => g.length > 1);
                
                if (duplicates.length === 0) {
                    container.innerHTML = '<div style="text-align:center; padding:40px; color:#10b981; font-weight:bold;">✅ Aucun doublon détecté !</div>';
                    return;
                }

                let html = '';
                duplicates.forEach(group => {
                    // Sort group by date descending (newest first)
                    group.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
                    
                    const name = (group[0].first_name || '') + ' ' + (group[0].last_name || '');
                    
                    html += `<div style="border:1px solid var(--border); border-radius:12px; padding:12px; background:var(--bg);">
                        <h4 style="margin:0 0 10px 0; color:var(--text1); font-size:1rem;">🧑‍🎓 ${name} <span style="font-size:0.75rem; color:var(--text2);">(${group.length} comptes)</span></h4>
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
                                        📅 ${dateStr} | 📄 Source: ${s.source_file || s.source || '-'} | 💳 ${s.payment_status === 'مسدد' || s.payment_status === 'PAID' ? 'Payé' : 'Non Payé'}
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
            }, 100);
        }

        async function toggleDuplicateExclude(studentId, excludedState) {
            try {
                const res = await fetch('/api/admin/gateway/toggle_exclude', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ student_id: studentId, excluded: excludedState })
                });
                const data = await res.json();
                if(data.success) {
                    // Update local data so we don't have to fetch everything immediately
                    const student = allStudents.find(s => s.student_id === studentId);
                    if (student) student.excluded = excludedState;
                    
                    // Re-render the scanner to update UI
                    openDuplicateScanner();
                } else {
                    alert('Erreur : ' + (data.error || 'Inconnue'));
                }
            } catch(e) {
                alert('Erreur réseau');
            }
        }
"""
if 'openDuplicateScanner' not in html:
    html = html.replace('function filterStudents()', js_logic + '\n        function filterStudents()')


# 2d. Hide excluded students from dashboard KPIs (important)
html = html.replace(
    "const subset = allStudents.filter(s => {",
    "const subset = allStudents.filter(s => {\n        if (s.excluded == 1) return false; // Ignore excluded students in KPIs"
)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Duplicate scanner injected.")
