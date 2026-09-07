import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# CSS pour la timeline
timeline_css = '''
<style>
.timeline {
    position: relative;
    padding-right: 20px;
    margin-top: 10px;
}
.timeline::before {
    content: '';
    position: absolute;
    right: 4px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--border);
}
.timeline-block {
    position: relative;
    margin-bottom: 20px;
}
.timeline-dot {
    position: absolute;
    right: -20px;
    top: 5px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--primary);
    border: 2px solid var(--bg);
}
.timeline-content {
    background: var(--bg);
    border: 1px solid var(--border);
    padding: 12px;
    border-radius: 8px;
}
.timeline-title {
    font-weight: bold;
    color: var(--text1);
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.timeline-subs {
    font-size: 0.85rem;
    color: var(--text2);
    margin-top: 10px;
    border-top: 1px dashed var(--border);
    padding-top: 8px;
}
.timeline-sub-item {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}
.btn-action {
    background: var(--primary);
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8rem;
    display: flex;
    align-items: center;
    gap: 5px;
}
.btn-action:hover {
    opacity: 0.9;
}
.btn-wa {
    background: #25D366;
}
.success-banner {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid #22c55e;
    color: #16a34a;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    font-weight: bold;
    margin-top: 15px;
    margin-bottom: 15px;
}
</style>
'''

if '.timeline-block' not in c:
    c = c.replace('</head>', timeline_css + '\n</head>')

# Remplacer le contenu de mcontent-funnel
old_funnel_pattern = re.compile(r'<div id="mcontent-funnel" class="mcontent" style="overflow-y:auto; flex:1; padding-right:5px;">.*?</div>\s+</div>', re.DOTALL)

new_funnel_html = '''<div id="mcontent-funnel" class="mcontent" style="overflow-y:auto; flex:1; padding-right:5px;">
    
    <div id="funnel-victory-banner" class="success-banner" style="display:none;">
        🎉 الهدف تحقق : الطالب مسجل في المنصة ولا يحتاج إلى متابعة إضافية !
    </div>

    <div class="timeline" id="funnel-timeline">
        
        <!-- ÉTAPE 1 : Email -->
        <div class="timeline-block" id="funnel-step-email1">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <div class="timeline-title">
                    <span>✉️ المرحلة 1 : الإيميل الترحيبي</span>
                    <button class="btn-action" onclick="sendFunnelAction('send_email_1')">إرسال الإيميل</button>
                </div>
                <div class="timeline-subs">
                    <div class="timeline-sub-item">
                        <span id="f-icon-email-sent">⏳</span>
                        <span>تم الإرسال :</span>
                        <span id="f-date-email-sent" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                    <div class="timeline-sub-item">
                        <span id="f-icon-email-opened">⏳</span>
                        <span>تم فتح الإيميل :</span>
                        <span id="f-date-email-opened" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                    <div class="timeline-sub-item">
                        <span id="f-icon-email-clicked">⏳</span>
                        <span>تم النقر على الرابط :</span>
                        <span id="f-date-email-clicked" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- ÉTAPE 2 : Email 2 (Relance) -->
        <div class="timeline-block" id="funnel-step-email2">
            <div class="timeline-dot" style="background:#f59e0b;"></div>
            <div class="timeline-content">
                <div class="timeline-title">
                    <span>📨 المرحلة 2 : إيميل التذكير</span>
                    <button class="btn-action" onclick="sendFunnelAction('send_email_2')" style="background:#f59e0b;">إرسال تذكير</button>
                </div>
            </div>
        </div>

        <!-- ÉTAPE 3 : WhatsApp -->
        <div class="timeline-block" id="funnel-step-wa">
            <div class="timeline-dot" style="background:#25D366;"></div>
            <div class="timeline-content">
                <div class="timeline-title">
                    <span>💬 المرحلة 3 : التواصل عبر واتساب</span>
                    <div>
                        <button class="btn-action btn-wa" onclick="sendFunnelAction('log_wa_1')" style="margin-bottom:5px;">إرسال واتساب 1</button>
                        <button class="btn-action btn-wa" onclick="sendFunnelAction('log_wa_2')">إرسال واتساب 2 (عاجل)</button>
                    </div>
                </div>
                <div class="timeline-subs">
                    <div class="timeline-sub-item">
                        <span id="f-icon-whatsapp-sent">⏳</span>
                        <span>تم التواصل (واتساب) :</span>
                        <span id="f-date-whatsapp-sent" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- ÉTAPE 4 : Intégration Finale -->
        <div class="timeline-block" id="funnel-step-final">
            <div class="timeline-dot" style="background:#8b5cf6;"></div>
            <div class="timeline-content">
                <div class="timeline-title">
                    <span>🎓 المرحلة 4 : التسجيل النهائي</span>
                </div>
                <div class="timeline-subs">
                    <div class="timeline-sub-item">
                        <span id="f-icon-bot-started">⏳</span>
                        <span>بدأ استخدام البوت :</span>
                        <span id="f-date-bot-started" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                    <div class="timeline-sub-item">
                        <span id="f-icon-group-joined">⏳</span>
                        <span>انضم للمجموعة :</span>
                        <span id="f-date-group-joined" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                </div>
            </div>
        </div>

    </div>
</div>
</div>'''

