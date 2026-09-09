import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add floating action bar
bulk_action_bar = """
    <!-- BULK ACTION BAR -->
    <div id="bulk-action-bar" style="display:none; position:fixed; bottom:90px; left:50%; transform:translateX(-50%); background:var(--surface); border:1px solid var(--accent); box-shadow:0 10px 30px rgba(0,0,0,0.8); padding:12px 20px; border-radius:30px; z-index:1000; align-items:center; gap:15px; width:90%; max-width:500px; justify-content:space-between;">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="background:var(--accent); color:white; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:900;" id="bulk-count">0</div>
        </div>
        <div style="display:flex; gap:10px;">
            <button onclick="openBulkModal('email')" style="background:#3b82f6; color:white; border:none; padding:8px 15px; border-radius:20px; font-weight:bold; cursor:pointer; font-size:0.85rem;">📧 Email</button>
            <button onclick="openBulkModal('whatsapp')" style="background:#10b981; color:white; border:none; padding:8px 15px; border-radius:20px; font-weight:bold; cursor:pointer; font-size:0.85rem;">💬 WhatsApp</button>
        </div>
        <button onclick="unselectAll()" style="background:var(--bg); border:1px solid var(--border); color:var(--text2); width:30px; height:30px; border-radius:50%; cursor:pointer; font-size:0.8rem;">❌</button>
    </div>

    <!-- BULK MODAL -->
    <div id="modal-bulk" class="modal-overlay">
        <div style="background:var(--surface); width:100%; max-width:650px; max-height:85vh; border-radius:20px 20px 0 0; padding:20px; overflow-y:auto; display:flex; flex-direction:column;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <h3 id="bulk-modal-title" style="margin:0; font-size:1.2rem; color:var(--text1);">Envoyer Message</h3>
                <button onclick="document.getElementById('modal-bulk').style.display='none'" style="background:var(--bg); border:1px solid var(--border); color:var(--text1); padding:5px 12px; border-radius:8px; cursor:pointer;">Annuler</button>
            </div>
            
            <p style="font-size:0.85rem; color:var(--text2); margin-top:0;">Vous allez envoyer un message à <strong id="bulk-modal-count" style="color:var(--accent2);">0</strong> étudiants.</p>
            
            <div style="display:flex; flex-direction:column; gap:12px; margin-top:10px;">
                <div id="bulk-subject-container" style="display:flex; flex-direction:column; gap:5px;">
                    <label style="font-size:0.8rem; font-weight:bold; color:var(--text2);">Sujet (Email uniquement)</label>
                    <input type="text" id="bulk-subject" placeholder="Bienvenue !" style="padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1);">
                </div>
                
                <div style="display:flex; flex-direction:column; gap:5px;">
                    <label style="font-size:0.8rem; font-weight:bold; color:var(--text2);">Message</label>
                    <div style="font-size:0.75rem; color:var(--text2); margin-bottom:5px;">Variables : {prenom}, {nom}, {lien}</div>
                    <textarea id="bulk-message" rows="6" placeholder="Bonjour {prenom}..." style="padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); resize:vertical; font-family:inherit;"></textarea>
                </div>
                
                <input type="hidden" id="bulk-type" value="email">
                
                <button onclick="executeBulkAction()" style="background:var(--accent); color:white; border:none; padding:12px; border-radius:12px; font-weight:bold; cursor:pointer; font-size:1rem; margin-top:10px;">🚀 Envoyer Maintenant</button>
            </div>
        </div>
    </div>
"""
if 'bulk-action-bar' not in html:
    html = html.replace('</body>', bulk_action_bar + '\n</body>')

