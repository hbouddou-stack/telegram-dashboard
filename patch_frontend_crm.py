import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add Tab Button
tab_target = r'<div class="mtab" onclick="switchModalTab(\'telegram\')" id="tab-telegram"> Telegram</div>'
new_tab = r'''<div class="mtab" onclick="switchModalTab('telegram')" id="tab-telegram"> Telegram</div>
                <div class="mtab" onclick="switchModalTab('crm')" id="tab-crm">📝 CRM</div>'''
if "id=\"tab-crm\"" not in c:
    c = re.sub(tab_target, new_tab, c)

# 2. Add Tab Content
mcontent_target = r'<!-- Tab 4: Funnel -->'
new_mcontent = r'''<!-- Tab CRM -->
            <div id="mcontent-crm" class="mcontent" style="flex-direction:column; flex:1; overflow:hidden;">
                <!-- Top Action Area -->
                <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:15px; margin-bottom:15px;">
                    <h4 style="margin:0 0 10px 0; font-size:0.9rem; color:var(--text1);">➕ Ajouter une Note</h4>
                    <div style="display:flex; gap:10px; margin-bottom:10px;">
                        <select id="crm-type" style="padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none; flex:1;">
                            <option value="APPEL">📞 Appel</option>
                            <option value="WHATSAPP">💬 WhatsApp</option>
                            <option value="EMAIL">📧 Email</option>
                            <option value="AUTRE">📌 Autre</option>
                        </select>
                        <select id="crm-tag" style="padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none; flex:1;">
                            <option value="TECHNIQUE">⚙️ Problème Technique</option>
                            <option value="REMBOURSEMENT">💳 Remboursement</option>
                            <option value="MALADIE">🏥 Maladie</option>
                            <option value="VOYAGE">✈️ Voyage</option>
                            <option value="MOTIVATION">📉 Motivation</option>
                            <option value="INFO">ℹ️ Information</option>
                        </select>
                    </div>
                    <textarea id="crm-note" placeholder="Détails de l'échange..." style="width:100%; height:60px; padding:10px; box-sizing:border-box; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); font-family:inherit; outline:none; resize:none; margin-bottom:10px;"></textarea>
                    <button class="btn btn-primary" onclick="addCrmNote()" style="width:100%; padding:10px; border-radius:8px;">💾 Enregistrer la Note</button>
                </div>

                <!-- Filters -->
                <div style="display:flex; gap:10px; margin-bottom:15px; overflow-x:auto; padding-bottom:5px; flex-shrink:0;">
                    <div class="chip crm-filter active" onclick="filterCrm('all')" id="crm-flt-all" style="cursor:pointer; background:rgba(10,132,255,0.15); color:#0a84ff; border-color:#0a84ff;">🔘 Tout voir</div>
                    <div class="chip crm-filter" onclick="filterCrm('notes')" id="crm-flt-notes" style="cursor:pointer; background:var(--surface);">🗣️ Notes</div>
                    <div class="chip crm-filter" onclick="filterCrm('tickets')" id="crm-flt-tickets" style="cursor:pointer; background:var(--surface);">🚨 Tickets (SOS)</div>
                    <div class="chip crm-filter" onclick="filterCrm('system')" id="crm-flt-system" style="cursor:pointer; background:var(--surface);">🤖 Système</div>
                </div>

                <!-- Timeline -->
                <div id="crm-timeline-container" style="flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:12px; padding-right:5px; margin-bottom:20px;">
                    <!-- JS populated -->
                </div>
            </div>

            <!-- Tab 4: Funnel -->'''
if 'id="mcontent-crm"' not in c:
    c = c.replace(mcontent_target, new_mcontent)

