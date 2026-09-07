import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Find the global var block and add activeStudent object variable
old_var = 'let activeStudentId = null;'
new_var = 'let activeStudentId = null;\n        let activeStudentObj = null;'
c = c.replace(old_var, new_var)

# 2. In openStudentCard, save the full student object
old_open = 'function openStudentCard(student) {\n            activeStudentId = student.student_id;'
new_open = 'function openStudentCard(student) {\n            activeStudentId = student.student_id;\n            activeStudentObj = student;'
c = c.replace(old_open, new_open)

# 3. Replace all usages of 'activeStudent' in addCrmNote with 'activeStudentObj'
new_add_func = r'''async function addCrmNote() {
            try {
                if(!activeStudentObj) {
                    alert('لم يتم اختيار أي طالب!');
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
                        student_id: activeStudentObj.student_id,
                        telegram_id: activeStudentObj.telegram_id,
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

# Replace the function completely
old_func = re.search(r'async function addCrmNote\(\) \{.*?(?=\n        function |\n        async function |\n        let currentTimelineData)', c, re.DOTALL)
if old_func:
    c = c.replace(old_func.group(0), new_add_func)
    print("addCrmNote replaced")
else:
    print("WARNING: addCrmNote not found, appending")

# 4. Fix fetchCrmTimeline calls: replace activeStudent.student_id with activeStudentObj
c = c.replace('fetchCrmTimeline(activeStudent.student_id, activeStudent.telegram_id)', 
               'fetchCrmTimeline(activeStudentObj.student_id, activeStudentObj.telegram_id)')
# Also fix the initial call when opening card
c = c.replace('fetchCrmTimeline(student.student_id, student.telegram_id)',
               'fetchCrmTimeline(student.student_id, student.telegram_id)')

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("Done")
