import io
import re

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update Students query to filter out excluded students
students_query_target = "FROM academy_students s"
if "WHERE s.excluded = 0" not in c[c.find(students_query_target):c.find(students_query_target)+100]:
    c = c.replace("FROM academy_students s\nLEFT JOIN users u", "FROM academy_students s\nLEFT JOIN users u ON u.telegram_id = s.telegram_id\nWHERE s.excluded = 0\n--")
    # Actually the join is already there:
    c = c.replace(
        "FROM academy_students s\nLEFT JOIN users u ON u.telegram_id = s.telegram_id\nORDER BY",
        "FROM academy_students s\nLEFT JOIN users u ON u.telegram_id = s.telegram_id\nWHERE s.excluded = 0 OR s.excluded IS NULL\nORDER BY"
    )

# 2. Update KPI query to filter out excluded students
# In api_admin_gateway_kpi
# Need to replace FROM academy_students with FROM academy_students WHERE excluded = 0 OR excluded IS NULL for count queries
c = re.sub(
    r'(SELECT COUNT\(\*\) FROM academy_students)\"',
    r'\1 WHERE excluded = 0 OR excluded IS NULL"',
    c
)
c = re.sub(
    r'(SELECT COUNT\(\*\) FROM academy_students WHERE) (telegram_id IS NOT NULL)',
    r'\1 (excluded = 0 OR excluded IS NULL) AND (\2)',
    c
)
c = re.sub(
    r'(SELECT COUNT\(\*\) FROM academy_students WHERE) (email_sent > 0)',
    r'\1 (excluded = 0 OR excluded IS NULL) AND (\2)',
    c
)
c = re.sub(
    r'(SELECT COUNT\(\*\) FROM academy_students WHERE) (whatsapp_sent > 0)',
    r'\1 (excluded = 0 OR excluded IS NULL) AND (\2)',
    c
)

# 3. Add new endpoint for archive
archive_api = """
async def api_admin_gateway_archive_student(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        student_id = data.get('student_id')
        reason = data.get('reason', 'Non specifie')
        admin_name = data.get('admin_name', 'Admin')
        
        if not student_id:
            return web.json_response({'success': False, 'error': 'ID etudiant manquant'})
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Check if student exists
            async with db.execute("SELECT first_name FROM academy_students WHERE student_id = ?", (student_id,)) as cur:
                if not await cur.fetchone():
                    return web.json_response({'success': False, 'error': 'Etudiant introuvable'})
            
            # Archive
            await db.execute("UPDATE academy_students SET excluded = 1 WHERE student_id = ?", (student_id,))
            
            # Add CRM Note
            note_text = f"[ARCHIVÉ] L'étudiant a été archivé/exclu.\\nRaison : {reason}"
            await db.execute(
                "INSERT INTO student_logs (student_id, action_type, description, telegram_name) VALUES (?, ?, ?, ?)",
                (student_id, "CRM_NOTE", f"[بواسطة: {admin_name}] [نوع: SYSTEM]\\n{note_text}", "Admin")
            )
            await db.commit()
            
        return web.json_response({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})

"""

if 'api_admin_gateway_archive_student' not in c:
    c = c.replace('async def api_admin_gateway_import_students', archive_api + '\nasync def api_admin_gateway_import_students')

    # Add Route
    route_target = "app.router.add_post('/api/admin/gateway/import_students'"
    new_route = "app.router.add_post('/api/admin/gateway/archive_student', api_admin_gateway_archive_student)\n    " + route_target
    c = c.replace(route_target, new_route)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Backend archive logic applied")
