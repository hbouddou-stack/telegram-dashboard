import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update filter UI grid layout
html = html.replace('grid-template-columns: 1fr 1.2fr;', 'grid-template-columns: 1fr 1.2fr 1.2fr;')

source_html = """                <div>
                    <div class="filter-title">المصدر (Source)</div>
                    <select id="source-select" onchange="setSourceFilter(this.value)" style="width:100%; padding:9px 12px; background:var(--bg); border:1px solid var(--border); border-radius:10px; color:var(--text1); font-family:'Tajawal'; outline:none; font-size:0.82rem; cursor:pointer;">
                        <option value="all">كل المصادر</option>
                        <option value="sheet">📊 Sheet</option>
                        <option value="excel">📗 Excel</option>
                        <option value="manuel">✍️ يدوي (Manuel)</option>
                    </select>
                </div>
            </div>"""
            
html = html.replace('</select>\n                </div>\n            </div>', '</select>\n                </div>\n' + source_html)

# 2. Update Javascript filters object
if "source: 'all'" not in html:
    html = html.replace("status: 'all', color: 'all'", "status: 'all', color: 'all', source: 'all'")

# 3. Add setSourceFilter function
if "function setSourceFilter" not in html:
    func_html = """function setStatusFilter(s) {
            filters.status = s;
            filterStudents();
        }
        function setSourceFilter(s) {
            filters.source = s;
            filterStudents();
        }"""
    html = html.replace("""function setStatusFilter(s) {
            filters.status = s;
            filterStudents();
        }""", func_html)

# 4. Update filterStudents() logic
if "const matchSource =" not in html:
    src_logic = """
                const srcLower = String(s.source || '').toLowerCase();
                let derivedSource = 'manuel';
                if (srcLower.includes('sheet') || srcLower.includes('google')) derivedSource = 'sheet';
                else if (srcLower.includes('excel')) derivedSource = 'excel';
                
                const matchSource = filters.source === 'all'
                    || filters.source === derivedSource;
"""
    html = html.replace("const linked = !!s.telegram_id;", src_logic + "\n                const linked = !!s.telegram_id;")
    html = html.replace("return matchSearch && matchGender && matchLevel && matchStatus && matchColor;", "return matchSearch && matchGender && matchLevel && matchStatus && matchColor && matchSource;")
    
    # Wait, previously I changed it to include matchSource... Let me just replace the exact match!
    # Sometimes it might have been slightly different, so I'll use regex for the return.
    html = re.sub(r'return matchSearch.*?matchColor;', 'return matchSearch && matchGender && matchLevel && matchStatus && matchColor && matchSource;', html)


with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('UI Filters updated safely!')
