import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

new_crm_html = r'''<div id="mcontent-crm" class="mcontent" style="flex-direction:column; flex:1; overflow:hidden; padding:0;">
                <!-- CRM Sub-tabs -->
                <div style="display:flex; border-bottom:1px solid var(--border); background:var(--surface); flex-shrink:0;">
                    <div class="crm-subtab active" onclick="switchCrmSubtab('timeline')" id="csub-timeline" style="flex:1; text-align:center; padding:12px; cursor:pointer; font-weight:bold; color:#0a84ff; border-bottom:2px solid #0a84ff;">🕒 سجل النشاطات</div>
                    <div class="crm-subtab" onclick="switchCrmSubtab('add')" id="csub-add" style="flex:1; text-align:center; padding:12px; cursor:pointer; color:var(--text2); border-bottom:2px solid transparent;">➕ إضافة ملاحظة</div>
                </div>

                <!-- Timeline View -->
                <div id="crm-view-timeline" style="flex:1; display:flex; flex-direction:column; padding:15px; overflow:hidden;">
                    <div style="display:flex; gap:10px; margin-bottom:15px; overflow-x:auto; padding-bottom:5px; flex-shrink:0;">
                        <div class="chip crm-filter active" onclick="filterCrm('all')" id="crm-flt-all" style="cursor:pointer; background:rgba(10,132,255,0.15); color:#0a84ff; border-color:#0a84ff;">🔘 عرض الكل</div>
                        <div class="chip crm-filter" onclick="filterCrm('notes')" id="crm-flt-notes" style="cursor:pointer; background:var(--surface); color:var(--text2); border-color:var(--border);">🗣️ الملاحظات</div>
                        <div class="chip crm-filter" onclick="filterCrm('tickets')" id="crm-flt-tickets" style="cursor:pointer; background:var(--surface); color:var(--text2); border-color:var(--border);">🚨 التذاكر</div>
                        <div class="chip crm-filter" onclick="filterCrm('system')" id="crm-flt-system" style="cursor:pointer; background:var(--surface); color:var(--text2); border-color:var(--border);">🤖 النظام</div>
                    </div>
                    <div id="crm-timeline-container" style="flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:12px; padding-right:5px; margin-bottom:20px;">
                        <!-- JS populated -->
                    </div>
                </div>

                <!-- Add Note View -->
                <div id="crm-view-add" style="flex:1; display:none; flex-direction:column; padding:15px; overflow-y:auto; background:var(--bg);">
                    <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                        <h4 style="margin:0 0 15px 0; font-size:1.1rem; color:var(--text1);">تفاصيل الملاحظة (CRM)</h4>
                        
                        <label style="display:block; margin-bottom:5px; font-weight:bold; color:var(--text2); font-size:0.85rem;">نوع التواصل:</label>
                        <select id="crm-type" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none; margin-bottom:15px;">
                            <option value="APPEL">📞 اتصال عادي</option>
                            <option value="APPEL_WA">📞 اتصال واتساب</option>
                            <option value="WHATSAPP">💬 رسالة واتساب</option>
                            <option value="TELEGRAM">✈️ تيليجرام</option>
                            <option value="EMAIL">📧 بريد إلكتروني</option>
                            <option value="AUTRE">📌 أخرى</option>
                        </select>
                        
                        <label style="display:block; margin-bottom:5px; font-weight:bold; color:var(--text2); font-size:0.85rem;">التصنيف (المشكلة):</label>
                        <select id="crm-tag" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none; margin-bottom:15px;">
                            <option value="TECHNIQUE">⚙️ مشكلة تقنية</option>
                            <option value="REMBOURSEMENT">💳 استرداد أموال</option>
                            <option value="MALADIE">🏥 مرض</option>
                            <option value="VOYAGE">✈️ سفر</option>
                            <option value="MOTIVATION">📉 نقص تحفيز</option>
                            <option value="INFO">ℹ️ معلومة</option>
                            <option value="AUTRE">📌 أخرى</option>
                        </select>
                        
                        <label style="display:block; margin-bottom:5px; font-weight:bold; color:var(--text2); font-size:0.85rem;">نص الملاحظة:</label>
                        <textarea id="crm-note" placeholder="اكتب تفاصيل المحادثة هنا..." style="width:100%; height:100px; padding:10px; box-sizing:border-box; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); font-family:inherit; outline:none; resize:none; margin-bottom:20px;"></textarea>
                        
                        <button class="btn btn-primary" onclick="addCrmNote()" style="width:100%; padding:12px; border-radius:8px; font-size:1rem; font-weight:bold;">💾 حفظ الملاحظة وإرسال</button>
                    </div>
                </div>
            </div>

            <!-- Tab 4: Funnel -->'''

