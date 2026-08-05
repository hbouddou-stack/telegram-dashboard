import re

def patch_main():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update get_node_questions with CTE
    old_node_func = """async def get_node_questions(request: web.Request):
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
        return web.json_response({"success": False, "error": str(e)}, status=500)"""

    new_node_func = """async def get_node_questions(request: web.Request):
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
            query = \"\"\"
                WITH RECURSIVE node_tree(id) AS (
                    SELECT id FROM thematic_nodes WHERE id = ?
                    UNION ALL
                    SELECT t.id FROM thematic_nodes t
                    INNER JOIN node_tree nt ON t.parent_id = nt.id
                )
                SELECT id, question, subject, course_number, source 
                FROM questions 
                WHERE thematic_node_id IN node_tree
            \"\"\"
            async with db.execute(query, (node_id,)) as cursor:
                questions = [dict(r) for r in await cursor.fetchall()]
                
        return web.json_response({"success": True, "questions": questions})
    except Exception as e:
        import logging
        logging.getLogger('bot').error(f"Error in get_node_questions: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)"""

    if old_node_func in content:
        content = content.replace(old_node_func, new_node_func)
    else:
        print("Could not find get_node_questions function to patch.")

    # 2. Add toggle_node_visibility endpoint
    toggle_func = """
async def toggle_node_visibility(request: web.Request):
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
            async with db.execute("SELECT is_active FROM thematic_nodes WHERE id = ?", (node_id,)) as cur:
                row = await cur.fetchone()
                if not row:
                    return web.json_response({"success": False, "error": "Node not found"})
                new_status = 0 if row[0] == 1 else 1
            await db.execute("UPDATE thematic_nodes SET is_active = ? WHERE id = ?", (new_status, node_id))
            await db.commit()
            
        return web.json_response({"success": True, "is_active": new_status})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)
"""
    if "async def toggle_node_visibility" not in content:
        # insert before save_admin_thematics
        content = content.replace("async def save_admin_thematics", toggle_func + "\nasync def save_admin_thematics")
        # register endpoint
        router_add = "    app.router.add_post('/admin/curriculum/node-questions', get_node_questions)"
        new_router = router_add + "\n    app.router.add_post('/admin/curriculum/toggle-visibility', toggle_node_visibility)"
        content = content.replace(router_add, new_router)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched main.py")

if __name__ == "__main__":
    patch_main()
