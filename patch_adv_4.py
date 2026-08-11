import re

with open('main.py', 'r', encoding='utf-8') as f:
    py = f.read()

new_endpoint = '''
async def report_quiz_question(request):
    try:
        data = await request.json()
        question_id = data.get('question_id')
        report_type = data.get('type')
        details = data.get('details', '')
        
        # Here we could insert into the database or trigger a telegram message
        # For now we just print it. The DB logic for reports can be expanded later.
        print(f"REPORT RECEIVED: Q_ID={question_id}, TYPE={report_type}, DETAILS={details}")
        
        return web.json_response({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({"success": False, "error": str(e)}, status=500)

'''

if 'async def report_quiz_question' not in py:
    py = py.replace('async def get_student_quiz_questions(request):', new_endpoint + '\nasync def get_student_quiz_questions(request):')
    py = py.replace("app.router.add_post('/api/student/quiz/setup', get_student_quiz_questions)", "app.router.add_post('/api/student/quiz/setup', get_student_quiz_questions)\n    app.router.add_post('/api/student/quiz/report', report_quiz_question)")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(py)
print('main.py updated')
