import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace empty tab-actions
old_actions = r'''<!-- TAB: Actions \(Vide pour l'instant\) -->\s*<div id="tab-actions" class="tab-content">.*?</div>'''

new_actions = r'''<!-- TAB: Actions Massives -->
    <div id="tab-actions" class="tab-content">
        <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:20px; margin-bottom:20px;">
            <h2 style="color:var(--text1); margin-bottom:15px;">🚀 الإجراءات الجماعية (Envois en masse)</h2>
            <p style="color:var(--text2); margin-bottom:20px;">قم بإرسال دعوات الأكاديمية أو رسائل التذكير بضغطة زر. النظام سيقوم بتصفية الطلاب الذين سبق لهم الانضمام تلقائياً.</p>
            
            <div style="display:flex; gap:15px; flex-wrap:wrap; margin-bottom:20px;">
                <div style="flex:1; min-width:200px;">
                    <label style="color:var(--text1); font-weight:bold; display:block; margin-bottom:5px;">📌 نوع الإجراء (Action) :</label>
                    <select id="mass-action-type" onchange="calculateMassTarget()" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none;">
                        <option value="email_1">📧 إرسال الإيميل الأول (Bienvenue)</option>
                        <option value="email_2">📧 إرسال الإيميل الثاني (Relance 48h)</option>
                    </select>
                </div>
                <div style="flex:1; min-width:200px;">
                    <label style="color:var(--text1); font-weight:bold; display:block; margin-bottom:5px;">🎓 المستوى (Niveau) :</label>
                    <select id="mass-action-year" onchange="calculateMassTarget()" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none;">
                        <option value="all">الكل (Tous)</option>
                        <option value="1">المستوى الأول (1)</option>
                        <option value="2">المستوى الثاني (2)</option>
                        <option value="3">المستوى الثالث (3)</option>
                        <option value="4">المستوى الرابع (4)</option>
                    </select>
                </div>
                <div style="flex:1; min-width:200px;">
                    <label style="color:var(--text1); font-weight:bold; display:block; margin-bottom:5px;">🚻 الجنس (Sexe) :</label>
                    <select id="mass-action-gender" onchange="calculateMassTarget()" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none;">
                        <option value="all">الكل (Tous)</option>
                        <option value="male">ذكور (Garçons)</option>
                        <option value="female">إناث (Filles)</option>
                    </select>
                </div>
            </div>
            
            <div id="mass-action-summary" style="background:rgba(0,132,255,0.1); border:1px solid #0084ff; border-radius:8px; padding:15px; margin-bottom:20px;">
                <h4 style="color:#0084ff; margin:0 0 10px 0;">📊 ملخص الاستهداف (Résumé de la cible) :</h4>
                <ul style="color:var(--text1); margin:0; padding-inline-start:20px; line-height:1.6;">
                    <li>إجمالي الطلاب في هذا الفلتر : <b id="mass-total">0</b></li>
                    <li>تم استبعاد (انضموا أو أرسل لهم) : <b id="mass-excluded" style="color:var(--warning);">0</b></li>
                    <li>الهدف النهائي للرسالة : <b id="mass-target" style="color:var(--success); font-size:1.1rem;">0</b> طالب</li>
                </ul>
            </div>
            
            <button id="btn-execute-mass" class="btn btn-primary" onclick="executeMassAction()" style="width:100%; padding:15px; font-size:1.1rem; border-radius:8px; opacity:0.5; pointer-events:none;">
                إرسال الآن (Envoyer)
            </button>
            
            <!-- Dispatch Status -->
            <div id="dispatch-status-container" style="display:none; margin-top:20px; padding:15px; background:var(--bg); border:1px solid var(--border); border-radius:8px;">
                <h4 style="color:var(--text1); margin:0 0 10px 0;">⏳ حالة الإرسال (Progression)</h4>
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <span style="color:var(--text2);">تم الإرسال: <b id="dispatch-sent" style="color:var(--success);">0</b></span>
                    <span style="color:var(--text2);">فشل: <b id="dispatch-fail" style="color:var(--danger);">0</b></span>
                    <span style="color:var(--text2);">المجموع: <b id="dispatch-total">0</b></span>
                </div>
                <div style="width:100%; background:var(--border); border-radius:10px; height:8px; overflow:hidden;">
                    <div id="dispatch-progress-bar" style="height:100%; background:var(--accent); width:0%; transition:width 0.3s;"></div>
                </div>
                <p id="dispatch-current" style="color:var(--text2); font-size:0.8rem; margin-top:10px; text-align:center;">-</p>
            </div>
        </div>
    </div>'''

c = re.sub(old_actions, new_actions, c, flags=re.DOTALL)


