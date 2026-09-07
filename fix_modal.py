import io

html_injection = '''
            <style>
                .mtab-container { display: flex; border-bottom: 2px solid var(--border); margin-bottom: 15px; }
                .mtab { flex: 1; text-align: center; padding: 10px; cursor: pointer; font-size: 0.9rem; font-weight: bold; color: var(--text2); transition: 0.2s; }
                .mtab.active { color: var(--accent); border-bottom: 2px solid var(--accent); background: rgba(10,132,255,0.05); }
                .mcontent { display: none; flex-direction: column; gap: 10px; }
                .mcontent.active { display: flex; }
                
                /* Funnel specific */
                .funnel-step { display: flex; align-items: center; gap: 10px; background: var(--surface); padding: 10px; border-radius: 8px; border: 1px solid var(--border); }
                .funnel-icon { width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; background: var(--bg); border: 1px solid var(--border); }
                .funnel-icon.success { background: rgba(52,199,89,0.1); border-color: #34c759; color: #34c759; }
                .funnel-icon.pending { background: rgba(255,59,48,0.1); border-color: #ff3b30; color: #ff3b30; }
                .funnel-text { flex: 1; font-size: 0.85rem; font-weight: 500; }
                .funnel-date { font-size: 0.75rem; color: var(--text2); dir: ltr; }
            </style>

            <div class="mtab-container">
                <div class="mtab active" onclick="switchModalTab('general')" id="mtab-general">????</div>
                <div class="mtab" onclick="switchModalTab('academy')" id="mtab-academy">??????????</div>
                <div class="mtab" onclick="switchModalTab('telegram')" id="mtab-telegram">????????</div>
                <div class="mtab" onclick="switchModalTab('funnel')" id="mtab-funnel">???? ????????</div>
            </div>

            <!-- Tab 1: General -->
            <div id="mcontent-general" class="mcontent active">
                <div class="chip" id="profile-name" style="background:rgba(10,132,255,0.15); border-color:#0a84ff; color:#0a84ff; display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ????? ?????? : <span id="profile-name-text">-</span></div>
                <div class="chip" id="profile-email" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ?????? ?????????? : <span id="profile-email-text" dir="ltr">-</span></div>
                <div class="chip" id="profile-phone" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ?????? : <span id="profile-phone-text" dir="ltr" style="text-align:left;">-</span></div>
                <div class="chip" id="profile-dob" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ????? ??????? : <span id="profile-dob-text">-</span></div>
                <div class="chip" id="profile-gender" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">? ????? : <span id="profile-gender-text">-</span></div>
                <div class="chip" id="profile-profession" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ?????? : <span id="profile-profession-text">-</span></div>
            </div>

            <!-- Tab 2: Academy -->
            <div id="mcontent-academy" class="mcontent">
                <div class="chip" id="profile-studentid" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ??? ?????? : <span id="profile-studentid-text">-</span></div>
                <div class="chip" id="profile-year" style="background:rgba(255,159,10,0.15); border-color:#ff9f0a; color:#ff9f0a; display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ??????? / ????? : <span id="profile-year-text">-</span></div>
                <div class="chip" id="profile-payment" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ???? ????? : <span id="profile-payment-text">-</span></div>
                <div class="chip" id="profile-inscription" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ????? ??????? : <span id="profile-inscription-text">-</span></div>
                <div class="chip" id="profile-source" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ?????? : <span id="profile-source-text">-</span></div>
                
                <div style="background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:12px; margin-top:5px; font-size:0.85rem; color:var(--text1);">
                    <strong>???? ???????:</strong> <span id="profile-membership">???? ???????...</span>
                </div>
            </div>

            <!-- Tab 3: Telegram -->
            <div id="mcontent-telegram" class="mcontent">
                <div class="chip" id="profile-tg-container" style="background:rgba(52,199,89,0.15); border-color:#34c759; color:#34c759; justify-content:flex-start; align-items:center; gap:8px;">? ???? ????? : <span id="profile-tg-display">-</span></div>
                <div class="chip" id="profile-tg-username-container" style="background:rgba(52,199,89,0.08); border-color:#34c759; color:#34c759; justify-content:flex-start; align-items:center; gap:8px;">@ ??? ???????? : <span id="profile-tg-username-text" dir="ltr">-</span></div>
                <div class="chip" id="profile-tgid" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">?? ????? ???????? : <span id="profile-tgid-text" dir="ltr">-</span></div>
            </div>

            <!-- Tab 4: Funnel -->
            <div id="mcontent-funnel" class="mcontent">
                <div class="funnel-step">
                    <div class="funnel-icon" id="f-icon-email-sent">-</div>
                    <div class="funnel-text">????? ??????? ?????</div>
                    <div class="funnel-date" id="f-date-email-sent">-</div>
                </div>
                <div class="funnel-step">
                    <div class="funnel-icon" id="f-icon-email-opened">-</div>
                    <div class="funnel-text">??? ???????</div>
                    <div class="funnel-date" id="f-date-email-opened">-</div>
                </div>
                <div class="funnel-step">
                    <div class="funnel-icon" id="f-icon-email-clicked">-</div>
                    <div class="funnel-text">????? ??? ??????</div>
                    <div class="funnel-date" id="f-date-email-clicked">-</div>
                </div>
                <div class="funnel-step">
                    <div class="funnel-icon" id="f-icon-whatsapp-sent">-</div>
                    <div class="funnel-text">????? ?????? (?????)</div>
                    <div class="funnel-date" id="f-date-whatsapp-sent">-</div>
                </div>
                <div class="funnel-step">
                    <div class="funnel-icon" id="f-icon-bot-started">-</div>
                    <div class="funnel-text">??? ?????? ?????</div>
                    <div class="funnel-date" id="f-date-bot-started">-</div>
                </div>
                <div class="funnel-step">
                    <div class="funnel-icon" id="f-icon-group-joined">-</div>
                    <div class="funnel-text">???????? ????????</div>
                    <div class="funnel-date" id="f-date-group-joined">-</div>
                </div>
            </div>
'''

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()
    
