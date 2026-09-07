import io
import re

# ============================================================
# BACKEND: Add ghost visitors API endpoint to main.py
# ============================================================
with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

ghost_api = '''
async def api_admin_gateway_ghost_visitors(request: web.Request):
    """Returns users who started the bot but are not linked to any student record"""
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT 
                    u.telegram_id,
                    u.first_name,
                    u.last_name,
                    u.username,
                    u.created_at
                FROM users u
                LEFT JOIN academy_students s ON s.telegram_id = u.telegram_id
                WHERE s.telegram_id IS NULL
                ORDER BY u.created_at DESC
                LIMIT 200
            """) as cur:
                rows = [dict(r) for r in await cur.fetchall()]
        return web.json_response({'success': True, 'visitors': rows, 'count': len(rows)})
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})

'''

# Inject before the existing timeline endpoint
target = 'async def api_admin_gateway_student_timeline(request: web.Request):'
if 'api_admin_gateway_ghost_visitors' not in c:
    c = c.replace(target, ghost_api + target)

# Add route
route_target = "app.router.add_get('/api/admin/gateway/student_timeline', api_admin_gateway_student_timeline)"
new_route = "app.router.add_get('/api/admin/gateway/ghost_visitors', api_admin_gateway_ghost_visitors)\n    " + route_target
if 'ghost_visitors' not in c:
    c = c.replace(route_target, new_route)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("Backend patched")
