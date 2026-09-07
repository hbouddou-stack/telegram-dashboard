import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix translations
old_dict = "const trNat = {'marocaine':'', 'marocain':'', 'algerienne':'', 'algrienne':'', 'algerien':'', 'algrien':'', 'francaise':'', 'franaise':'', 'francais':'', 'franais':'', 'tunisienne':'', 'tunisien':''};"
new_dict = "const trNat = {'marocaine':'مغربية', 'marocain':'مغربي', 'algerienne':'جزائرية', 'algrienne':'جزائرية', 'algerien':'جزائري', 'algrien':'جزائري', 'francaise':'فرنسية', 'franaise':'فرنسية', 'francais':'فرنسي', 'franais':'فرنسي', 'tunisienne':'تونسية', 'tunisien':'تونسي', 'moroccan':'مغربي', 'algerian':'جزائري', 'french':'فرنسي', 'tunisian':'تونسي', 'belgian':'بلجيكي', 'swiss':'سويسري', 'canadian':'كندي', 'egyptian':'مصري'};"
if old_dict in c:
    c = c.replace(old_dict, new_dict)

# Update UI elements in HTML
c = c.replace('📓 ID académique :', '🎓 Numéro étudiant :')
c = c.replace('📓 ID académique', '🎓 Numéro étudiant')
c = c.replace('id="profile-source-text">-</span>', 'id="profile-source-text">-</span> <span id="profile-phone-text" style="margin-left:10px; font-weight:bold; color:var(--text1);" dir="ltr"></span>')

# Replace Name rendering
old_name_render = r"const fullName = String(student.first_name || '').trim() + (student.last_name ? ' ' + String(student.last_name).trim() : '');\s*document.getElementById\('profile-name-text'\).textContent = fullName.trim\(\) \|\| ' ';"
new_name_render = '''const first = String(student.first_name || '').trim();
            const last = String(student.last_name || '').trim();
            document.getElementById('profile-name-text').innerHTML = `${last || '-'} <span style="font-size:0.9rem; color:var(--text2); font-weight:normal; margin-left:10px;">${first || ''}</span>`;'''
c = re.sub(old_name_render, new_name_render, c)

# Replace Source rendering to make Sheet button-like and display exact phone
old_src_render = "const srcEl = document.getElementById('profile-source-text');\n            if(srcEl) srcEl.textContent = student.source || ' ';"
new_src_render = '''const srcEl = document.getElementById('profile-source-text');
            if(srcEl) {
                const s = String(student.source || '').toLowerCase();
                if(s.includes('sheet') || s.includes('google')) {
                    srcEl.innerHTML = '<span style="background:#0f9d58; color:white; padding:2px 6px; border-radius:4px; font-size:0.8rem;">Sheet</span>';
                } else if(s.includes('excel')) {
                    srcEl.innerHTML = '<span style="background:#107c41; color:white; padding:2px 6px; border-radius:4px; font-size:0.8rem;">Excel</span>';
                } else {
                    srcEl.textContent = student.source || ' ';
                }
            }
            const phoneEl = document.getElementById('profile-phone-text');
            if(phoneEl) phoneEl.textContent = student.phone || '';'''
c = c.replace(old_src_render, new_src_render)


# Funnel Timeline HTML update
old_timeline = r'<!-- ÉTAPE 3 : WhatsApp -->.*?<!-- ÉTAPE 4 : Intégration Finale -->.*?</div>\s*</div>\s*</div>\s*</div>\s*</div>'

new_timeline = r'''<!-- ÉTAPE 3 : WhatsApp -->
        <div class="timeline-block" id="funnel-step-wa">
            <div class="timeline-dot" style="background:#25D366;"></div>
            <div class="timeline-content">
                <div class="timeline-title">
                    <span>💬 ÉTAPE 3 : WhatsApp</span>
                    <div>
                        <button class="btn-action btn-wa" onclick="sendFunnelAction('log_wa_1')" style="margin-bottom:5px;">💬 WhatsApp 1</button>
                        <button class="btn-action btn-wa" onclick="sendFunnelAction('log_wa_2')">💬 WhatsApp 2 (Dernier)</button>
                    </div>
                </div>
                <div class="timeline-subs">
                    <div class="timeline-sub-item">
                        <span id="f-icon-whatsapp-sent">⏳</span>
                        <span>Dernier WhatsApp envoyé :</span>
                        <span id="f-date-whatsapp-sent" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- ÉTAPE 4 : Telegram -->
        <div class="timeline-block" id="funnel-step-tg">
            <div class="timeline-dot" style="background:#0088cc;"></div>
            <div class="timeline-content">
                <div class="timeline-title">
                    <span>✈️ ÉTAPE 4 : Envoi sur Telegram</span>
                    <button class="btn-action" onclick="sendFunnelAction('log_tg_1')" style="background:#0088cc;">✈️ Message direct</button>
                </div>
                <div class="timeline-subs">
                    <div class="timeline-sub-item">
                        <span id="f-icon-telegram-sent">⏳</span>
                        <span>Message Telegram envoyé :</span>
                        <span id="f-date-telegram-sent" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- ÉTAPE FINALE -->
        <div class="timeline-block" id="funnel-step-final">
            <div class="timeline-dot" style="background:#8b5cf6;"></div>
            <div class="timeline-content">
                <div class="timeline-title">
                    <span>🏁 ÉTAPE FINALE : Action de l'Élève</span>
                </div>
                <div class="timeline-subs">
                    <div class="timeline-sub-item">
                        <span id="f-icon-bot-started">⏳</span>
                        <span>Appuyer sur le lien (Démarrage) :</span>
                        <span id="f-date-bot-started" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                    <div class="timeline-sub-item">
                        <span id="f-icon-folder-clicked">⏳</span>
                        <span>Appuyer sur le bouton Folder :</span>
                        <span id="f-date-folder-clicked" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                    <div class="timeline-sub-item">
                        <span id="f-icon-group-joined">⏳</span>
                        <span>Rejoindre le groupe :</span>
                        <span id="f-date-group-joined" dir="ltr" style="font-weight:bold;">-</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
'''

c = re.sub(old_timeline, new_timeline, c, flags=re.DOTALL)

# Add f-icon-folder-clicked and telegram to JS
js_funnel_logic = r'''setFunnelStep\('bot-started', student\.bot_started_at\);
                setFunnelStep\('group-joined', student\.joined_at \|\| \(student\.group_joined \? '' : null\)\);'''

js_funnel_new = '''setFunnelStep('bot-started', student.bot_started_at);
                setFunnelStep('folder-clicked', student.folder_clicked_at);
                setFunnelStep('group-joined', student.joined_at || (student.group_joined ? '' : null));
                
                // Extra checks for manual telegram log
                const tgLogs = data.logs ? data.logs.filter(l => l.action_type === 'TELEGRAM_CONTACT') : [];
                if (tgLogs.length > 0) {
                    setFunnelStep('telegram-sent', tgLogs[0].timestamp);
                } else {
                    setFunnelStep('telegram-sent', null);
                }'''

c = re.sub(js_funnel_logic, js_funnel_new, c)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Card and Timeline updated!")