c = old_funnel_pattern.sub(new_funnel_html, c)

# Ajouter la fonction Javascript pour les actions et mettre à jour la logique d'affichage
js_functions = '''
        async function sendFunnelAction(actionType) {
            if(!activeStudentId) return;
            
            // Si c'est WA, on l'ouvre dans un nouvel onglet avant d'appeler l'API
            if (actionType.startsWith('log_wa_')) {
                // Trouver le téléphone et le lien
                const st = allStudents.find(s => s.student_id === activeStudentId);
                if (st && st.phone) {
                    let phoneStr = String(st.phone).replace(/[^0-9]/g, '');
                    let link = 'https://t.me/Alsirahquizz_bot?start=' + (st.magic_token || 'auth_'+st.student_id);
                    let message = `السلام عليكم ورحمة الله وبركاته ${st.first_name || ''}،\\n\\nهذا تذكير من أكاديمية القدوة. يرجى تفعيل حسابك بالضغط على الرابط التالي:\\n${link}`;
                    let waUrl = `https://wa.me/${phoneStr}?text=${encodeURIComponent(message)}`;
                    window.open(waUrl, '_blank');
                }
            }

            try {
                // Montrer qu'on charge (ou bloquer bouton)
                const res = await fetch('/api/admin/gateway/action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: actionType, student_id: activeStudentId })
                });
                const data = await res.json();
                if(data.success) {
                    alert('✅ العملية تمت بنجاح !');
                    // Rafraîchir pour voir les nouvelles dates
                    loadStudents();
                } else {
                    alert('❌ خطأ : ' + data.error);
                }
            } catch (e) {
                alert('Erreur réseau');
            }
        }
'''

if 'sendFunnelAction' not in c:
    c = c.replace('function switchModalTab(tabId) {', js_functions + '\n        function switchModalTab(tabId) {')


# Modifier setFunnelStep et la logique de condition de victoire
victory_logic_old = '''// Funnel & Tab logic
            if(typeof setFunnelStep === 'function') {
                setFunnelStep('email-sent', student.email_sent_at || (student.email_sent ? 'نعم' : null));
                setFunnelStep('email-opened', student.email_opened_at);
                setFunnelStep('email-clicked', student.email_clicked_at || student.folder_clicked_at);
                setFunnelStep('whatsapp-sent', student.whatsapp_sent_at || (student.whatsapp_sent ? 'نعم' : null));
                setFunnelStep('bot-started', student.bot_started_at);
                setFunnelStep('group-joined', student.joined_at || (student.group_joined ? 'نعم' : null));
                switchModalTab('general');
            }'''

victory_logic_new = '''// Funnel & Tab logic
            if(typeof setFunnelStep === 'function') {
                setFunnelStep('email-sent', student.email_sent_at || (student.email_sent ? 'نعم' : null));
                setFunnelStep('email-opened', student.email_opened_at);
                setFunnelStep('email-clicked', student.email_clicked_at || student.folder_clicked_at);
                setFunnelStep('whatsapp-sent', student.whatsapp_sent_at || (student.whatsapp_sent ? 'نعم' : null));
                setFunnelStep('bot-started', student.bot_started_at);
                setFunnelStep('group-joined', student.joined_at || (student.group_joined ? 'نعم' : null));
                
                // CONDITION DE VICTOIRE
                const victoryBanner = document.getElementById('funnel-victory-banner');
                const stepEmail2 = document.getElementById('funnel-step-email2');
                const stepWa = document.getElementById('funnel-step-wa');
                
                if (student.telegram_id) {
                    // L'élève est synchronisé ! On cache Email2 et WA, on montre le bandeau
                    if (victoryBanner) victoryBanner.style.display = 'block';
                    if (stepEmail2) stepEmail2.style.display = 'none';
                    if (stepWa) stepWa.style.display = 'none';
                } else {
                    // L'élève n'est pas synchronisé. On montre tout.
                    if (victoryBanner) victoryBanner.style.display = 'none';
                    if (stepEmail2) stepEmail2.style.display = 'block';
                    if (stepWa) stepWa.style.display = 'block';
                }
                
                switchModalTab('general');
            }'''

c = c.replace(victory_logic_old, victory_logic_new)


with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Funnel UI updated successfully.")
