import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add admin-name input field to the form (before the textarea)
old_textarea = '''<label style="display:block; margin-bottom:5px; font-weight:bold; color:var(--text2); font-size:0.85rem;">نص الملاحظة:</label>
                        <textarea id="crm-note"'''

new_textarea = '''<label style="display:block; margin-bottom:5px; font-weight:bold; color:var(--text2); font-size:0.85rem;">اسم المسؤول (يُحفظ تلقائياً):</label>
                        <input id="crm-admin-name" type="text" placeholder="اسمك..." style="width:100%; padding:10px; box-sizing:border-box; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none; margin-bottom:15px;" oninput="localStorage.setItem('adminName', this.value)">
                        
                        <label style="display:block; margin-bottom:5px; font-weight:bold; color:var(--text2); font-size:0.85rem;">نص الملاحظة:</label>
                        <textarea id="crm-note"'''

c = c.replace(old_textarea, new_textarea)

# 2. Replace the entire addCrmNote JS function with a prompt()-free version
old_func_pattern = re.compile(
    r'async function addCrmNote\(\) \{.*?(?=\n\s*function |\n\s*async function |\n\s*let currentCrmFilter)',
    re.DOTALL
)

new_func = r'''async function addCrmNote() {
            try {
                if(!activeStudent) {
                    alert('Erreur: Aucun étudiant sélectionné !');
                    return;
                }
                const ctype = document.getElementById('crm-type').value;
                const tag = document.getElementById('crm-tag').value;
                const note = document.getElementById('crm-note').value.trim();
                const adminNameField = document.getElementById('crm-admin-name');
                
                if(!note) { 
                    alert('الرجاء كتابة الملاحظة أولا'); 
                    return; 
                }
                
                let adminName = (adminNameField && adminNameField.value.trim()) || localStorage.getItem('adminName') || 'Admin';
                localStorage.setItem('adminName', adminName);
                
                const btn = document.getElementById('btn-save-note');
                if(btn) {
                    btn.innerHTML = '⏳ جاري الحفظ...';
                    btn.disabled = true;
                }
                
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
                
                if(btn) {
                    btn.innerHTML = '💾 حفظ الملاحظة وإرسال';
                    btn.disabled = false;
                }
                
                if(!res.ok) {
                    alert('❌ خطأ من السيرفر: ' + res.status);
                    return;
                }
                
                const data = await res.json();
                
                if(data.success) {
                    document.getElementById('crm-note').value = '';
                    alert('✅ تم حفظ الملاحظة بنجاح!');
                    switchCrmSubtab('timeline');
                } else {
                    alert('❌ خطأ في الحفظ: ' + data.error);
                }
            } catch(e) {
                alert('❌ حدث خطأ: ' + e.message);
                console.error(e);
                const btn = document.getElementById('btn-save-note');
                if(btn) {
                    btn.innerHTML = '💾 حفظ الملاحظة وإرسال';
                    btn.disabled = false;
                }
            }
        }

'''

c = old_func_pattern.sub(new_func, c)

# 3. Add pre-fill logic when switching to CRM tab
old_switch = "if (tab === 'timeline') {"
new_switch = """if (tab === 'add') {
                // Pre-fill admin name from localStorage
                const savedName = localStorage.getItem('adminName');
                const nameField = document.getElementById('crm-admin-name');
                if(nameField && savedName) nameField.value = savedName;
            }
            if (tab === 'timeline') {"""
c = c.replace(old_switch, new_switch)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("Step 1 patched")
