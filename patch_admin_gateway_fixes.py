import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Fix switchModalTab bug (add 'crm')
c = c.replace("['general', 'academy', 'telegram', 'funnel'].forEach", "['general', 'academy', 'telegram', 'funnel', 'crm'].forEach")

# 2. Fix the flex wrap for mtab-container (Issue 1)
# Find `<div class="mtab-container">`
# Add `flex-wrap: wrap;` in its style if possible, or create a style block.
c = c.replace('<div class="mtab-container">', '<div class="mtab-container" style="flex-wrap:wrap; display:flex;">')

# 3. Translate CRM Tab to Arabic
old_crm_content = re.search(r'<!-- Tab 5: CRM -->.*?<!-- Tab 4: Funnel -->', c, re.DOTALL)
if old_crm_content:
    new_crm_html = r'''<!-- Tab 5: CRM -->
            <div id="mcontent-crm" class="mcontent" style="flex-direction:column; flex:1; overflow:hidden;">
                <!-- Top Action Area -->
                <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:15px; margin-bottom:15px;">
                    <h4 style="margin:0 0 10px 0; font-size:0.9rem; color:var(--text1);">➕ إضافة ملاحظة CRM</h4>
                    <div style="display:flex; gap:10px; margin-bottom:10px;">
                        <select id="crm-type" style="padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none; flex:1;">
                            <option value="APPEL">📞 اتصال عادي</option>
                            <option value="APPEL_WA">📞 اتصال واتساب</option>
                            <option value="WHATSAPP">💬 رسالة واتساب</option>
                            <option value="TELEGRAM">✈️ تيليجرام</option>
                            <option value="EMAIL">📧 بريد إلكتروني</option>
                            <option value="AUTRE">📌 أخرى</option>
                        </select>
                        <select id="crm-tag" style="padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none; flex:1;">
                            <option value="TECHNIQUE">⚙️ مشكلة تقنية</option>
                            <option value="REMBOURSEMENT">💳 استرداد أموال</option>
                            <option value="MALADIE">🏥 مرض</option>
                            <option value="VOYAGE">✈️ سفر</option>
                            <option value="MOTIVATION">📉 نقص تحفيز</option>
                            <option value="INFO">ℹ️ معلومة</option>
                            <option value="AUTRE">📌 أخرى</option>
                        </select>
                    </div>
                    <textarea id="crm-note" placeholder="تفاصيل المحادثة..." style="width:100%; height:60px; padding:10px; box-sizing:border-box; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); font-family:inherit; outline:none; resize:none; margin-bottom:10px;"></textarea>
                    <button class="btn btn-primary" onclick="addCrmNote()" style="width:100%; padding:10px; border-radius:8px;">💾 حفظ الملاحظة</button>
                </div>

                <!-- Filters -->
                <div style="display:flex; gap:10px; margin-bottom:15px; overflow-x:auto; padding-bottom:5px; flex-shrink:0;">
                    <div class="chip crm-filter active" onclick="filterCrm('all')" id="crm-flt-all" style="cursor:pointer; background:rgba(10,132,255,0.15); color:#0a84ff; border-color:#0a84ff;">🔘 عرض الكل</div>
                    <div class="chip crm-filter" onclick="filterCrm('notes')" id="crm-flt-notes" style="cursor:pointer; background:var(--surface); color:var(--text2); border-color:var(--border);">🗣️ الملاحظات</div>
                    <div class="chip crm-filter" onclick="filterCrm('tickets')" id="crm-flt-tickets" style="cursor:pointer; background:var(--surface); color:var(--text2); border-color:var(--border);">🚨 التذاكر</div>
                    <div class="chip crm-filter" onclick="filterCrm('system')" id="crm-flt-system" style="cursor:pointer; background:var(--surface); color:var(--text2); border-color:var(--border);">🤖 النظام</div>
                </div>

                <!-- Timeline -->
                <div id="crm-timeline-container" style="flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:12px; padding-right:5px; margin-bottom:20px;">
                    <!-- JS populated -->
                </div>
            </div>

            <!-- Tab 4: Funnel -->'''
    c = c.replace(old_crm_content.group(0), new_crm_html)

