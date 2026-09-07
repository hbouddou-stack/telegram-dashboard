import io
import re

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Inject API functions before api_admin_gateway_logs
target_func = 'async def api_admin_gateway_logs(request: web.Request):'
new_funcs = '''async def api_admin_gateway_student_timeline(request: web.Request):
    student_id = request.query.get('id')
    tid = request.query.get('tid')
    import aiosqlite
    from config import DATABASE_PATH
    try:
        timeline = []
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            if tid and tid != 'null' and tid != 'undefined':
                async with db.execute("SELECT id, action_type, description, timestamp FROM student_logs WHERE telegram_id = ? OR student_id = ? ORDER BY id DESC LIMIT 100", (tid, student_id)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'student_logs'
                        timeline.append(r)
                async with db.execute("SELECT id, message, status, timestamp FROM gateway_sos WHERE telegram_id = ? OR student_id = ? ORDER BY id DESC", (tid, student_id)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'gateway_sos'
                        timeline.append(r)
            else:
                async with db.execute("SELECT id, action_type, description, timestamp FROM student_logs WHERE student_id = ? ORDER BY id DESC LIMIT 100", (student_id,)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'student_logs'
                        timeline.append(r)
                async with db.execute("SELECT id, message, status, timestamp FROM gateway_sos WHERE student_id = ? ORDER BY id DESC", (student_id,)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'gateway_sos'
                        timeline.append(r)
        
        timeline.sort(key=lambda x: x['timestamp'], reverse=True)
        return web.json_response({'success': True, 'timeline': timeline})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_add_crm_note(request: web.Request):
    data = await request.json()
    student_id = data.get('student_id') or 0
    tid = data.get('telegram_id')
    ctype = data.get('type', 'AUTRE')
    tag = data.get('tag', 'INFO')
    note = data.get('note', '')
    
    if not note:
        return web.json_response({'success': False, 'error': 'Note is empty'})
        
    description = f"[{ctype}] [{tag}] {note}"
    import database as db
    try:
        await db.log_student_action(student_id, "CRM_NOTE", description, telegram_id=tid)
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

'''

if 'api_admin_gateway_student_timeline' not in c:
    c = c.replace(target_func, new_funcs + target_func)

# 2. Inject Routes
route_target = "app.router.add_get('/api/admin/gateway/logs', api_admin_gateway_logs)"
new_routes = '''app.router.add_get('/api/admin/gateway/student_timeline', api_admin_gateway_student_timeline)
app.router.add_post('/api/admin/gateway/add_crm_note', api_admin_gateway_add_crm_note)
'''
if 'api_admin_gateway_student_timeline' not in c.split(route_target)[0] and 'api_admin_gateway_student_timeline' not in c.split(route_target)[-1]:
    c = c.replace(route_target, new_routes + route_target)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Backend CRM Patched")
