import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix sendFunnelAction
js_target = r"if (data.success) {"
js_new = r"""if (data.success) {
                    // Open WA or TG links based on action
                    const student = allStudents.find(s => s.student_id === activeStudentId);
                    if (student) {
                        const token = student.magic_token || student.student_id;
                        let text = encodeURIComponent(`السلام عليكم، هذا رابط الدخول الخاص بك للأكاديمية:\nhttps://t.me/Oswah_academy_bot?start=${actionType === 'log_wa_1' ? 'w1' : 'w2'}_${token}`);
                        
                        if (actionType === 'log_wa_1' || actionType === 'log_wa_2') {
                            let phoneStr = String(student.phone || '').replace(/\D/g, '');
                            if (phoneStr) {
                                window.open(`https://wa.me/${phoneStr}?text=${text}`, '_blank');
                            } else {
                                alert("Aucun numéro de téléphone pour cet étudiant.");
                            }
                        } else if (actionType === 'log_tg_1') {
                            let phoneStr = String(student.phone || '').replace(/\D/g, '');
                            if (phoneStr) {
                                window.open(`https://t.me/+${phoneStr}`, '_blank');
                            } else {
                                alert("Aucun numéro de téléphone pour cet étudiant.");
                            }
                        }
                    }
"""

c = c.replace(js_target, js_new)

# Add TG button
old_wa_buttons = r"""<button class="btn-action btn-wa" onclick="sendFunnelAction('log_wa_1')" style="margin-bottom:5px;">💬 واتساب 1</button>
                        <button class="btn-action btn-wa" onclick="sendFunnelAction('log_wa_2')">💬 واتساب 2 (أخير)</button>"""
new_wa_buttons = r"""<button class="btn-action btn-wa" onclick="sendFunnelAction('log_wa_1')" style="margin-bottom:5px;">💬 واتساب 1</button>
                        <button class="btn-action btn-wa" onclick="sendFunnelAction('log_wa_2')" style="margin-bottom:5px;">💬 واتساب 2</button>
                        <button class="btn-action" onclick="sendFunnelAction('log_tg_1')" style="background:#0088cc; color:white;">✈️ تليجرام</button>"""
c = c.replace(old_wa_buttons, new_wa_buttons)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Patched JS buttons')
