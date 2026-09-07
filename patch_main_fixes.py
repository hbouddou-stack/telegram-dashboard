import io
with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()
    
# Find add_crm_note
old = r'''async def api_admin_gateway_add_crm_note(request: web.Request):
    data = await request.json()
    student_id = data.get('student_id') or 0
    tid = data.get('telegram_id')
    ctype = data.get('type', 'AUTRE')
    tag = data.get('tag', 'INFO')
    note = data.get('note', '')
    
    if not note:
        return web.json_response({'success': False, 'error': 'Note is empty'})
        
    description = f"[{ctype}] [{tag}] {note}"'''
new = r'''async def api_admin_gateway_add_crm_note(request: web.Request):
    data = await request.json()
    student_id = data.get('student_id') or 0
    tid = data.get('telegram_id')
    ctype = data.get('type', 'AUTRE')
    tag = data.get('tag', 'INFO')
    note = data.get('note', '')
    admin_name = data.get('admin_name', 'Admin')
    
    if not note:
        return web.json_response({'success': False, 'error': 'Note is empty'})
        
    description = f"[{ctype}] [{tag}] [بواسطة: {admin_name}] {note}"'''
c = c.replace(old, new)

# And inject crm_tickets into api_admin_gateway_student_timeline
old_timeline = r'''async with db.execute("SELECT id, message, status, timestamp FROM gateway_sos WHERE telegram_id = ? OR student_id = ? ORDER BY id DESC", (tid, student_id)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'gateway_sos'
                        timeline.append(r)'''
new_timeline = r'''async with db.execute("SELECT id, message, status, timestamp FROM gateway_sos WHERE telegram_id = ? OR student_id = ? ORDER BY id DESC", (tid, student_id)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'gateway_sos'
                        timeline.append(r)
                async with db.execute("SELECT id, message, status, timestamp, theme FROM crm_tickets WHERE telegram_id = ? ORDER BY id DESC", (tid,)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'crm_tickets'
                        timeline.append(r)'''
c = c.replace(old_timeline, new_timeline)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Main patched')
