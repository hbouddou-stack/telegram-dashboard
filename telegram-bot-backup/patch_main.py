import sys

file_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('async def save_admin_thematics(request: web.Request):'):
        # Inject the new endpoint just before save_admin_thematics
        code = '''
async def get_node_questions(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        node_id = data.get('node_id')
        if not node_id:
            return web.json_response({"success": False, "error": "Missing node_id"}, status=400)
        
        from config import DATABASE_PATH
        import aiosqlite
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT id, question, subject, course_number, source FROM questions WHERE thematic_node_id = ?"
            async with db.execute(query, (node_id,)) as cursor:
                questions = [dict(r) for r in await cursor.fetchall()]
                
        return web.json_response({"success": True, "questions": questions})
    except Exception as e:
        import logging
        logging.getLogger('bot').error(f"Error in get_node_questions: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

'''
        new_lines.append(code)
    
    if line.strip() == "app.router.add_post('/admin/thematics/save', save_admin_thematics)":
        new_lines.append("    app.router.add_post('/admin/thematics/node_questions', get_node_questions)\n")
        
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Patched main.py successfully.')
