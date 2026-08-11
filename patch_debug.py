import re

with open('telegram-bot-backup/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """async def handle_editor(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'editor.html'))"""

replacement = """async def handle_editor(request):
    print("============= handle_editor CALLED =============")
    f = os.path.join(DASHBOARD_DIR, 'editor.html')
    print(f"File path: {f}, exists: {os.path.exists(f)}")
    return web.FileResponse(f)"""

if "============= handle_editor CALLED =============" not in content:
    content = content.replace(target, replacement)

with open('telegram-bot-backup/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("main.py patched with debug print in handle_editor.")
