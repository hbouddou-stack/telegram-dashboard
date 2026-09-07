import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Make modal full screen
c = c.replace('<div class="modal">', '<div class="modal" id="fiche-eleve-modal" style="width: 95%; max-width: 1200px; height: 90vh; display: flex; flex-direction: column;">', 1)

# Make the modal content scrollable
c = c.replace('<div id="mcontent-general" class="mcontent active">', '<div id="mcontent-general" class="mcontent active" style="overflow-y:auto; flex:1; padding-right:5px;">')
c = c.replace('<div id="mcontent-academy" class="mcontent">', '<div id="mcontent-academy" class="mcontent" style="overflow-y:auto; flex:1; padding-right:5px;">')
c = c.replace('<div id="mcontent-telegram" class="mcontent">', '<div id="mcontent-telegram" class="mcontent" style="overflow-y:auto; flex:1; padding-right:5px;">')
c = c.replace('<div id="mcontent-funnel" class="mcontent">', '<div id="mcontent-funnel" class="mcontent" style="overflow-y:auto; flex:1; padding-right:5px;">')

# Add Country, Nationality, Arabic level to General tab
general_chips = """<div class="chip" id="profile-profession" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">💼 المهنة : <span id="profile-profession-text">-</span></div>
                <div class="chip" id="profile-country" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">🌍 بلد الإقامة : <span id="profile-country-text">-</span></div>
                <div class="chip" id="profile-nationality" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">🪪 الجنسية : <span id="profile-nationality-text">-</span></div>
                <div class="chip" id="profile-arabiclevel" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">🗣️ مستوى اللغة العربية : <span id="profile-arabiclevel-text">-</span></div>"""

c = c.replace('<div class="chip" id="profile-profession" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">💼 المهنة : <span id="profile-profession-text">-</span></div>', general_chips)

# Update Javascript
js_update = """
            // Funnel Logic
            setFunnelStep('email-sent', student.email_sent_at || (student.email_sent ? 'نعم' : null));
            setFunnelStep('email-opened', student.email_opened_at);
            setFunnelStep('email-clicked', student.email_clicked_at || student.folder_clicked_at);
            setFunnelStep('whatsapp-sent', student.whatsapp_sent_at || (student.whatsapp_sent ? 'نعم' : null));
            setFunnelStep('bot-started', student.bot_started_at);
            setFunnelStep('group-joined', student.joined_at || (student.group_joined ? 'نعم' : null));
            
            document.getElementById('profile-profession-text').textContent = student.profession || '-';
            document.getElementById('profile-country-text').textContent = student.country || '-';
            document.getElementById('profile-nationality-text').textContent = student.nationality || '-';
            document.getElementById('profile-arabiclevel-text').textContent = student.arabic_level || '-';
            
            // Age Calculator
            let ageText = student.dob || '-';
            if (student.dob) {
                try {
                    let parts = student.dob.split(/[\/\-]/);
                    let d = null;
                    if(parts.length === 3) {
                        if(parts[0].length === 4) d = new Date(parts[0], parts[1]-1, parts[2]);
                        else d = new Date(parts[2], parts[1]-1, parts[0]);
                    }
                    if(d && !isNaN(d.getTime())) {
                        let today = new Date();
                        let years = today.getFullYear() - d.getFullYear();
                        let months = today.getMonth() - d.getMonth();
                        if (months < 0 || (months === 0 && today.getDate() < d.getDate())) {
                            years--;
                            months += 12;
                        }
                        ageText = student.dob + ' (' + years + ' سنة و ' + months + ' أشهر)';
                    }
                } catch(e) {}
            }
            document.getElementById('profile-dob-text').textContent = ageText;
            
            switchModalTab('general');
"""

c = c.replace("""
            // Funnel Logic
            setFunnelStep('email-sent', student.email_sent_at || (student.email_sent ? 'نعم' : null));
            setFunnelStep('email-opened', student.email_opened_at);
            setFunnelStep('email-clicked', student.email_clicked_at || student.folder_clicked_at);
            setFunnelStep('whatsapp-sent', student.whatsapp_sent_at || (student.whatsapp_sent ? 'نعم' : null));
            setFunnelStep('bot-started', student.bot_started_at);
            setFunnelStep('group-joined', student.joined_at || (student.group_joined ? 'نعم' : null));
            
            switchModalTab('general');
""", js_update)

# Fix switchModalTab if it was previously injected into `let currentStudentId = null;`
# Actually, I injected `function switchModalTab(tabId) {...}` earlier. 
# But wait, why wasn't `onclick="switchModalTab('general')"` triggering?
# Because `switchModalTab` was inside `window.onload = function() { ... }` ? NO! Wait, let me check.
with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("Updated successfully")
