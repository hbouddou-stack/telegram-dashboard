import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Checkboxes in Table Headers and Rows
if 'id="selectAllCheckbox"' not in html:
    # Inject into thead
    th_old = '<tr style="background:rgba(10,132,255,0.1); border-bottom:2px solid var(--border); text-align:right;">'
    th_new = '<tr style="background:rgba(10,132,255,0.1); border-bottom:2px solid var(--border); text-align:right;">\n                        <th style="padding:12px; width:40px; text-align:center;"><input type="checkbox" id="selectAllCheckbox" onclick="toggleAllStudents()"></th>'
    html = html.replace(th_old, th_new)

    # Inject into tbody row
    tr_old = '<td style="padding:12px;"><strong>${name}</strong></td>'
    tr_new = '<td style="padding:12px; text-align:center;" onclick="event.stopPropagation()"><input type="checkbox" class="student-select-cb" value="${s.student_id}"></td>\n                        <td style="padding:12px;"><strong>${name}</strong></td>'
    html = html.replace(tr_old, tr_new)

# 2. Add Mass SMS Button
if 'id="btn-mass-sms"' not in html:
    # Inject near view-mode-selector
    btn_html = """
                <button id="btn-mass-sms" onclick="sendMassSms()" style="background:#0ea5e9; color:white; border:none; padding:4px 10px; border-radius:6px; font-weight:bold; display:none; cursor:pointer; font-size:0.85rem; margin-right:10px;">
                    📱 إرسال SMS للكل (<span id="mass-sms-count">0</span>)
                </button>
    """
    html = html.replace('<select id="card-style-selector"', btn_html + '<select id="card-style-selector"')

# 3. Add Javascript Logic
js_logic = """
        function toggleAllStudents() {
            const isChecked = document.getElementById('selectAllCheckbox').checked;
            const checkboxes = document.querySelectorAll('.student-select-cb');
            checkboxes.forEach(cb => cb.checked = isChecked);
            updateMassSmsButton();
        }
        document.addEventListener('change', (e) => {
            if(e.target && e.target.classList && e.target.classList.contains('student-select-cb')) {
                updateMassSmsButton();
            }
        });
        function updateMassSmsButton() {
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
        }
        async function sendMassSms() {
            const cbs = document.querySelectorAll('.student-select-cb:checked');
            const ids = Array.from(cbs).map(cb => cb.value);
            if(ids.length === 0) return;
            if(!confirm(`هل أنت متأكد من وضع ${ids.length} طالب في قائمة انتظار SMS ؟`)) return;
            
            try {
                const res = await fetch('/api/admin/gateway/queue_sms', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ student_ids: ids })
                });
                const data = await res.json();
                if(data.success) {
                    alert(`✅ تم وضع ${data.queued} رسالة SMS في قائمة الانتظار للروبوت بنجاح.`);
                    cbs.forEach(cb => cb.checked = false);
                    document.getElementById('selectAllCheckbox').checked = false;
                    updateMassSmsButton();
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch(e) {
                console.error(e);
                alert('Erreur réseau.');
            }
        }
"""
if 'function toggleAllStudents()' not in html:
    html = html.replace("function changeViewMode(mode) {", js_logic + "\n        function changeViewMode(mode) {")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("admin_gateway.html patched!")
