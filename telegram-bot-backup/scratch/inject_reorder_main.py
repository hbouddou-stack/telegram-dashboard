import sys

filepath = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\main.py'

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

reorder_function = '''
async def reorder_admin_thematics(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        source_node_id = data.get("source_node_id")
        target_node_id = data.get("target_node_id")
        level = data.get("level")
        
        from config import DATABASE_PATH
        import aiosqlite
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # 1. Obtenir les infos du target node pour connaitre le contexte (parent_id, program_id)
            async with db.execute("SELECT parent_id, program_id FROM thematic_nodes WHERE id = ?", (target_node_id,)) as cursor:
                target_row = await cursor.fetchone()
            if not target_row:
                return web.json_response({"success": False, "error": "Target node not found"})
                
            parent_id, program_id = target_row
            
            # 2. Obtenir tous les noeuds frères (siblings) ordonnés
            if parent_id is None:
                query = "SELECT id FROM thematic_nodes WHERE program_id = ? AND level = ? AND parent_id IS NULL ORDER BY order_index, title"
                params = (program_id, level)
            else:
                query = "SELECT id FROM thematic_nodes WHERE program_id = ? AND level = ? AND parent_id = ? ORDER BY order_index, title"
                params = (program_id, level, parent_id)
                
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
            sibling_ids = [row[0] for row in rows]
            
            # 3. Réorganiser la liste
            if source_node_id in sibling_ids and target_node_id in sibling_ids:
                sibling_ids.remove(source_node_id)
                target_index = sibling_ids.index(target_node_id)
                # Inserer le source juste avant le target
                sibling_ids.insert(target_index, source_node_id)
                
                # 4. Mettre à jour la base de données
                for idx, node_id in enumerate(sibling_ids):
                    await db.execute("UPDATE thematic_nodes SET order_index = ? WHERE id = ?", (idx, node_id))
                await db.commit()
                return web.json_response({"success": True})
            else:
                return web.json_response({"success": False, "error": "Nodes are not siblings"})
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({"success": False, "error": str(e)}, status=500)
'''

# Find the place to inject
inject_idx = -1
for i, line in enumerate(lines):
    if 'async def save_admin_thematics' in line:
        inject_idx = i
        break

if inject_idx != -1:
    lines.insert(inject_idx, reorder_function + '\n')

# Find route injection
for i, line in enumerate(lines):
    if "app.router.add_post('/admin/thematics/save', save_admin_thematics)" in line:
        lines.insert(i + 1, "    app.router.add_post('/admin/thematics/reorder', reorder_admin_thematics)\n")
        break

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Injected reorder_admin_thematics into main.py")
