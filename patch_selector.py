import io, re
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

search_input_pattern = r'<input class="search-box" type="text" id="search-input".*?>'
match = re.search(search_input_pattern, c)
if match and 'card-style-selector' not in c:
    selector_html = '''
        <div style="display:flex; justify-content:space-between; align-items:center; padding: 10px 15px; border-bottom: 1px solid var(--border);">
            <div style="font-weight: 800; color: var(--text1); font-size: 0.9rem;" id="students-count-display"></div>
            <select id="card-style-selector" onchange="changeCardStyle(this.value)" style="padding:4px 8px; border-radius:6px; border:1px solid var(--border); background:var(--bg); color:var(--text1); font-size:0.8rem; outline:none;">
                <option value="1">✨ النموذج 1 (كلاسيكي)</option>
                <option value="2">📋 النموذج 2 (حالة)</option>
                <option value="3">📱 النموذج 3 (مدمج)</option>
            </select>
        </div>
        <script>
            let currentCardStyle = localStorage.getItem('cardStyle') || '1';
            document.addEventListener("DOMContentLoaded", () => {
                const sel = document.getElementById('card-style-selector');
                if (sel) sel.value = currentCardStyle;
            });
            function changeCardStyle(style) {
                currentCardStyle = style;
                localStorage.setItem('cardStyle', style);
                filterStudents();
            }
        </script>'''
    
    old_count_pattern = r'<div id="students-count-display".*?</div>'
    c = re.sub(old_count_pattern, '', c)
    
    match = re.search(search_input_pattern, c)
    c = c[:match.end()] + selector_html + c[match.end():]
    
    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Injected Style Selector!')
