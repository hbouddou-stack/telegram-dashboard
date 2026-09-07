import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = "app.router.add_get('/api/admin/gateway/logs', api_admin_gateway_logs)"
new_routes = """app.router.add_get('/api/admin/gateway/student_timeline', api_admin_gateway_student_timeline)
    app.router.add_post('/api/admin/gateway/add_crm_note', api_admin_gateway_add_crm_note)
    """

if 'api_admin_gateway_student_timeline' not in c[c.find(target)-200:c.find(target)]:
    c = c.replace(target, new_routes + target)
    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Routes injected')
else:
    print('Routes already there')
