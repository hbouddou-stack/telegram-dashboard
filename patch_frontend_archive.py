import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add Archive Button and Details to Student Card
# Find the actions div inside openStudentCard
actions_target = r"<!-- Actions -->\s*<div style=\"display:flex; gap:10px; margin-top:15px; flex-wrap:wrap;\">"
m = re.search(actions_target, c)
if m:
    inject_pos = m.end()
    archive_btn = r"""
                <button class="btn btn-primary" onclick="archiveStudent()" style="background:#ef4444; color:white; border:none; padding:8px 12px; border-radius:8px; display:flex; align-items:center; gap:5px;">
                    🗑️ استبعاد
                </button>
"""
    if "archiveStudent()" not in c:
        c = c[:inject_pos] + archive_btn + c[inject_pos:]
        print("Archive button injected")

# Add import details in the info block
info_target = r"document\.getElementById\('profile-email-text'\)\.textContent = student\.email \|\| '-';"
m2 = re.search(info_target, c)
if m2:
    inject_pos2 = m2.end()
    info_js = r"""
            const createdAt = student.created_at ? new Date(student.created_at + 'Z').toLocaleDateString() : 'N/A';
            const sourceFile = student.source_file ? student.source_file : (student.source === 'excel' ? 'Fichier Excel inconnu' : (student.source || 'Manuel'));
            document.getElementById('profile-import-text').innerHTML = `📅 ${createdAt} <br> 📁 ${sourceFile}`;
"""
    if "profile-import-text" not in c:
        c = c[:inject_pos2] + info_js + c[inject_pos2:]
        print("Import info JS injected")
        
        # Add the HTML placeholder for profile-import-text
        html_target = r'<div class="info-label">رقم الهاتف</div>\s*<div class="info-value" id="profile-phone-text">-</div>\s*</div>'
        m3 = re.search(html_target, c)
        if m3:
            html_inject = r"""
                        <div class="info-item">
                            <div class="info-label">معلومات الاستيراد</div>
                            <div class="info-value" id="profile-import-text" style="font-size:0.75rem; line-height:1.4;">-</div>
                        </div>"""
            c = c[:m3.end()] + html_inject + c[m3.end():]
            print("Import info HTML injected")

# 3. Add archiveStudent JS function
archive_js = r"""
        async function archiveStudent() {
            if(!activeStudentId) return;
            
            const reason = prompt("لماذا تريد استبعاد هذا الطالب؟ (مثال: حساب تجريبي، مكرر...)");
            if(reason === null) return; // cancelled
            
            let adminName = localStorage.getItem('adminName') || 'Admin';
            
            if(confirm('هل أنت متأكد من استبعاد هذا الطالب؟ سيتم إخفاؤه من الإحصائيات.')) {
                try {
                    const res = await fetch('/api/admin/gateway/archive_student', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            student_id: activeStudentId,
                            reason: reason || 'غير محدد',
                            admin_name: adminName
                        })
                    });
                    const data = await res.json();
                    if(data.success) {
                        alert('✅ تم استبعاد الطالب بنجاح');
                        closeCard();
                        filterStudents();
                        loadGeneralSettings(); // To update KPIs if overview is loaded
                    } else {
                        alert('❌ خطأ: ' + data.error);
                    }
                } catch(e) {
                    alert('❌ حدث خطأ في الاتصال');
                }
            }
        }
"""
if "function archiveStudent" not in c:
    c = c.replace('function closeCard() {', archive_js + '\n        function closeCard() {')
    print("archiveStudent JS function injected")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Frontend archive patch complete")
