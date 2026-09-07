import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix translations
old_dict = "const trNat = {'marocaine':'مغربية', 'marocain':'مغربي', 'algerienne':'جزائرية', 'algérienne':'جزائرية', 'algerien':'جزائري', 'algérien':'جزائري', 'francaise':'فرنسية', 'française':'فرنسية', 'francais':'فرنسي', 'français':'فرنسي', 'tunisienne':'تونسية', 'tunisien':'تونسي'};"
new_dict = "const trNat = {'marocaine':'مغربية', 'marocain':'مغربي', 'algerienne':'جزائرية', 'algérienne':'جزائرية', 'algerien':'جزائري', 'algérien':'جزائري', 'francaise':'فرنسية', 'française':'فرنسية', 'francais':'فرنسي', 'français':'فرنسي', 'tunisienne':'تونسية', 'tunisien':'تونسي', 'moroccan':'مغربي', 'algerian':'جزائري', 'french':'فرنسي', 'tunisian':'تونسي', 'belgian':'بلجيكي', 'swiss':'سويسري', 'canadian':'كندي', 'egyptian':'مصري'};"
if old_dict in c:
    c = c.replace(old_dict, new_dict)
else:
    print("WARNING: old_dict not found")

# Update UI elements in HTML (Emoji changes)
c = c.replace('📓 ID académique', '🎓 Num. Étudiant')
c = c.replace('id="profile-source-text">-</span>', 'id="profile-source-text">-</span> <span id="profile-phone-text" style="margin-left:10px; font-weight:bold; color:var(--text1);" dir="ltr"></span>')

# Fix name rendering correctly using string replacement
old_name = "const fullName = String(student.first_name || '').trim() + (student.last_name ? ' ' + String(student.last_name).trim() : '');\n            document.getElementById('profile-name-text').textContent = fullName.trim() || 'غير محدد';"
new_name = '''const first = String(student.first_name || '').trim();
            const last = String(student.last_name || '').trim();
            document.getElementById('profile-name-text').innerHTML = `${last || '-'} <span style="font-size:0.9rem; color:var(--text2); font-weight:normal; margin-left:10px;">${first || ''}</span>`;'''
if old_name in c:
    c = c.replace(old_name, new_name)
else:
    print("WARNING: old_name not found")

# Fix source rendering
old_src = "const srcEl = document.getElementById('profile-source-text');\n            if(srcEl) srcEl.textContent = student.source || ' ';"
new_src = '''const srcEl = document.getElementById('profile-source-text');
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
if old_src in c:
    c = c.replace(old_src, new_src)
else:
    print("WARNING: old_src not found")

# Fix Timeline WA and TG
old_timeline_search = '<!-- ÉTAPE 3 : WhatsApp -->'
if old_timeline_search in c:
    print("Timeline found, we can patch it!")
    
    # Let's extract the timeline chunk to replace
    start_idx = c.find('<!-- ÉTAPE 3 : WhatsApp -->')
    end_idx = c.find('</div>\n</div>\n            <div style="display:flex; gap:10px;')
    
    if start_idx != -1 and end_idx != -1:
        new_timeline = '''<!-- ÉTAPE 3 : WhatsApp -->
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
    '''
        c = c[:start_idx] + new_timeline + c[end_idx:]
    else:
        print("WARNING: Timeline indices not found")
else:
    print("WARNING: ÉTAPE 3 not found in timeline")


# Add TG script block
tg_script = '<script src="https://telegram.org/js/telegram-web-app.js"></script>'
if tg_script not in c:
    c = c.replace('<head>', '<head>\n' + tg_script + '\n<script>if(window.Telegram && Telegram.WebApp) { Telegram.WebApp.expand(); }</script>')


# Update Funnel JS
js_funnel_logic = "setFunnelStep('bot-started', student.bot_started_at);\n                setFunnelStep('group-joined', student.joined_at || (student.group_joined ? '' : null));"
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
if js_funnel_logic in c:
    c = c.replace(js_funnel_logic, js_funnel_new)
else:
    print("WARNING: js_funnel_logic not found")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("SUCCESS")
