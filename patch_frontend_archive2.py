import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, l in enumerate(lines):
    if '<div class="info-label">رقم الهاتف</div>' in l:
        new_lines.append(l)
        # Add the import info HTML
        new_lines.append('                        </div>\n')
        new_lines.append('                        <div class="info-item" style="border: 1px solid #e0e0e0; padding: 10px; border-radius: 8px;">\n')
        new_lines.append('                            <div class="info-label">معلومات الاستيراد</div>\n')
        new_lines.append('                            <div class="info-value" id="profile-import-text" style="font-size:0.75rem; line-height:1.4;">-</div>\n')
    
    elif "const foreignNameEl = document.getElementById('profile-foreign-name-text');" in l:
        new_lines.append(l)
        new_lines.append("            const createdAt = student.created_at ? new Date(student.created_at + 'Z').toLocaleDateString() : 'N/A';\n")
        new_lines.append("            const sourceFile = student.source_file ? student.source_file : (student.source === 'excel' ? 'Fichier Excel inconnu' : (student.source || 'Manuel'));\n")
        new_lines.append("            document.getElementById('profile-import-text').innerHTML = `📅 ${createdAt} <br> 📁 ${sourceFile}`;\n")

    elif "<!-- Actions -->" in l and "استبعاد" not in ''.join(lines[i:i+10]):
        new_lines.append(l)
        new_lines.append('                    <button class="btn btn-primary" onclick="archiveStudent()" style="background:#ef4444; color:white; border:none; padding:8px 12px; border-radius:8px; display:flex; align-items:center; gap:5px;">\n')
        new_lines.append('                        🗑️ استبعاد\n')
        new_lines.append('                    </button>\n')
        
    elif "function closeCard() {" in l and "function archiveStudent()" not in ''.join(lines[max(0, i-40):i]):
        archive_js = """
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
        new_lines.append(archive_js)
        new_lines.append(l)

    else:
        new_lines.append(l)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