# 2. Add Logic
bulk_js = """
        function unselectAll() {
            document.querySelectorAll('.student-select-cb').forEach(cb => cb.checked = false);
            const selectAllCb = document.getElementById('selectAllCheckbox');
            if(selectAllCb) selectAllCb.checked = false;
            updateMassSmsButton();
        }

        function openBulkModal(type) {
            const selected = document.querySelectorAll('.student-select-cb:checked').length;
            if (selected === 0) return;
            
            document.getElementById('bulk-type').value = type;
            document.getElementById('bulk-modal-count').textContent = selected;
            
            if (type === 'email') {
                document.getElementById('bulk-modal-title').textContent = '📧 Envoyer Email en masse';
                document.getElementById('bulk-subject-container').style.display = 'flex';
            } else {
                document.getElementById('bulk-modal-title').textContent = '💬 Envoyer WhatsApp/SMS en masse';
                document.getElementById('bulk-subject-container').style.display = 'none';
            }
            
            document.getElementById('modal-bulk').style.display = 'flex';
        }

        async function executeBulkAction() {
            const type = document.getElementById('bulk-type').value;
            const subject = document.getElementById('bulk-subject').value;
            const message = document.getElementById('bulk-message').value;
            const cbs = document.querySelectorAll('.student-select-cb:checked');
            const ids = Array.from(cbs).map(cb => cb.value);
            
            if (ids.length === 0) return;
            if (!message.trim()) {
                alert("Le message est vide !");
                return;
            }
            if (type === 'email' && !subject.trim()) {
                alert("Le sujet de l'email est obligatoire !");
                return;
            }
            
            if (!confirm(`Vous allez envoyer ce ${type} à ${ids.length} étudiants. Confirmer ?`)) return;
            
            // Simulation logic for now to prevent actual mass mailing until backend is wired if needed
            // Actually, we can call the backend bulk_action endpoint
            try {
                const res = await fetch('/api/admin/gateway/bulk_action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        action: type,
                        student_ids: ids,
                        subject: subject,
                        message: message
                    })
                });
                const data = await res.json();
                if (data.success) {
                    alert(`✅ Envoi lancé avec succès pour ${ids.length} étudiants !`);
                    document.getElementById('modal-bulk').style.display = 'none';
                    unselectAll();
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch(e) {
                alert('Erreur réseau');
            }
        }
"""
if 'openBulkModal' not in html:
    html = html.replace('function filterStudents()', bulk_js + '\n        function filterStudents()')

# 3. Update existing updateMassSmsButton to use the bulk bar
update_sms_old = """function updateMassSmsButton() {
const selected = document.querySelectorAll('.student-select-cb:checked').length;
const btn = document.getElementById('btn-mass-sms');
if(btn) {
if(selected > 0) {
btn.style.display = 'inline-block';
document.getElementById('mass-sms-count').innerText = selected;
} else {
btn.style.display = 'none';
}
}
}"""
update_sms_new = """function updateMassSmsButton() {
    const selected = document.querySelectorAll('.student-select-cb:checked').length;
    const bar = document.getElementById('bulk-action-bar');
    if(bar) {
        if(selected > 0) {
            bar.style.display = 'flex';
            document.getElementById('bulk-count').textContent = selected;
        } else {
            bar.style.display = 'none';
        }
    }
}"""

# A more robust regex replacement for updateMassSmsButton
html = re.sub(r'function updateMassSmsButton\(\)\s*\{.*?\}[\s\n]*\}', update_sms_new, html, flags=re.DOTALL)
# Just in case the regex missed it because of brackets
if 'bar.style.display =' not in html:
    html = re.sub(r'function updateMassSmsButton\(\).*?\}\s*\}', update_sms_new, html, flags=re.DOTALL)

# 4. Inject checkboxes into List View
# find: <div style="display:flex;justify-content:space-between;align-items:flex-start;">
# replace: <div style="display:flex;justify-content:space-between;align-items:flex-start;">
#          <input type="checkbox" class="student-select-cb" value="${s.student_id}" onclick="event.stopPropagation()" style="margin-left:10px; transform:scale(1.2);">

cb_inject = """<div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <input type="checkbox" class="student-select-cb" value="${s.student_id}" onclick="event.stopPropagation()" style="margin-left:10px; transform:scale(1.2); cursor:pointer;">"""
html = html.replace('<div style="display:flex;justify-content:space-between;align-items:flex-start;">', cb_inject)

# Template 2 injection
cb_inject_2 = """<div style="display:flex;justify-content:space-between;align-items:center;">
                            <input type="checkbox" class="student-select-cb" value="${s.student_id}" onclick="event.stopPropagation()" style="margin-left:10px; transform:scale(1.2); cursor:pointer;">"""
html = html.replace('<div style="display:flex;justify-content:space-between;align-items:center;">', cb_inject_2)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Frontend Bulk UI injected.")
