import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add currentViewMode and currentSort state to Javascript
if "let currentViewMode" not in c:
    state_injection = """            let currentCardStyle = localStorage.getItem('cardStyle') || '1';
            let currentViewMode = localStorage.getItem('viewMode') || 'grid';
            let currentSort = { key: 'date', order: 'desc' };
            
            function changeViewMode(mode) {
                currentViewMode = mode;
                localStorage.setItem('viewMode', mode);
                filterStudents();
            }
            
            function sortTable(key) {
                if(currentSort.key === key) {
                    currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSort.key = key;
                    currentSort.order = 'asc';
                }
                filterStudents();
            }
"""
    c = c.replace("let currentCardStyle = localStorage.getItem('cardStyle') || '1';", state_injection)
    
    # 2. Setup the DOM listener for the new view mode selector
    dom_loaded = """document.addEventListener("DOMContentLoaded", () => {
                const sel = document.getElementById('card-style-selector');
                if (sel) sel.value = currentCardStyle;
                const vSel = document.getElementById('view-mode-selector');
                if (vSel) vSel.value = currentViewMode;
            });"""
    c = re.sub(r'document\.addEventListener\("DOMContentLoaded", \(\) => \{.*?\}\);', dom_loaded, c, flags=re.DOTALL)

# 3. Add the UI selector for Grid vs Table
if "view-mode-selector" not in c:
    selector_injection = """<select id="card-style-selector" onchange="changeCardStyle(this.value)" style="padding:4px 8px; border-radius:6px; border:1px solid var(--border); background:var(--bg); color:var(--text1); font-size:0.8rem; outline:none;">
                <option value="1">✨ النموذج 1 (كلاسيكي)</option>
                <option value="2">📋 النموذج 2 (حالة)</option>
                <option value="3">📱 النموذج 3 (مدمج)</option>
            </select>
            <select id="view-mode-selector" onchange="changeViewMode(this.value)" style="padding:4px 8px; border-radius:6px; border:1px solid var(--border); background:var(--bg); color:var(--text1); font-size:0.8rem; outline:none; margin-right:10px;">
                <option value="grid">🗂️ بطاقات</option>
                <option value="table">📊 جدول</option>
            </select>"""
    c = re.sub(r'<select id="card-style-selector".*?</select>', selector_injection, c, flags=re.DOTALL)


# 4. Modify filterStudents to support sorting and table rendering
# We inject right after `return matchSearch && matchGender && matchLevel && matchStatus && matchColor;` and `});`

sort_and_table_logic = """
            }); // End of filtering

            // Sort filtered results
            filtered.sort((a, b) => {
                let valA, valB;
                if (currentSort.key === 'name') {
                    valA = (a.first_name || '').toLowerCase();
                    valB = (b.first_name || '').toLowerCase();
                } else if (currentSort.key === 'email') {
                    valA = (a.email || '').toLowerCase();
                    valB = (b.email || '').toLowerCase();
                } else if (currentSort.key === 'level') {
                    valA = String(a.year || '');
                    valB = String(b.year || '');
                } else if (currentSort.key === 'status') {
                    valA = a.telegram_id ? 1 : 0;
                    valB = b.telegram_id ? 1 : 0;
                } else {
                    // Default: date
                    valA = new Date(a.created_at || 0).getTime();
                    valB = new Date(b.created_at || 0).getTime();
                }
                
                if (valA < valB) return currentSort.order === 'asc' ? -1 : 1;
                if (valA > valB) return currentSort.order === 'asc' ? 1 : -1;
                return 0;
            });

"""
if "// Sort filtered results" not in c:
    c = c.replace("});\n\n            const linkedCount =", sort_and_table_logic + "            const linkedCount =")

# 5. Inject Table Rendering block
table_rendering_logic = """
            if (currentViewMode === 'table') {
                const table = document.createElement('table');
                table.style.width = '100%';
                table.style.borderCollapse = 'collapse';
                table.style.fontSize = '0.85rem';
                table.style.background = 'var(--surface)';
                table.style.borderRadius = '8px';
                table.style.overflow = 'hidden';
                table.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
                
                const thead = document.createElement('thead');
                thead.innerHTML = `
                    <tr style="background:rgba(10,132,255,0.1); border-bottom:2px solid var(--border); text-align:right;">
                        <th style="padding:12px; cursor:pointer;" onclick="sortTable('name')">الاسم ${currentSort.key==='name'?(currentSort.order==='asc'?'🔼':'🔽'):'↕️'}</th>
                        <th style="padding:12px; cursor:pointer;" onclick="sortTable('email')">الإيميل ${currentSort.key==='email'?(currentSort.order==='asc'?'🔼':'🔽'):'↕️'}</th>
                        <th style="padding:12px; cursor:pointer;" onclick="sortTable('status')">الحالة ${currentSort.key==='status'?(currentSort.order==='asc'?'🔼':'🔽'):'↕️'}</th>
                        <th style="padding:12px; cursor:pointer;" onclick="sortTable('level')">المستوى ${currentSort.key==='level'?(currentSort.order==='asc'?'🔼':'🔽'):'↕️'}</th>
                        <th style="padding:12px; cursor:pointer;" onclick="sortTable('date')">التاريخ ${currentSort.key==='date'?(currentSort.order==='asc'?'🔼':'🔽'):'↕️'}</th>
                    </tr>
                `;
                table.appendChild(thead);
                const tbody = document.createElement('tbody');
                
                const displayLimit = Math.min(filtered.length, 500);
                for(let i=0; i<displayLimit; i++) {
                    const s = filtered[i];
                    const tr = document.createElement('tr');
                    tr.style.borderBottom = '1px solid var(--border)';
                    tr.style.cursor = 'pointer';
                    tr.onmouseover = () => tr.style.background = 'var(--bg)';
                    tr.onmouseout = () => tr.style.background = 'transparent';
                    tr.onclick = () => openStudentCard(s);
                    
                    // Status dot
                    let dotColor, dotTitle;
                    if (s.excluded) { dotColor = '#111'; dotTitle = 'مستبعد'; }
                    else if (s.group_joined) { dotColor = '#16a34a'; dotTitle = 'منضم ✅'; }
                    else if (s.email_clicked_at || s.folder_clicked_at || s.bot_started_at) { dotColor = '#f97316'; dotTitle = 'في طور الانضمام'; }
                    else { dotColor = '#ef4444'; dotTitle = 'لم ينضم'; }
                    
                    const name = (s.first_name || '') + ' ' + (s.last_name || '');
                    const yrStr = String(s.year || '');
                    const yrMatch = yrStr.match(/\\d+/);
                    const yrNum = yrMatch ? yrMatch[0] : '';
                    
                    const d = new Date(s.created_at);
                    const dateStr = !isNaN(d) ? d.toLocaleDateString('fr-FR') : '-';
                    
                    tr.innerHTML = `
                        <td style="padding:12px;"><strong>${name}</strong></td>
                        <td style="padding:12px; direction:ltr; text-align:right;">${s.email || '-'}</td>
                        <td style="padding:12px;"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${dotColor};margin-left:5px;"></span>${dotTitle}</td>
                        <td style="padding:12px;">${yrNum ? 'السنة '+yrNum : '-'}</td>
                        <td style="padding:12px;">${dateStr}</td>
                    `;
                    tbody.appendChild(tr);
                }
                table.appendChild(tbody);
                list.appendChild(table);
                return; // skip the grid rendering
            }
"""

if "if (currentViewMode === 'table')" not in c:
    c = c.replace("const fragment = document.createDocumentFragment();", table_rendering_logic + "\n            const fragment = document.createDocumentFragment();")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Patch successful!")
