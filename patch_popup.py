import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_func_pattern = r'async function sendFunnelAction\(actionType\) \{.*?\n        \}'
new_func = '''async function sendFunnelAction(actionType) {
            if (!activeStudentId) return;
            if (!confirm('Voulez-vous vraiment effectuer cette action ?')) return;
            
            const student = allStudents.find(s => s.student_id === activeStudentId);
            let finalUrl = null;
            
            if (student) {
                const token = student.magic_token || student.student_id;
                let text = encodeURIComponent(`السلام عليكم، هذا رابط الدخول الخاص بك للأكاديمية:\\nhttps://t.me/Oswah_academy_bot?start=${actionType === 'log_wa_1' ? 'w1' : 'w2'}_${token}`);
                let phoneStr = String(student.phone || '').replace(/\\D/g, '');
                
                if (actionType === 'log_wa_1' || actionType === 'log_wa_2') {
                    if (phoneStr) {
                        finalUrl = `https://wa.me/${phoneStr}?text=${text}`;
                    } else {
                        alert("Aucun numéro de téléphone pour cet étudiant.");
                        return;
                    }
                } else if (actionType === 'log_tg_1') {
                    if (phoneStr) {
                        finalUrl = `https://t.me/+${phoneStr}`;
                    } else {
                        alert("Aucun numéro de téléphone pour cet étudiant.");
                        return;
                    }
                }
            }
            
            if (finalUrl) {
                window.open(finalUrl, '_blank');
            }
            
            try {
                const res = await fetch('/api/admin/gateway/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        action: actionType,
                        student_id: activeStudentId
                    })
                });
                const data = await res.json();
                if (data.success) {
                    if(actionType.includes('email')) {
                        alert('Action réussie !');
                    }
                    loadStudents();
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch(e) {}
        }'''

if re.search(old_func_pattern, c, re.DOTALL):
    c = re.sub(old_func_pattern, new_func.replace('\\', '\\\\'), c, flags=re.DOTALL)
    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Patched JS')
else:
    print('Not found')
