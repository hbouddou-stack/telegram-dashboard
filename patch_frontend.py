import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace Tab 2 Academy Year label (المستوى) and add School Level (المستوى الدراسي)
academy_old = '<div class="chip" id="profile-year" style="background:rgba(255,159,10,0.15); border-color:#ff9f0a; color:#ff9f0a; display:flex; justify-content:flex-start; align-items:center; gap:8px;">📚 المستوى / السنة : <span id="profile-year-text">-</span></div>'
academy_new = """<div class="chip" id="profile-year" style="background:rgba(255,159,10,0.15); border-color:#ff9f0a; color:#ff9f0a; display:flex; justify-content:flex-start; align-items:center; gap:8px;">📚 المستوى : <span id="profile-year-text">-</span></div>
                 <div class="chip" id="profile-school-level" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">🏫 المستوى الدراسي : <span id="profile-school-level-text">-</span></div>"""
c = c.replace(academy_old, academy_new)

# Add TG extra info inside Tab 3 Telegram
tg_old = '<div class="chip" id="profile-tgid" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">🆔 معرّف تيليجرام : <span id="profile-tgid-text" dir="ltr">-</span></div>'
tg_new = """<div class="chip" id="profile-tgid" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">🆔 معرّف تيليجرام : <span id="profile-tgid-text" dir="ltr">-</span></div>
            <div class="chip" id="profile-tg-firstname" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">👤 الاسم الأول : <span id="profile-tg-firstname-text">-</span></div>
            <div class="chip" id="profile-tg-lastname" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">👤 الاسم العائلي : <span id="profile-tg-lastname-text">-</span></div>
            <div class="chip" id="profile-tg-folder" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">📁 تاريخ الانضمام للملف : <span id="profile-tg-folder-text" dir="ltr">-</span></div>"""
c = c.replace(tg_old, tg_new)

js_update = """
            // Funnel & Tab logic
            if(typeof setFunnelStep === 'function') {
                setFunnelStep('email-sent', student.email_sent_at || (student.email_sent ? 'نعم' : null));
                setFunnelStep('email-opened', student.email_opened_at);
                setFunnelStep('email-clicked', student.email_clicked_at || student.folder_clicked_at);
                setFunnelStep('whatsapp-sent', student.whatsapp_sent_at || (student.whatsapp_sent ? 'نعم' : null));
                setFunnelStep('bot-started', student.bot_started_at);
                setFunnelStep('group-joined', student.joined_at || (student.group_joined ? 'نعم' : null));
                switchModalTab('general');
            }

            // Translation dictionaries
            const trPays = {'france':'فرنسا', 'maroc':'المغرب', 'algerie':'الجزائر', 'algérie':'الجزائر', 'belgique':'بلجيكا', 'suisse':'سويسرا', 'canada':'كندا', 'tunisie':'تونس'};
            const trNat = {'marocaine':'مغربية', 'marocain':'مغربي', 'algerienne':'جزائرية', 'algérienne':'جزائرية', 'algerien':'جزائري', 'algérien':'جزائري', 'francaise':'فرنسية', 'française':'فرنسية', 'francais':'فرنسي', 'français':'فرنسي', 'tunisienne':'تونسية', 'tunisien':'تونسي'};
            const trAr = {'debutant':'مبتدئ', 'débutant':'مبتدئ', 'intermediaire':'متوسط', 'intermédiaire':'متوسط', 'moyen':'متوسط', 'avance':'متقدم', 'avancé':'متقدم'};

            function tr(val, dict) {
                if(!val) return '-';
                const v = String(val).toLowerCase().trim();
                return dict[v] || val;
            }

            const cEl = document.getElementById('profile-country-text');
            if(cEl) cEl.textContent = tr(student.country, trPays);
            const natEl = document.getElementById('profile-nationality-text');
            if(natEl) natEl.textContent = tr(student.nationality, trNat);
            const arEl = document.getElementById('profile-arabiclevel-text');
            if(arEl) arEl.textContent = tr(student.arabic_level, trAr);
            
            const slEl = document.getElementById('profile-school-level-text');
            if(slEl) slEl.textContent = student.school_level || '-';

            const tgFEl = document.getElementById('profile-tg-firstname-text');
            if(tgFEl) tgFEl.textContent = student.tg_first_name || '-';
            const tgLEl = document.getElementById('profile-tg-lastname-text');
            if(tgLEl) tgLEl.textContent = student.tg_last_name || '-';
            const tgFolder = document.getElementById('profile-tg-folder-text');
            if(tgFolder) tgFolder.textContent = student.folder_clicked_at ? student.folder_clicked_at.substring(0, 16).replace('T', ' ') : '-';
            
            const inscEl = document.getElementById('profile-inscription-text');
            if(inscEl) inscEl.textContent = student.created_at ? student.created_at.split(' ')[0] : '-';

            // Phone number fancy display
            const phoneEl = document.getElementById('profile-phone-text');
            if (phoneEl) {
                let p = String(student.phone || '').trim();
                if (p && p !== '-' && p !== 'null') {
                    if (p.startsWith('+')) {
                        let ind = p.substring(0, 4); // basic guess
                        let rest = p.substring(4);
                        if (p.startsWith('+212') || p.startsWith('+213') || p.startsWith('+216')) {
                            ind = p.substring(0, 4); rest = p.substring(4);
                        } else if (p.startsWith('+33') || p.startsWith('+32') || p.startsWith('+41')) {
                            ind = p.substring(0, 3); rest = p.substring(3);
                        }
                        phoneEl.innerHTML = `<span style="background:var(--bg); border:1px solid var(--border); border-radius:4px; padding:2px 6px; font-size:0.8rem; margin-right:5px; color:var(--text1);">${ind}</span> <span dir="ltr">${rest}</span>`;
                    } else {
                        phoneEl.innerHTML = `<span dir="ltr">${p}</span>`;
                    }
                } else {
                    phoneEl.textContent = '-';
                }
            }

            // Age Calculator
            let ageText = student.dob || '-';
            if (student.dob) {
                try {
                    let parts = student.dob.split(/[\\/\\-]/);
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
            const dobEl = document.getElementById('profile-dob-text');
            if(dobEl) dobEl.textContent = ageText;
"""

# Now we need to properly replace the old injection
# Let's locate the old injection block in the file and replace it.
import re
start_token = "// Funnel & Tab logic"
end_token = "if(dobEl) dobEl.textContent = ageText;"
if start_token in c and end_token in c:
    s_idx = c.find(start_token)
    e_idx = c.find(end_token) + len(end_token)
    c = c[:s_idx] + js_update.strip() + c[e_idx:]
else:
    print("WARNING: Could not find old injection block, inserting at the end of openStudentCard")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Frontend patched")
