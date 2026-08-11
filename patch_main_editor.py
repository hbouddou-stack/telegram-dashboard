import re

with open('telegram-bot-backup/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

handler_injection = """
async def handle_editor(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'editor.html'))
"""

if "def handle_editor" not in content:
    content = content.replace("async def handle_admin(request):", handler_injection + "\nasync def handle_admin(request):")

route_injection = """
    app.router.add_get('/editor', handle_editor)
    app.router.add_get('/editor.html', handle_editor)
"""

if "app.router.add_get('/editor'" not in content:
    content = content.replace("app.router.add_get('/admin', handle_admin)", route_injection + "    app.router.add_get('/admin', handle_admin)")

with open('telegram-bot-backup/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("main.py patched with /editor route.")
