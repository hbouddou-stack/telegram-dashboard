import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Catch bot_username in fetchStudents / loadStudents
if 'window.BOT_USERNAME =' not in c:
    c = c.replace(
        "allStudents = data.students;",
        "allStudents = data.students;\n                window.BOT_USERNAME = data.bot_username || 'alsirahquizz_bot';"
    )

# 2. Add SMS step in the funnel timeline
sms_html = """
        <!-- ÉTAPE SMS -->
        <div class="timeline-block" id="funnel-step-sms">
            <div class="timeline-dot" style="background:#0ea5e9;"></div>
            <div class="timeline-content">
                <div class="timeline-title">
                    <span>📱 المرحلة : رسالة SMS (Lien Direct)</span>
                    <div>
                        <button class="btn-action" onclick="sendFunnelAction('log_sms')" style="background:#0ea5e9;">📱 إرسال SMS / فتح التطبيق</button>
                    </div>
                </div>
                <div class="timeline-subs">
                    <div class="timeline-sub-item">
                        <span id="f-icon-sms-sent">⏳</span>
                        <span>آخر رسالة SMS :</span>
                        <span id="f-date-sms-sent" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                    <div class="timeline-sub-item">
                        <span id="f-icon-last-source">🔍</span>
                        <span>مصدر الدخول الأخير :</span>
                        <span id="f-source-last-click" style="font-weight:bold; color:var(--accent);">-</span>
                    </div>
                </div>
            </div>
        </div>
"""
if 'funnel-step-sms' not in c:
    c = c.replace("<!-- ÉTAPE FINALE -->", sms_html + "\n        <!-- ÉTAPE FINALE -->")

# 3. Add to sendFunnelAction logic
if "actionType === 'log_sms'" not in c:
    old_wa = "if (actionType === 'log_wa_1' || actionType === 'log_wa_2') {"
    new_sms_logic = """if (actionType === 'log_sms') {
                    if (phoneStr) {
                        let smsBot = window.BOT_USERNAME || 'alsirahquizz_bot';
                        let smsText = encodeURIComponent(`السلام عليكم ${student.first_name || ''}، إليك رابط الدخول الخاص بك للأكاديمية:\\nhttps://t.me/${smsBot}?start=sms_${token}`);
                        finalUrl = `sms:+${phoneStr}?body=${smsText}`;
                    } else {
                        alert("Aucun numéro de téléphone"); return;
                    }
                } else if (actionType === 'log_wa_1' || actionType === 'log_wa_2') {"""
    c = c.replace(old_wa, new_sms_logic)

# 4. Add data to openStudentCard
if "document.getElementById('f-date-sms-sent')" not in c:
    old_setfun = "function setFunnelStep(stepId, dateStr) {"
    new_setfun = """
            if (document.getElementById('f-date-sms-sent')) {
                let smsIcon = document.getElementById('f-icon-sms-sent');
                if (student.sms_sent_at || student.sms_sent) {
                    document.getElementById('f-date-sms-sent').textContent = student.sms_sent_at ? new Date(student.sms_sent_at).toLocaleString('fr-FR') : 'Envoyé';
                    smsIcon.textContent = '✅'; smsIcon.className = 'funnel-icon success';
                } else {
                    document.getElementById('f-date-sms-sent').textContent = '-';
                    smsIcon.textContent = '⏳'; smsIcon.className = 'funnel-icon pending';
                }
            }
            if (document.getElementById('f-source-last-click')) {
                document.getElementById('f-source-last-click').textContent = student.last_click_source || 'Aucun (Organic/Vieux)';
            }
            """ + old_setfun
    c = c.replace(old_setfun, new_setfun)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("admin_gateway.html updated.")
