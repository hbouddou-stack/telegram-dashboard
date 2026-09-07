import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

log_css = '''
<style>
.log-card {
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
    line-height: 1.5;
}
.log-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8rem;
    margin-bottom: 5px;
}
.log-card-title {
    font-weight: 800;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 6px;
}
.log-card-time {
    color: var(--text2);
    font-family: monospace;
}
.log-card-desc {
    color: var(--text1);
    font-size: 0.9rem;
    font-weight: 500;
}
.log-card-user {
    margin-top: 8px;
    font-size: 0.8rem;
    color: var(--text2);
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    background: rgba(0,0,0,0.05);
    padding: 6px;
    border-radius: 6px;
}
.log-badge {
    color: white;
    padding: 2px 6px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: bold;
    margin-right: 5px;
}
</style>
'''

if '.log-card' not in c:
    c = c.replace('</head>', log_css + '\n</head>')

js_log_functions = '''
        const LOG_RULES = {
            'AUTH_FAILED': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '❌', label: 'فشل تسجيل الدخول' },
            'LINK_FAILED': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '❌', label: 'فشل الربط' },
            'SOS_SUBMITTED': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '🆘', label: 'طلب مساعدة (SOS)' },
            'MANUAL_UNLINK': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '💔', label: 'إلغاء الربط اليدوي' },
            'NAME_VIOLATION_DETECTED': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '🚩', label: 'اسم غير مسموح' },

            'AUTH_SUCCESS': { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '✅', label: 'تسجيل دخول ناجح' },
            'LINK_SUCCESS': { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '🔗', label: 'تم ربط الحساب بنجاح' },
            'ACCOUNT_LINKED': { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '🔗', label: 'تم ربط الحساب' },
            'LINK_SUCCESS_APPROVED': { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '🔗', label: 'تم اعتماد الربط' },
            'JOIN_GROUP_CLICK': { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '🎓', label: 'دخول المجموعة' },
            
            'APP_OPENED': { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '📱', label: 'فتح التطبيق' },
            'APP_OPENED_UNLINKED': { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '📱', label: 'فتح التطبيق (غير مربوط)' },
            'FOLDER_CLICKED': { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '📁', label: 'فتح مجلد الدروس' },
            'QUIZ_STARTED': { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '📝', label: 'بدأ اختبار' },
            'TUTO_OPENED': { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '📖', label: 'فتح الشرح' },

            'EMAIL_SENT': { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.4)', text: '#d97706', icon: '📨', label: 'إرسال إيميل' },
            'WHATSAPP_SENT': { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.4)', text: '#d97706', icon: '💬', label: 'إرسال واتساب' },
            'MAGIC_LINK_GENERATED': { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.4)', text: '#d97706', icon: '⚙️', label: 'توليد رابط' },
            'DEFAULT': { bg: 'var(--surface)', border: 'var(--border)', text: 'var(--text1)', icon: '📌', label: 'نشاط' }
        };

        function getLogStyle(action_type) {
            let r = LOG_RULES[action_type];
            if (r) return r;
            if (action_type.includes('SUCCESS') || action_type.includes('JOIN')) return { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '✅', label: action_type };
            if (action_type.includes('FAIL') || action_type.includes('UNLINK') || action_type.includes('SOS')) return { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '❌', label: action_type };
            if (action_type.includes('OPEN') || action_type.includes('CLICK')) return { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '🖱️', label: action_type };
            if (action_type.includes('SENT')) return { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.4)', text: '#d97706', icon: '📤', label: action_type };
            return LOG_RULES['DEFAULT'];
        }
        
        function colorizeDescription(desc) {
            if (!desc) return '';
            let colored = desc.replace(/\\b(\\d{6})\\b/g, '<span style="color:#ff9f0a; font-family:monospace; font-weight:800; padding:2px 4px; background:rgba(255,159,10,0.15); border-radius:4px; letter-spacing:1px;">$1</span>');
            colored = colored.replace(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\\.[a-zA-Z0-9._-]+)/gi, '<span style="color:#0a84ff; font-family:monospace; font-weight:700; padding:2px 4px; background:rgba(10,132,255,0.15); border-radius:4px;">$1</span>');
            return colored;
        }

        function renderLogCard(l, showUserInfo = false) {
            const style = getLogStyle(l.action_type);
            let desc = colorizeDescription(l.description || '');
            
            let countBadge = l.count && l.count > 1 ? `<span class="log-badge" style="background:${style.text};">x${l.count}</span>` : '';
            
            let userInfo = '';
            if (showUserInfo) {
                let tgUname = l.telegram_username || l.tg_username || '';
                let unameSpan = tgUname ? ` <span dir="ltr" style="color:#0a84ff;">(@${tgUname})</span>` : '';
                let tgDisplay = l.telegram_name || '';
                if (!tgDisplay && l.tg_first_name) {
                    tgDisplay = l.tg_first_name + (l.tg_last_name ? ' ' + l.tg_last_name : '');
                }
                
                userInfo = `
                <div class="log-card-user">
                    ${l.first_name ? `<span>👤 <strong>${l.first_name} ${l.last_name||''}</strong></span>` : ''}
                    ${tgDisplay ? `<span>📱 <strong>${tgDisplay}</strong>${unameSpan}</span>` : ''}
                    ${l.telegram_id ? `<span style="font-family:monospace;">ID: ${l.telegram_id}</span>` : ''}
                </div>`;
            }

            return `
            <div class="log-card" style="background:${style.bg}; border:1px solid ${style.border}; border-left:4px solid ${style.text};">
                <div class="log-card-header">
                    <div class="log-card-title" style="color:${style.text};">
                        ${style.icon} ${style.label} ${countBadge}
                    </div>
                    <div class="log-card-time" dir="ltr">${formatDateArabic(l.timestamp)}</div>
                </div>
                <div class="log-card-desc">${desc}</div>
                ${userInfo}
            </div>
            `;
        }
        
        function groupLogs(logsArr) {
            let grouped = [];
            logsArr.forEach(l => {
                if (grouped.length > 0) {
                    let prev = grouped[grouped.length-1];
                    // Si même action, même description et même user, on groupe
                    if (prev.action_type === l.action_type && prev.description === l.description && prev.student_id === l.student_id && prev.telegram_id === l.telegram_id) {
                        prev.count = (prev.count || 1) + 1;
                        return;
                    }
                }
                l.count = 1;
                grouped.push(l);
            });
            return grouped;
        }
'''

