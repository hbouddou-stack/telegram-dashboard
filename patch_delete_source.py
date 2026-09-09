import re
import io

# 1. Update Backend (main.py)
with io.open('main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

# Add endpoint function
delete_source_func = """
async def api_admin_gateway_delete_source(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        source_file = data.get('source_file')
        if not source_file:
            return web.json_response({"success": False, "error": "No source_file provided"})
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("DELETE FROM academy_students WHERE source_file = ?", (source_file,)) as cur:
                deleted = cur.rowcount
            await db.commit()
            
        return web.json_response({"success": True, "deleted": deleted})
    except Exception as e:
        import logging
        logging.getLogger('main').error(f"Error in delete_source: {e}", exc_info=True)
        return web.json_response({"success": False, "error": str(e)})

"""

if 'api_admin_gateway_delete_source' not in main_code:
    # Insert function before api_admin_gateway_students
    main_code = main_code.replace('async def api_admin_gateway_students', delete_source_func + 'async def api_admin_gateway_students')

if '/api/admin/gateway/delete_source' not in main_code:
    # Register route
    main_code = main_code.replace(
        "app.router.add_get('/api/admin/gateway/students', api_admin_gateway_students)",
        "app.router.add_get('/api/admin/gateway/students', api_admin_gateway_students)\n    app.router.add_post('/api/admin/gateway/delete_source', api_admin_gateway_delete_source)"
    )

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)
print("Backend updated with delete_source endpoint.")

# 2. Update Frontend (admin_gateway.html)
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the source select with a container holding select + delete button
old_source_select = """<select id="source-select" onchange="setSourceFilter(this.value)" style="flex:1; padding:8px 6px; background:var(--bg); border:1px solid var(--border); border-radius:12px; color:var(--text1); font-family:'Tajawal'; outline:none; font-size:0.75rem; cursor:pointer; font-weight:700;">
                    <option value="all">📁 كل المصادر</option>
                    <option value="excel">📗 Excel</option>
                    <option value="sheet">📊 Sheet</option>
                    <option value="manuel">✍️ يدوي</option>
                </select>"""

new_source_html = """<div style="flex:1; display:flex; gap:4px;">
                    <select id="source-select" onchange="setSourceFilter(this.value)" style="flex:1; padding:8px 6px; background:var(--bg); border:1px solid var(--border); border-radius:12px; color:var(--text1); font-family:'Tajawal'; outline:none; font-size:0.75rem; cursor:pointer; font-weight:700;">
                        <option value="all">📁 كل المصادر</option>
                        <option value="excel">📗 Excel (الكل)</option>
                        <option value="sheet">📊 Sheet</option>
                        <option value="manuel">✍️ يدوي</option>
                    </select>
                    <button id="btn-delete-source" onclick="deleteSelectedSource()" style="display:none; background:#ef4444; color:white; border:none; border-radius:12px; padding:4px 8px; cursor:pointer;" title="حذف هذا الملف (Supprimer ce fichier)">🗑️</button>
                </div>"""

if "btn-delete-source" not in html:
    html = html.replace(old_source_select, new_source_html)

# Add logic to populate dynamic source files in fetchStudents
fetch_injection = """
        if (data && data.success) {
            allStudents = data.data;
            
            // Build dynamic Excel files dropdown
            const sourceSelect = document.getElementById('source-select');
            const currentVal = sourceSelect.value;
            // Keep base options
            let opts = `<option value="all">📁 كل المصادر</option>
                        <option value="excel">📗 Excel (الكل)</option>
                        <option value="sheet">📊 Sheet</option>
                        <option value="manuel">✍️ يدوي</option>`;
            
            // Extract unique filenames
            const excelFiles = [...new Set(allStudents.filter(s => s.source === 'excel' && s.source_file).map(s => s.source_file))];
            excelFiles.forEach(f => {
                opts += `<option value="file:${f}">📄 ${f}</option>`;
            });
            sourceSelect.innerHTML = opts;
            if (opts.includes(`value="${currentVal}"`)) sourceSelect.value = currentVal;
"""
html = re.sub(
    r'if\s*\(\s*data\s*&&\s*data\.success\s*\)\s*\{\s*allStudents\s*=\s*data\.data;',
    fetch_injection,
    html,
    count=1
)

# Update setSourceFilter in SECOND script to show/hide delete button
old_set_source = """        function setSourceFilter(val) {
            filters.source = val;
            filterStudents();
        }"""
new_set_source = """        function setSourceFilter(val) {
            filters.source = val;
            const delBtn = document.getElementById('btn-delete-source');
            if (val && val.startsWith('file:')) {
                delBtn.style.display = 'block';
            } else {
                delBtn.style.display = 'none';
            }
            filterStudents();
        }

        async function deleteSelectedSource() {
            const val = document.getElementById('source-select').value;
            if (!val.startsWith('file:')) return;
            const filename = val.replace('file:', '');
            
            if (!confirm(`⚠️ Attention !\nVous êtes sur le point de supprimer TOUS les étudiants importés depuis le fichier :\\n\\n📄 ${filename}\\n\\nCette action est irréversible. Continuer ?`)) return;
            
            try {
                const res = await fetch('/api/admin/gateway/delete_source', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source_file: filename })
                });
                const data = await res.json();
                if (data.success) {
                    alert(`✅ Fichier supprimé avec succès !\\n${data.deleted} étudiants ont été retirés.`);
                    document.getElementById('source-select').value = 'all';
                    setSourceFilter('all');
                    fetchStudents();
                } else {
                    alert('Erreur: ' + (data.error || 'Inconnue'));
                }
            } catch(e) {
                alert('Erreur réseau');
            }
        }"""
html = html.replace(old_set_source, new_set_source)

# Update filterStudents to support file: match
old_source_match = """                const matchSource = filters.source === 'all' || (s.source || 'inconnu').toLowerCase() === filters.source;"""
new_source_match = """                const matchSource = filters.source === 'all' 
                    || (filters.source.startsWith('file:') && s.source_file === filters.source.replace('file:', ''))
                    || (filters.source === 'excel' && (s.source || '').toLowerCase() === 'excel')
                    || (filters.source === 'sheet' && (s.source || '').toLowerCase() === 'sheet')
                    || (filters.source === 'manuel' && (s.source || '').toLowerCase() === 'manuel');"""
html = html.replace(old_source_match, new_source_match)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Frontend updated with dynamic source filter and delete button.")
