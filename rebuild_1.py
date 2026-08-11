import re

with open('main.py', 'r', encoding='utf-8') as f:
    main_py = f.read()

# Add report endpoint
report_route = '''
@app.post("/api/student/quiz/report")
async def report_quiz_error(request: Request):
    """Handle student reports for quiz errors."""
    try:
        data = await request.json()
        report_type = data.get("type")
        details = data.get("details", "")
        question_id = data.get("questionId")
        
        # In a real scenario, save this to DB.
        print(f"REPORT RECEIVED - Type: {report_type}, QuestionID: {question_id}, Details: {details}")
        
        return JSONResponse({"success": True})
    except Exception as e:
        print(f"Error handling quiz report: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
'''

if "/api/student/quiz/report" not in main_py:
    # insert before @app.post("/api/student/quiz/setup")
    main_py = main_py.replace('@app.post("/api/student/quiz/setup")', report_route + '\n@app.post("/api/student/quiz/setup")')
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(main_py)
        print("main.py updated")