if 'LOG_RULES' not in c:
    c = c.replace('// ============ DATE FORMATTER IN ARABIC ============', js_log_functions + '\n        // ============ DATE FORMATTER IN ARABIC ============')


# Update student modal logs
student_logs_old = '''let timelineHTML = '<div style="position:relative; border-right: 2px solid var(--border); padding-right:15px; margin-right:5px; margin-top:10px;">';
                    timelineHTML += data.logs.map(l => {
                        let color = 'var(--warning)';
                        if (l.action_type === 'LINK_FAILED') color = 'var(--danger)';
                        else if (l.action_type === 'LINK_SUCCESS' || l.action_type === 'ACCOUNT_LINKED' || l.action_type === 'JOIN_GROUP_CLICK') color = 'var(--success)';
                        else if (l.action_type === 'APP_OPENED' || l.action_type === 'APP_OPENED_UNLINKED') color = '#0a84ff';
                        
                        let uNameStr = l.telegram_username ? `<span dir="ltr" style="color:#0a84ff; font-weight:normal; margin-right:5px;">(@${l.telegram_username})</span>` : '';
                        let tgNameStr = l.telegram_name ? `<span style="font-size:0.75rem; color:var(--text2); display:block;">🗣️: ${l.telegram_name} ${uNameStr}</span>` : '';

                        return `
                        <div style="position:relative; margin-bottom:15px;">
                            <div style="position:absolute; right:-21px; top:4px; width:10px; height:10px; border-radius:50%; background:${color}; border:2px solid var(--card-bg);"></div>
                            <div style="font-size:0.75rem; color:var(--text2); display:flex; justify-content:space-between;">
                                <span>${formatDateArabic(l.timestamp)}</span>
                                <span style="font-weight:700; color:${color}; margin-right:10px; font-size:0.7rem;">[${l.action_type}]</span>
                            </div>
                            <div style="color:var(--text1); font-size:0.85rem; margin-top:4px; line-height:1.4;">${l.description}</div>
                            ${tgNameStr}
                        </div>
                        `;
                    }).join('');
                    timelineHTML += '</div>';
                    document.getElementById('logs-body').innerHTML = timelineHTML;'''

# Some emojis or specific texts might differ in the existing file. Use Regex!
import re

c = re.sub(r'let timelineHTML = \'<div style="position:relative; border-right: 2px solid var\(--border\); padding-right:15px; margin-right:5px; margin-top:10px;">\';.*?document\.getElementById\(\'logs-body\'\)\.innerHTML = timelineHTML;', 
           '''let grouped = groupLogs(data.logs);
                    let html = grouped.map(l => renderLogCard(l, false)).join('');
                    document.getElementById('logs-body').innerHTML = html;''', 
           c, flags=re.DOTALL)


# Update Global Logs
global_logs_old = r'list\.innerHTML = filteredLogs\.map\(\(l\) => \{.*?\}\)\.join\(\'\'\);'
c = re.sub(global_logs_old, 
           '''
            let grouped = groupLogs(filteredLogs);
            list.innerHTML = grouped.map(l => renderLogCard(l, true)).join('');
           ''', 
           c, flags=re.DOTALL)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Patch log UI applied.")
