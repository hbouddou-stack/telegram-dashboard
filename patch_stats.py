import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

overview_html = '''<!-- TAB: Accueil / Stats -->
    <div id="tab-overview" class="tab-content">
        <!-- Filters for Stats -->
        <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:15px; margin-bottom:20px;">
            <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                <span style="color:var(--text2); font-weight:bold;">🔎 تصفية الإحصائيات (Filtres) :</span>
                <select id="stat-filter-year" onchange="renderDashboardStats()" style="padding:6px 12px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none;">
                    <option value="all">كل المستويات (Tous)</option>
                    <option value="1">المستوى الأول (1)</option>
                    <option value="2">المستوى الثاني (2)</option>
                    <option value="3">المستوى الثالث (3)</option>
                    <option value="4">المستوى الرابع (4)</option>
                </select>
                <select id="stat-filter-gender" onchange="renderDashboardStats()" style="padding:6px 12px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none;">
                    <option value="all">الكل (Tous)</option>
                    <option value="male">ذكور (Garçons)</option>
                    <option value="female">إناث (Filles)</option>
                </select>
            </div>
        </div>

        <!-- Global KPIs -->
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:15px; margin-bottom:20px;">
            <div style="background:linear-gradient(135deg, rgba(0,132,255,0.1), rgba(0,132,255,0.05)); border:1px solid #0084ff; border-radius:12px; padding:20px; text-align:center;">
                <div style="font-size:2rem; font-weight:800; color:#0084ff;" id="stat-kpi-total">0</div>
                <div style="color:var(--text1); font-weight:600; margin-top:5px;">إجمالي المسجلين<br><span style="font-size:0.8rem; color:var(--text2);">(Total Inscrits)</span></div>
            </div>
            <div style="background:linear-gradient(135deg, rgba(34,197,94,0.1), rgba(34,197,94,0.05)); border:1px solid #22c55e; border-radius:12px; padding:20px; text-align:center;">
                <div style="font-size:2rem; font-weight:800; color:#22c55e;" id="stat-kpi-joined">0</div>
                <div style="color:var(--text1); font-weight:600; margin-top:5px;">تم الربط والدخول<br><span style="font-size:0.8rem; color:var(--text2);">(Ont rejoint)</span></div>
            </div>
            <div style="background:linear-gradient(135deg, rgba(239,68,68,0.1), rgba(239,68,68,0.05)); border:1px solid #ef4444; border-radius:12px; padding:20px; text-align:center;">
                <div style="font-size:2rem; font-weight:800; color:#ef4444;" id="stat-kpi-pending">0</div>
                <div style="color:var(--text1); font-weight:600; margin-top:5px;">في الانتظار<br><span style="font-size:0.8rem; color:var(--text2);">(N'ont pas rejoint)</span></div>
            </div>
        </div>

        <!-- Funnel Details (Toggleable) -->
        <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:15px;">
            <div style="display:flex; justify-content:space-between; align-items:center; cursor:pointer;" onclick="toggleFunnelStats()">
                <h3 style="color:var(--text1); margin:0;">📊 تفاصيل مسار التحويل (Entonnoir)</h3>
                <span id="funnel-stats-arrow" style="color:var(--text2); transition:transform 0.3s;">▼</span>
            </div>
            <div id="funnel-stats-container" style="display:none; margin-top:20px; border-top:1px solid var(--border); padding-top:20px;">
                <!-- Funnel Steps -->
                <div style="display:flex; flex-direction:column; gap:12px;">
                    
                    <div style="display:flex; align-items:center; justify-content:space-between; background:var(--bg); padding:10px 15px; border-radius:8px;">
                        <span style="color:var(--text1);">📧 تم إرسال الإيميل 1 (Email 1 envoyé)</span>
                        <span style="font-weight:bold; color:var(--accent2);" id="stat-funnel-e1">0</span>
                    </div>
                    
                    <div style="display:flex; align-items:center; justify-content:space-between; background:var(--bg); padding:10px 15px; border-radius:8px;">
                        <span style="color:var(--text1);">📧 تم إرسال الإيميل 2 (Email 2 envoyé)</span>
                        <span style="font-weight:bold; color:var(--accent2);" id="stat-funnel-e2">0</span>
                    </div>

                    <div style="display:flex; align-items:center; justify-content:space-between; background:var(--bg); padding:10px 15px; border-radius:8px;">
                        <span style="color:var(--text1);">💬 رسالة واتساب 1 (WA 1 envoyé)</span>
                        <span style="font-weight:bold; color:#10b981;" id="stat-funnel-w1">0</span>
                    </div>

                    <div style="display:flex; align-items:center; justify-content:space-between; background:var(--bg); padding:10px 15px; border-radius:8px;">
                        <span style="color:var(--text1);">💬 رسالة واتساب 2 (WA 2 envoyé)</span>
                        <span style="font-weight:bold; color:#10b981;" id="stat-funnel-w2">0</span>
                    </div>

                    <div style="display:flex; align-items:center; justify-content:space-between; background:var(--bg); padding:10px 15px; border-radius:8px; border-right:4px solid #0084ff;">
                        <span style="color:var(--text1);">📁 نقر على زر فتح المنصة (Folder Clicked)</span>
                        <span style="font-weight:bold; color:#0084ff;" id="stat-funnel-folder">0</span>
                    </div>

                    <div style="display:flex; align-items:center; justify-content:space-between; background:var(--bg); padding:10px 15px; border-radius:8px; border-right:4px solid #22c55e;">
                        <span style="color:var(--text1);">✅ نجاح الربط (Liaison réussie)</span>
                        <span style="font-weight:bold; color:#22c55e;" id="stat-funnel-joined">0</span>
                    </div>
                </div>
            </div>
        </div>
    </div>'''