# 4. Modify addCrmNote JS to prompt for admin name if not set
js_add = r'''async function addCrmNote() {
            if(!activeStudent) return;
            const ctype = document.getElementById('crm-type').value;
            const tag = document.getElementById('crm-tag').value;
            const note = document.getElementById('crm-note').value.trim();
            if(!note) { alert('Veuillez entrer une note.'); return; }
            
            let adminName = localStorage.getItem('adminName');
            if(!adminName) {
                adminName = prompt("Quel est votre nom ? (Sera affiché sur la note)");
                if(!adminName) return;
                localStorage.setItem('adminName', adminName);
            }
            
            try {
                const res = await fetch('/api/admin/gateway/add_crm_note', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        student_id: activeStudent.student_id,
                        telegram_id: activeStudent.telegram_id,
                        type: ctype,
                        tag: tag,
                        note: note,
                        admin_name: adminName
                    })
                });
                const data = await res.json();
                if(data.success) {
                    document.getElementById('crm-note').value = '';
                    fetchCrmTimeline(activeStudent.student_id, activeStudent.telegram_id);
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch(e) {
                alert('Erreur de connexion API');
            }
        }'''
c = re.sub(r'async function addCrmNote\(\) \{.*?\}\s*\}', js_add + '\n\n', c, flags=re.DOTALL)

# Let's write that correctly: I'll just replace the old addCrmNote entirely
old_add_func = re.search(r'async function addCrmNote\(\) \{.*?\}\n        \}', c, re.DOTALL)
if old_add_func:
    c = c.replace(old_add_func.group(0), js_add)

# 5. Modify renderCrmTimeline for FAQ tickets and Arabic translation
# I need to update the rendering of gateway_sos vs crm_tickets.
render_repl = r'''if (item.source_table === 'gateway_sos' || item.source_table === 'crm_tickets') {
                    icon = '🚨';
                    title = item.source_table === 'crm_tickets' ? 'تذكرة الأسئلة (FAQ)' : 'تذكرة الدعم (SOS)';
                    color = '#ef4444';
                    let subj = item.theme || "طلب مساعدة";
                    content = `<strong>الموضوع :</strong> ${subj}<br><strong>الرسالة :</strong> ${item.message || ''}<br><span style="font-size:0.8rem; color:${item.status==='closed'?'#16a34a':'#f97316'};">الحالة: ${item.status}</span>`;
                } else if (item.action_type === 'CRM_NOTE') {
                    icon = '🗣️';
                    title = 'ملاحظة الإدارة';
                    color = '#0a84ff';
                    let badge = '';
                    let cleanDesc = item.description || '';
                    const bMatch = cleanDesc.match(/^\[(.*?)\]\s*\[(.*?)\]\s*(.*)$/);
                    if (bMatch) {
                        badge = `<span style="background:rgba(10,132,255,0.1); color:#0a84ff; padding:2px 6px; border-radius:4px; font-size:0.75rem; margin-right:5px; font-weight:bold;">${bMatch[1]}</span><span style="background:rgba(255,159,10,0.1); color:#ff9f0a; padding:2px 6px; border-radius:4px; font-size:0.75rem; font-weight:bold;">${bMatch[2]}</span>`;
                        cleanDesc = bMatch[3];
                    }
                    content = `<div style="margin-bottom:8px;">${badge}</div><div style="white-space:pre-wrap; line-height:1.4;">${cleanDesc}</div>`;
                } else {
                    title = item.action_type;
                }'''
old_render_ifs = re.search(r"if \(item\.source_table === 'gateway_sos'\) \{.*?\} else \{.*?title = item\.action_type;\s*\}", c, re.DOTALL)
if old_render_ifs:
    c = c.replace(old_render_ifs.group(0), render_repl)

# Also fix the ticket filter logic
c = c.replace("item.source_table === 'gateway_sos'", "(item.source_table === 'gateway_sos' || item.source_table === 'crm_tickets')")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("Admin Gateway Patched")