start_marker = '<div class="profile-chips-container"'
end_marker = '<div style="display:flex; gap:10px; margin-bottom:18px;">'

if start_marker in c and end_marker in c:
    s_idx = c.find(start_marker)
    e_idx = c.find(end_marker)
    
    # We strip out the old chips and the membership block which were all before the buttons container
    new_c = c[:s_idx] + html_injection + '\n              <div style="display:flex; gap:10px; margin-bottom:18px;">\n                  <button class="btn btn-danger" id="profile-unlink-btn" onclick="manualUnlink()" style="padding:10px; font-size:0.85rem;">?? ??? ????????</button>\n'
    
    # Wait, e_idx points to `<div style="display:flex; gap:10px; margin-bottom:18px;">`
    # Let's find the closing of the unlink button to append the rest
    unlink_end = c.find('</button>', c.find('profile-unlink-btn', e_idx)) + 9
    new_c += c[unlink_end:]
    
    js_injection = '''
        function switchModalTab(tabId) {
            ['general', 'academy', 'telegram', 'funnel'].forEach(t => {
                document.getElementById('mtab-' + t).classList.remove('active');
                document.getElementById('mcontent-' + t).classList.remove('active');
            });
            document.getElementById('mtab-' + tabId).classList.add('active');
            document.getElementById('mcontent-' + tabId).classList.add('active');
        }
        
        function setFunnelStep(stepId, dateVal) {
            const icon = document.getElementById('f-icon-' + stepId);
            const dateEl = document.getElementById('f-date-' + stepId);
            if (dateVal && dateVal !== '0' && dateVal !== 'false') {
                icon.className = 'funnel-icon success';
                icon.innerHTML = '?';
                dateEl.textContent = String(dateVal).substring(0,16).replace('T', ' ');
            } else {
                icon.className = 'funnel-icon pending';
                icon.innerHTML = '?';
                dateEl.textContent = '?? ??? ???';
            }
        }
'''
    new_c = new_c.replace('let currentStudentId = null;', 'let currentStudentId = null;' + js_injection)
    
    update_js = '''
            // Funnel Logic
            setFunnelStep('email-sent', student.email_sent_at || (student.email_sent ? '???' : null));
            setFunnelStep('email-opened', student.email_opened_at);
            setFunnelStep('email-clicked', student.email_clicked_at || student.folder_clicked_at);
            setFunnelStep('whatsapp-sent', student.whatsapp_sent_at || (student.whatsapp_sent ? '???' : null));
            setFunnelStep('bot-started', student.bot_started_at);
            setFunnelStep('group-joined', student.joined_at || (student.group_joined ? '???' : null));
            
            switchModalTab('general');
'''
    new_c = new_c.replace("document.getElementById('profile-source-text').textContent = student.source || '??? ?????';", "document.getElementById('profile-source-text').textContent = student.source || '??? ?????';" + update_js)

    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(new_c)
    print("Modal patched successfully!")
else:
    print("Markers not found!")