# Replace old tab-overview
pattern = r'<!-- TAB: Accueil / Stats -->\s*<div id="tab-overview" class="tab-content">.*?</div>\n    </div>'
if re.search(pattern, c, re.DOTALL):
    c = re.sub(pattern, overview_html, c, flags=re.DOTALL)
else:
    print("Could not find tab-overview pattern!")

js_code = '''
        function toggleFunnelStats() {
            const container = document.getElementById('funnel-stats-container');
            const arrow = document.getElementById('funnel-stats-arrow');
            if (container.style.display === 'none') {
                container.style.display = 'block';
                arrow.style.transform = 'rotate(180deg)';
            } else {
                container.style.display = 'none';
                arrow.style.transform = 'rotate(0deg)';
            }
        }

        function renderDashboardStats() {
            if (!allStudents || allStudents.length === 0) return;
            
            const yrFilter = document.getElementById('stat-filter-year').value;
            const genFilter = document.getElementById('stat-filter-gender').value;
            
            // Filter logic
            const filtered = allStudents.filter(s => {
                // Year match
                const yr = String(s.year || '').toLowerCase();
                let matchYr = yrFilter === 'all' 
                    || yr.includes(yrFilter)
                    || (yrFilter === '1' && (yr.includes('أول') || yr.includes('1')))
                    || (yrFilter === '2' && (yr.includes('ثاني') || yr.includes('2')))
                    || (yrFilter === '3' && (yr.includes('ثالث') || yr.includes('3')))
                    || (yrFilter === '4' && (yr.includes('رابع') || yr.includes('4')));
                
                // Gender match
                const g = String(s.gender || '').toLowerCase();
                const isM = g.startsWith('h') || g === 'm' || g === 'male' || g.includes('ذكر');
                const isF = g.startsWith('f') || g === 'female' || g === 'fille' || g.includes('أنثى');
                let matchGen = genFilter === 'all' 
                    || (genFilter === 'male' && isM)
                    || (genFilter === 'female' && isF);
                    
                return matchYr && matchGen;
            });
            
            // Calculate KPIs
            const total = filtered.length;
            const joined = filtered.filter(s => !!s.telegram_id).length;
            const pending = total - joined;
            
            document.getElementById('stat-kpi-total').textContent = total;
            document.getElementById('stat-kpi-joined').textContent = joined;
            document.getElementById('stat-kpi-pending').textContent = pending;
            
            // Calculate Funnel
            const e1 = filtered.filter(s => s.email_sent >= 1).length;
            const e2 = filtered.filter(s => s.email_sent >= 2).length;
            const w1 = filtered.filter(s => s.whatsapp_sent >= 1).length;
            const w2 = filtered.filter(s => s.whatsapp_sent >= 2).length;
            const folder = filtered.filter(s => !!s.folder_clicked_at).length;
            
            document.getElementById('stat-funnel-e1').textContent = e1;
            document.getElementById('stat-funnel-e2').textContent = e2;
            document.getElementById('stat-funnel-w1').textContent = w1;
            document.getElementById('stat-funnel-w2').textContent = w2;
            document.getElementById('stat-funnel-folder').textContent = folder;
            document.getElementById('stat-funnel-joined').textContent = joined; // same as joined
        }
'''

# Insert js_code before loadStudents() or anywhere in scripts
if 'function toggleFunnelStats()' not in c:
    c = c.replace('function loadStudents() {', js_code + '\n        function loadStudents() {')

# Hook renderDashboardStats into loadStudents success
hook = '''allStudents = data.students || [];
                renderStudents();'''
new_hook = '''allStudents = data.students || [];
                renderStudents();
                renderDashboardStats();'''
c = c.replace(hook, new_hook)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Patched Dashboard Stats!")