# 3. Add JS Functions
js_target = r'function switchModalTab(tabId) {'
new_js = r'''let currentCrmFilter = 'all';
        async function fetchCrmTimeline(studentId, tgId) {
            const container = document.getElementById('crm-timeline-container');
            container.innerHTML = '<div style="text-align:center; padding:20px; color:var(--text2);">Chargement...</div>';
            try {
                const res = await fetch(`/api/admin/gateway/student_timeline?id=${studentId}&tid=${tgId || ''}`);
                const data = await res.json();
                if(data.success) {
                    renderCrmTimeline(data.timeline);
                } else {
                    container.innerHTML = `<div style="color:red; text-align:center;">Erreur: ${data.error}</div>`;
                }
            } catch (e) {
                container.innerHTML = `<div style="color:red; text-align:center;">Erreur de connexion</div>`;
            }
        }

        let currentTimelineData = [];
        function renderCrmTimeline(data) {
            if (data) currentTimelineData = data;
            const container = document.getElementById('crm-timeline-container');
            container.innerHTML = '';
            
            let filtered = currentTimelineData;
            if (currentCrmFilter === 'notes') {
                filtered = filtered.filter(item => item.source_table === 'student_logs' && item.action_type === 'CRM_NOTE');
            } else if (currentCrmFilter === 'tickets') {
                filtered = filtered.filter(item => item.source_table === 'gateway_sos');
            } else if (currentCrmFilter === 'system') {
                filtered = filtered.filter(item => item.source_table === 'student_logs' && item.action_type !== 'CRM_NOTE');
            }
            
            if(filtered.length === 0) {
                container.innerHTML = '<div style="text-align:center; padding:20px; color:var(--text2);">Aucun historique trouvé.</div>';
                return;
            }
            
            filtered.forEach(item => {
                const div = document.createElement('div');
                div.style.cssText = 'background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:12px; position:relative;';
                
                let icon = '🤖';
                let title = 'Action Système';
                let color = 'var(--text2)';
                let content = item.description;
                
                if (item.source_table === 'gateway_sos') {
                    icon = '🚨';
                    title = 'Ticket SOS';
                    color = '#ef4444';
                    content = `<strong>Sujet :</strong> Ticket<br><strong>Message :</strong> ${item.message || ''}<br><span style="font-size:0.8rem; color:${item.status==='closed'?'#16a34a':'#f97316'};">Statut: ${item.status}</span>`;
                } else if (item.action_type === 'CRM_NOTE') {
                    icon = '🗣️';
                    title = 'Note de l\'équipe';
                    color = '#0a84ff';
                    // Parse description "[APPEL] [MALADIE] details"
                    let badge = '';
                    let cleanDesc = item.description;
                    const bMatch = item.description.match(/^\[(.*?)\]\s*\[(.*?)\]\s*(.*)$/);
                    if (bMatch) {
                        badge = `<span style="background:rgba(10,132,255,0.1); color:#0a84ff; padding:2px 6px; border-radius:4px; font-size:0.75rem; margin-right:5px; font-weight:bold;">${bMatch[1]}</span><span style="background:rgba(255,159,10,0.1); color:#ff9f0a; padding:2px 6px; border-radius:4px; font-size:0.75rem; font-weight:bold;">${bMatch[2]}</span>`;
                        cleanDesc = bMatch[3];
                    }
                    content = `<div style="margin-bottom:8px;">${badge}</div><div style="white-space:pre-wrap; line-height:1.4;">${cleanDesc}</div>`;
                } else {
                    title = item.action_type;
                }
                
                // Format Date
                let dStr = item.timestamp;
                try {
                    const d = new Date(item.timestamp + 'Z'); // UTC
                    dStr = d.toLocaleString();
                } catch(e){}
                
                div.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; border-bottom:1px solid var(--border); padding-bottom:6px;">
                        <div style="font-weight:bold; font-size:0.9rem; color:${color}; display:flex; align-items:center; gap:6px;">${icon} ${title}</div>
                        <div style="font-size:0.75rem; color:var(--text2);">${dStr}</div>
                    </div>
                    <div style="font-size:0.85rem; color:var(--text1);">${content}</div>
                `;
                container.appendChild(div);
            });
        }
        
        function filterCrm(type) {
            currentCrmFilter = type;
            ['all', 'notes', 'tickets', 'system'].forEach(t => {
                const el = document.getElementById('crm-flt-' + t);
                if(el) {
                    if (t === type) {
                        el.style.background = 'rgba(10,132,255,0.15)';
                        el.style.color = '#0a84ff';
                        el.style.borderColor = '#0a84ff';
                    } else {
                        el.style.background = 'var(--surface)';
                        el.style.color = 'var(--text2)';
                        el.style.borderColor = 'var(--border)';
                    }
                }
            });
            renderCrmTimeline();
        }

        async function addCrmNote() {
            if(!activeStudent) return;
            const ctype = document.getElementById('crm-type').value;
            const tag = document.getElementById('crm-tag').value;
            const note = document.getElementById('crm-note').value.trim();
            if(!note) { alert('Veuillez entrer une note.'); return; }
            
            try {
                const res = await fetch('/api/admin/gateway/add_crm_note', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        student_id: activeStudent.student_id,
                        telegram_id: activeStudent.telegram_id,
                        type: ctype,
                        tag: tag,
                        note: note
                    })
                });
                const data = await res.json();
                if(data.success) {
                    document.getElementById('crm-note').value = '';
                    // Refresh timeline
                    fetchCrmTimeline(activeStudent.student_id, activeStudent.telegram_id);
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch(e) {
                alert('Erreur de connexion');
            }
        }

        function switchModalTab(tabId) {'''
if 'async function fetchCrmTimeline' not in c:
    c = c.replace(js_target, new_js)

# 4. Trigger fetch on openStudentCard
fetch_target = r'document.getElementById(\'logs-overlay\').style.display = \'flex\';'
new_fetch = r'''document.getElementById('logs-overlay').style.display = 'flex';
            fetchCrmTimeline(student.student_id, student.telegram_id);'''
if 'fetchCrmTimeline(student.student_id' not in c:
    c = c.replace(fetch_target, new_fetch)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Frontend CRM Patched")
