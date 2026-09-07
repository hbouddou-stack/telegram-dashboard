import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# ===========================================
# 1. Add Ghost tab to bottom navigation
# ===========================================
old_nav_end = '''        <div class="nav-item" onclick="switchTab('settings')">
            <span class="nav-icon">⚙️</span>
            <span>الإعدادات</span>
        </div>
    </div>'''
new_nav_end = '''        <div class="nav-item" onclick="switchTab('settings')">
            <span class="nav-icon">⚙️</span>
            <span>الإعدادات</span>
        </div>
        <div class="nav-item" onclick="switchTab('ghosts')" id="nav-ghosts">
            <span class="nav-icon">👻</span>
            <span>زوار</span>
        </div>
    </div>'''

if 'nav-ghosts' not in c:
    c = c.replace(old_nav_end, new_nav_end)
    print("Nav tab added")
else:
    print("Nav tab already there")

# ===========================================
# 2. Find where sections live and add ghost section
# ===========================================
# Find the logs section end so we can inject after it
section_target = "id=\"section-logs\""
m = re.search(r'<div[^>]*id="section-logs".*?(?=<div[^>]*id="section-|$)', c, re.DOTALL)
if m:
    print("Found section-logs, injecting after")
else:
    m = re.search(r'<div[^>]*id="section-settings"', c)
    if m:
        print("Found section-settings at:", m.start())

# Find where section-settings starts
settings_match = re.search(r'(<div[^>]*id="section-settings")', c)
if settings_match:
    inject_pos = settings_match.start()
    
    ghost_section = r'''<div id="section-ghosts" class="section" style="display:none; flex-direction:column; height:100%; overflow:hidden;">
        <!-- Header -->
        <div style="padding:15px 15px 10px; background:var(--surface); border-bottom:1px solid var(--border); flex-shrink:0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h2 style="margin:0; font-size:1.1rem; color:var(--text1);">👻 الزوار المجهولون</h2>
                    <p style="margin:4px 0 0; font-size:0.8rem; color:var(--text2);">مستخدمون بدأوا البوت لكنهم لم يربطوا حسابهم</p>
                </div>
                <button class="btn btn-primary" onclick="loadGhostVisitors()" style="padding:8px 15px; border-radius:8px; font-size:0.85rem;">
                    🔄 تحديث
                </button>
            </div>
            <!-- Count badge -->
            <div id="ghost-count-badge" style="margin-top:10px; display:none;">
                <span id="ghost-count-text" style="background:rgba(239,68,68,0.15); color:#ef4444; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight:bold;"></span>
            </div>
        </div>
        
        <!-- List -->
        <div id="ghost-list" style="flex:1; overflow-y:auto; padding:10px;">
            <div style="text-align:center; padding:40px; color:var(--text2);">
                <div style="font-size:3rem; margin-bottom:10px;">👻</div>
                <div>اضغط على "تحديث" لتحميل القائمة</div>
            </div>
        </div>
    </div>

    '''
    c = c[:inject_pos] + ghost_section + c[inject_pos:]
    print("Ghost section injected before settings")

# ===========================================
# 3. Add JS function for ghost visitors
# ===========================================
ghost_js = r'''
        // =================== GHOST VISITORS ===================
        async function loadGhostVisitors() {
            const list = document.getElementById('ghost-list');
            if(!list) return;
            list.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text2);">⏳ جاري التحميل...</div>';
            
            try {
                const res = await fetch('/api/admin/gateway/ghost_visitors');
                const data = await res.json();
                
                if(!data.success) {
                    list.innerHTML = '<div style="color:red; text-align:center; padding:20px;">❌ ' + data.error + '</div>';
                    return;
                }
                
                const visitors = data.visitors;
                const badge = document.getElementById('ghost-count-badge');
                const badgeText = document.getElementById('ghost-count-text');
                if(badge && badgeText) {
                    badge.style.display = 'block';
                    badgeText.textContent = visitors.length + ' زائر مجهول';
                }
                
                if(visitors.length === 0) {
                    list.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text2);"><div style="font-size:3rem;">🎉</div><div style="margin-top:10px;">لا يوجد زوار مجهولون! جميع المستخدمين مرتبطون.</div></div>';
                    return;
                }
                
                list.innerHTML = '';
                visitors.forEach(v => {
                    const card = document.createElement('div');
                    card.style.cssText = 'background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:14px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;';
                    
                    let dateStr = v.created_at || '';
                    try {
                        dateStr = new Date(v.created_at + 'Z').toLocaleDateString();
                    } catch(e){}
                    
                    const name = [v.first_name, v.last_name].filter(Boolean).join(' ') || 'مجهول';
                    const username = v.username ? '@' + v.username : '';
                    
                    card.innerHTML = `
                        <div style="display:flex; align-items:center; gap:12px;">
                            <div style="width:42px; height:42px; border-radius:50%; background:rgba(239,68,68,0.1); display:flex; align-items:center; justify-content:center; font-size:1.3rem; flex-shrink:0;">👻</div>
                            <div>
                                <div style="font-weight:bold; color:var(--text1); font-size:0.95rem;">${name}</div>
                                <div style="font-size:0.8rem; color:#0a84ff;">${username}</div>
                                <div style="font-size:0.75rem; color:var(--text2); margin-top:2px;">🆔 ${v.telegram_id} · 📅 ${dateStr}</div>
                            </div>
                        </div>
                        <a href="https://t.me/${v.username || v.telegram_id}" target="_blank" 
                           style="background:rgba(10,132,255,0.1); color:#0a84ff; padding:6px 12px; border-radius:8px; text-decoration:none; font-size:0.8rem; white-space:nowrap;">
                            ✉️ تواصل
                        </a>
                    `;
                    list.appendChild(card);
                });
            } catch(e) {
                list.innerHTML = '<div style="color:red; text-align:center; padding:20px;">❌ خطأ في الاتصال</div>';
                console.error(e);
            }
        }
        // =================== END GHOST VISITORS ===================

'''

# Inject before switchTab function
target_fn = 'function switchTab('
if 'loadGhostVisitors' not in c:
    c = c.replace(target_fn, ghost_js + '        ' + target_fn)
    print("Ghost JS injected")

# ===========================================
# 4. Make switchTab handle 'ghosts'
# ===========================================
# Find the switchTab function and check if it handles ghosts
switch_match = re.search(r'function switchTab\(tab\) \{.*?(?=\n\s*function |\n\s*async function )', c, re.DOTALL)
if switch_match:
    switch_body = switch_match.group(0)
    if "'ghosts'" not in switch_body and '"ghosts"' not in switch_body:
        # Find where sections list is and add ghosts
        c = c.replace(
            "const sections = ['overview', 'students', 'sos', 'actions', 'logs', 'settings']",
            "const sections = ['overview', 'students', 'sos', 'actions', 'logs', 'settings', 'ghosts']"
        )
        print("switchTab sections updated")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("Frontend ghost section done")
