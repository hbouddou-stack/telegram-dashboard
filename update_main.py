import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add get_student_quiz_options right before get_student_quiz_questions
options_func = '''
async def get_student_quiz_options(request):
    try:
        subject = request.query.get('subject')
        if not subject:
            return web.json_response({"success": False, "error": "Missing subject"}, status=400)
            
        import database as db
        
        lessons = await db.get_available_lessons(subject)
        themes = await db.get_available_themes(subject)
        years = []
        if subject.lower() == 'sira':
            years = await db.get_available_sira_years()
            
        return web.json_response({
            "success": True,
            "lessons": lessons,
            "themes": themes,
            "years": years
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({"success": False, "error": str(e)}, status=500)

'''

content = content.replace('async def get_student_quiz_questions(request):', options_func + 'async def get_student_quiz_questions(request):')

# Add route mapping for options
content = content.replace("app.router.add_post('/api/student/quiz/setup', get_student_quiz_questions)", "app.router.add_get('/api/student/quiz/options', get_student_quiz_options)\n    app.router.add_post('/api/student/quiz/setup', get_student_quiz_questions)")

# Modify get_student_quiz_questions logic
# First extract mode parameter
content = content.replace("source = data.get('source', 'all') # 'all', 'favorites', 'errors'", "source = data.get('source', 'all') # 'all', 'favorites', 'errors'\n        mode = data.get('mode', 'lessons')")

# Helper to inject logic into query builder
def replace_condition(query_block):
    new_logic = '''
                if mode == 'themes' and course_numbers:
                    theme_ids = course_numbers
                    placeholders = ",".join("?" for _ in theme_ids)
                    query_nodes = f"SELECT id FROM thematic_nodes WHERE id IN ({placeholders}) OR parent_id IN ({placeholders})"
                    params_nodes = list(theme_ids) + list(theme_ids)
                    async with db_conn.execute(query_nodes, params_nodes) as cursor:
                        nodes_rows = await cursor.fetchall()
                        node_ids = [r['id'] for r in nodes_rows]
                        
                    if node_ids:
                        node_placeholders = ",".join("?" for _ in node_ids)
                        query += f" AND q.thematic_node_id IN ({node_placeholders})"
                    else:
                        query += " AND 1=0" # No nodes found
                elif mode == 'years' and course_numbers:
                    placeholders = ",".join("?" for _ in course_numbers)
                    query += f" AND q.hijra_year IN ({placeholders})"
                    params.extend(course_numbers)
                elif course_numbers:
                    placeholders = ",".join("?" for _ in course_numbers)
                    query += f" AND q.course_number IN ({placeholders})"
                    params.extend(course_numbers)
'''
    old_logic = '''
                if course_numbers:
                    placeholders = ",".join("?" for _ in course_numbers)
                    query += f" AND q.course_number IN ({placeholders})"
                    params.extend(course_numbers)
'''
    old_logic_all = '''
                if course_numbers:
                    placeholders = ",".join("?" for _ in course_numbers)
                    query += f" AND course_number IN ({placeholders})"
                    params.extend(course_numbers)
'''
    new_logic_all = new_logic.replace('q.thematic_node_id', 'thematic_node_id').replace('q.hijra_year', 'hijra_year').replace('q.course_number', 'course_number')
    
    qb = query_block.replace(old_logic, new_logic)
    qb = qb.replace(old_logic_all, new_logic_all)
    return qb

content = replace_condition(content)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
