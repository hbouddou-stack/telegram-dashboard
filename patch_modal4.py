import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

injection = """
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

            // Additional Info
            const cEl = document.getElementById('profile-country-text');
            if(cEl) cEl.textContent = student.country || '-';
            const natEl = document.getElementById('profile-nationality-text');
            if(natEl) natEl.textContent = student.nationality || '-';
            const arEl = document.getElementById('profile-arabiclevel-text');
            if(arEl) arEl.textContent = student.arabic_level || '-';

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

# We inject at the end of openStudentCard.
# Look for: `document.getElementById('logs-overlay').style.display = 'flex';`
target = "document.getElementById('logs-overlay').style.display = 'flex';"
if target in c:
    c = c.replace(target, injection + "\n            " + target)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Funnel and Age logic injected")