old_html = re.search(r'<div id="mcontent-crm".*?<!-- Tab 4: Funnel -->', c, re.DOTALL)
if old_html:
    c = c.replace(old_html.group(0), new_crm_html)
else:
    print("HTML not found!")

# Now add/replace JS functions
new_js_logic = r'''
        function switchCrmSubtab(tab) {
            document.getElementById('csub-timeline').style.color = 'var(--text2)';
            document.getElementById('csub-timeline').style.borderColor = 'transparent';
            document.getElementById('csub-timeline').style.fontWeight = 'normal';
            
            document.getElementById('csub-add').style.color = 'var(--text2)';
            document.getElementById('csub-add').style.borderColor = 'transparent';
            document.getElementById('csub-add').style.fontWeight = 'normal';
            
            document.getElementById('csub-' + tab).style.color = '#0a84ff';
            document.getElementById('csub-' + tab).style.borderColor = '#0a84ff';
            document.getElementById('csub-' + tab).style.fontWeight = 'bold';
            
            if (tab === 'timeline') {
                document.getElementById('crm-view-timeline').style.display = 'flex';
                document.getElementById('crm-view-add').style.display = 'none';
                if(activeStudent) fetchCrmTimeline(activeStudent.student_id, activeStudent.telegram_id);
            } else {
                document.getElementById('crm-view-timeline').style.display = 'none';
                document.getElementById('crm-view-add').style.display = 'flex';
            }
        }

        async function addCrmNote() {
            try {
                if(!activeStudent) {
                    alert('Erreur: Aucun étudiant sélectionné !');
                    return;
                }
                const ctype = document.getElementById('crm-type').value;
                const tag = document.getElementById('crm-tag').value;
                const note = document.getElementById('crm-note').value.trim();
                
                if(!note) { 
                    alert('الرجاء كتابة الملاحظة أولا'); 
                    return; 
                }
                
                let adminName = localStorage.getItem('adminName');
                if(!adminName) {
                    adminName = prompt("ما هو اسمك؟ (سيظهر في الملاحظة)");
                    if(!adminName || adminName.trim() === '') adminName = "Admin";
                    else localStorage.setItem('adminName', adminName);
                }
                
                // Disable button to prevent double click
                const btn = event.currentTarget;
                const oldText = btn.innerHTML;
                btn.innerHTML = '⏳ جاري الحفظ...';
                btn.disabled = true;
                
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
                btn.innerHTML = oldText;
                btn.disabled = false;
                
                if(data.success) {
                    alert('✅ تم حفظ الملاحظة بنجاح!');
                    document.getElementById('crm-note').value = '';
                    switchCrmSubtab('timeline'); // Switch back to timeline
                } else {
                    alert('❌ خطأ في الحفظ: ' + data.error);
                }
            } catch(e) {
                alert('❌ حدث خطأ في الاتصال بالسيرفر');
                console.error(e);
            }
        }
'''

# Let's replace the old addCrmNote function
old_add_func = re.search(r'async function addCrmNote\(\) \{.*?(?=\s*function switchModalTab|\s*let currentTimelineData)', c, re.DOTALL)
if old_add_func:
    c = c.replace(old_add_func.group(0), new_js_logic)
else:
    # If regex failed, just append to the end of the script before </script>
    # Find </script>
    print("Could not find old addCrmNote to replace cleanly, injecting before </script>")
    # Actually wait, let's remove the old one with a simpler regex.
    old_add_basic = re.search(r'async function addCrmNote\(\) \{.*?\}\s*\}\s*\}', c, re.DOTALL)
    if old_add_basic:
        c = c.replace(old_add_basic.group(0), new_js_logic)
    else:
        # manual replace
        pass

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("UI Redesign Patched")
