import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

bulk_endpoint = """
async def api_admin_gateway_bulk_action(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        action = data.get('action')
        student_ids = data.get('student_ids', [])
        subject = data.get('subject', '')
        message = data.get('message', '')
        
        if not student_ids:
            return web.json_response({"success": False, "error": "Aucun étudiant sélectionné"})
            
        import logging
        _log = logging.getLogger('main')
        _log.info(f"Bulk action '{action}' triggered for {len(student_ids)} students.")
        
        # Here we could loop and send emails or whatsapp
        # For now, just mark success to validate the UI workflow
        # A real implementation would push to a background queue or use aiocron
        
        # Example of updating stats if it was email:
        # if action == 'email':
        #    async with aiosqlite.connect(DATABASE_PATH) as db:
        #        for sid in student_ids:
        #            await db.execute("UPDATE academy_students SET email_sent = email_sent + 1 WHERE student_id = ?", (sid,))
        #        await db.commit()
                
        return web.json_response({"success": True, "count": len(student_ids)})
    except Exception as e:
        import logging
        logging.getLogger('main').error(f"Error in bulk_action: {e}")
        return web.json_response({"success": False, "error": str(e)})
"""

if 'api_admin_gateway_bulk_action' not in main_code:
    main_code = main_code.replace("async def api_admin_gateway_students", bulk_endpoint + "\nasync def api_admin_gateway_students")

if '/api/admin/gateway/bulk_action' not in main_code:
    main_code = main_code.replace(
        "app.router.add_get('/api/admin/gateway/students', api_admin_gateway_students)",
        "app.router.add_get('/api/admin/gateway/students', api_admin_gateway_students)\n    app.router.add_post('/api/admin/gateway/bulk_action', api_admin_gateway_bulk_action)"
    )

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)
print("Backend Bulk endpoint injected.")