# Add JS code for calculating mass targets
js_code = '''
        let currentMassTargetIds = [];
        let dispatchInterval = null;

        function calculateMassTarget() {
            if (!allStudents) return;
            
            const actionType = document.getElementById('mass-action-type').value;
            const yrFilter = document.getElementById('mass-action-year').value;
            const genFilter = document.getElementById('mass-action-gender').value;
            
            let targetIds = [];
            let totalInFilter = 0;
            
            for(let s of allStudents) {
                // Year match
                const yr = String(s.year || '').toLowerCase();
                let matchYr = yrFilter === 'all' 
                    || yr.includes(yrFilter)
                    || (yrFilter === '1' && (yr.includes('أول') || yr.includes('1')))
                    || (yrFilter === '2' && (yr.includes('ثاني') || yr.includes('2')))
                    || (yrFilter === '3' && (yr.includes('ثالث') || yr.includes('3')))
                    || (yrFilter === '4' && (yr.includes('رابع') || yr.includes('4')));
                
                // Gender match
                const g = String(s.gender || '').toLowerCase();
                const isM = g.startsWith('h') || g === 'm' || g === 'male' || g.includes('ذكر');
                const isF = g.startsWith('f') || g === 'female' || g === 'fille' || g.includes('أنثى');
                let matchGen = genFilter === 'all' 
                    || (genFilter === 'male' && isM)
                    || (genFilter === 'female' && isF);
                    
                if (matchYr && matchGen) {
                    totalInFilter++;
                    
                    // Business Logic filtering
                    const joined = !!s.telegram_id || s.group_joined;
                    
                    if (!joined) {
                        if (actionType === 'email_1' && (!s.email_sent || s.email_sent < 1)) {
                            targetIds.push(s.student_id);
                        } else if (actionType === 'email_2' && s.email_sent === 1) {
                            targetIds.push(s.student_id);
                        }
                    }
                }
            }
            
            currentMassTargetIds = targetIds;
            
            document.getElementById('mass-total').textContent = totalInFilter;
            document.getElementById('mass-excluded').textContent = totalInFilter - targetIds.length;
            document.getElementById('mass-target').textContent = targetIds.length;
            
            const btn = document.getElementById('btn-execute-mass');
            if (targetIds.length > 0) {
                btn.style.opacity = '1';
                btn.style.pointerEvents = 'auto';
            } else {
                btn.style.opacity = '0.5';
                btn.style.pointerEvents = 'none';
            }
        }

        async function executeMassAction() {
            if (currentMassTargetIds.length === 0) return;
            const actionType = document.getElementById('mass-action-type').value;
            
            if (!confirm(`هل أنت متأكد من إرسال ${currentMassTargetIds.length} رسالة؟ (Action: ${actionType})`)) return;
            
            try {
                const res = await fetch('/api/admin/gateway/send_bulk_emails', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        action_type: actionType,
                        student_ids: currentMassTargetIds
                    })
                });
                const data = await res.json();
                if (data.success) {
                    alert('تم بدء الإرسال في الخلفية !');
                    document.getElementById('dispatch-status-container').style.display = 'block';
                    if (!dispatchInterval) dispatchInterval = setInterval(checkDispatchStatus, 2000);
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch(e) {
                alert('Erreur réseau');
            }
        }
        
        async function checkDispatchStatus() {
            try {
                const res = await fetch('/api/admin/gateway/email_dispatch_status');
                const data = await res.json();
                if (data.success && data.state) {
                    const st = data.state;
                    document.getElementById('dispatch-total').textContent = st.total;
                    document.getElementById('dispatch-sent').textContent = st.sent;
                    document.getElementById('dispatch-fail').textContent = st.failed;
                    document.getElementById('dispatch-current').textContent = st.current_student || '-';
                    
                    if (st.total > 0) {
                        const pct = ((st.sent + st.failed) / st.total) * 100;
                        document.getElementById('dispatch-progress-bar').style.width = pct + '%';
                    }
                    
                    if (!st.is_running && st.total > 0 && (st.sent + st.failed) >= st.total) {
                        clearInterval(dispatchInterval);
                        dispatchInterval = null;
                        alert('Terminé !');
                        loadStudents();
                    }
                }
            } catch(e) {}
        }
'''

# Insert js_code before loadStudents()
if 'function calculateMassTarget()' not in c:
    c = c.replace('function loadStudents() {', js_code + '\n        function loadStudents() {')

# Hook calculateMassTarget into loadStudents success
hook = '''renderDashboardStats();'''
new_hook = '''renderDashboardStats();\n                calculateMassTarget();'''
c = c.replace(hook, new_hook)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('Patched mass actions UI')
