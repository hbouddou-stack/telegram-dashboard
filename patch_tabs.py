import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Navbar renaming
old_links_nav = '''<div class="nav-item" onclick="switchTab('links')">
            <span style="font-size: 1.2rem;">🔗</span>
            <span>الروابط</span>
        </div>'''
new_actions_nav = '''<div class="nav-item" onclick="switchTab('actions')">
            <span style="font-size: 1.2rem;">🚀</span>
            <span>إجراءات</span>
        </div>'''
if old_links_nav in c:
    c = c.replace(old_links_nav, new_actions_nav)
else:
    c = re.sub(r'<div class="nav-item" onclick="switchTab\(\'links\'\)">.*?</div>', new_actions_nav, c, flags=re.DOTALL)


# 2. Extract tab-links content
tab_links_pattern = r'<!-- TAB: Liens Groupes -->\s*<div id="tab-links" class="tab-content">.*?</div>\n'
match = re.search(tab_links_pattern, c, re.DOTALL)
if match:
    tab_links_html = match.group(0)
    
    # 3. Create tab-actions and tab-overview
    tab_actions_and_overview = '''<!-- TAB: Accueil / Stats -->
    <div id="tab-overview" class="tab-content">
        <div style="padding:20px; text-align:center; background:var(--surface); border-radius:12px; border:1px solid var(--border); margin-bottom:20px;">
            <h2 style="color:var(--text1); margin-bottom:10px;">📊 نظرة عامة وإحصائيات</h2>
            <p style="color:var(--text2); line-height:1.6;">جاري بناء لوحة الإحصائيات (Statistiques et Tableau de Bord). قريباً ستجد هنا ملخصاً لنسبة التحويل والتفاعل في الأكاديمية.</p>
        </div>
    </div>

    <!-- TAB: Actions (Vide pour l'instant) -->
    <div id="tab-actions" class="tab-content">
        <div style="padding:40px; text-align:center; color:var(--text2);">
            <div style="font-size:3rem; margin-bottom:10px;">🚀</div>
            <h3>قسم الإجراءات</h3>
            <p>هذا القسم مخصص للعمليات الجماعية (قيد التطوير)</p>
        </div>
    </div>
    '''
    
    # Replace tab-links with the new tabs
    c = c.replace(tab_links_html, tab_actions_and_overview)
    
    # Inner links content
    inner_links = tab_links_html.replace('<!-- TAB: Liens Groupes -->', '').replace('<div id="tab-links" class="tab-content">', '').strip()
    inner_links = inner_links[:-6] # remove last </div>
    
    settings_section = f'''
        <hr style="border-color:var(--border); margin:20px 0;">
        <h3 style="font-size: 1.1rem; margin-bottom: 15px; color:var(--text1);">🔗 إدارة روابط المجموعات (Liens)</h3>
        {inner_links}
    </div>
    <script>'''
    
    # tab-settings is the last tab before `<script>`
    # so we replace `</div>\n    <script>` (the closing of tab-settings) with the new section
    c = re.sub(r'</div>\s*<script>', settings_section, c)

else:
    print("tab-links not found!")


with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('Patch applied successfully')
