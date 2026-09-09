import io
import re

# 1. Update database.py
with io.open('database.py', 'r', encoding='utf-8') as f:
    db_text = f.read()

old_db_def = "async def create_crm_ticket(telegram_id, username, first_name, theme, subtheme, message, status='new', is_ghost=False, ai_topic='', file_data=None, file_name=None):"
new_db_def = "async def create_crm_ticket(telegram_id, username, first_name, theme, subtheme, message, status='new', is_ghost=False, ai_topic='', file_data=None, file_name=None, ai_reply=None):"

old_db_conv = """        init_conv = [{
            "sender": "student",
            "name": first_name or "\u0623\u0646\u062a",
            "text": message,
            "file_data": file_data_str,
            "file_name": file_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }]"""
new_db_conv = """        init_conv = [{
            "sender": "student",
            "name": first_name or "\u0623\u0646\u062a",
            "text": message,
            "file_data": file_data_str,
            "file_name": file_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }]
        if ai_reply:
            init_conv.append({
                "sender": "admin",
                "name": "\u0627\u0644\u0645\u0633\u0627\u0639\u062f \u0627\u0644\u0630\u0643\u064a",
                "text": ai_reply,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            })"""

db_text = db_text.replace(old_db_def, new_db_def).replace(old_db_conv, new_db_conv)
with io.open('database.py', 'w', encoding='utf-8') as f:
    f.write(db_text)


# 2. Update main.py api_support
with io.open('main.py', 'r', encoding='utf-8') as f:
    main_text = f.read()

old_main_vars = """            auto_resolved = data.get('auto_resolved') == 'true'
        else:
            data = await request.json()
            theme = data.get('theme')
            subtheme = data.get('subtheme')
            msg = data.get('message')
            telegram_id = data.get('telegram_id')
            username = data.get('username', '\u063a\u064a\u0631 \u0645\u0639\u0631\u0648\u0641')
            first_name = data.get('first_name', '\u063a\u064a\u0631 \u0645\u0639\u0631\u0648\u0641')
            auto_resolved = data.get('auto_resolved', False)
            file_data = data.get('file_data')
            file_name = data.get('file_name')

        import database as db
        
        status = 'resolved' if auto_resolved else 'new'
        ai_topic = 'IA' if auto_resolved else ''"""

new_main_vars = """            auto_resolved = data.get('auto_resolved') == 'true'
            ai_reply = data.get('ai_reply')
        else:
            data = await request.json()
            theme = data.get('theme')
            subtheme = data.get('subtheme')
            msg = data.get('message')
            telegram_id = data.get('telegram_id')
            username = data.get('username', '\u063a\u064a\u0631 \u0645\u0639\u0631\u0648\u0641')
            first_name = data.get('first_name', '\u063a\u064a\u0631 \u0645\u0639\u0631\u0648\u0641')
            auto_resolved = data.get('auto_resolved', False)
            ai_reply = data.get('ai_reply')
            file_data = data.get('file_data')
            file_name = data.get('file_name')

        import database as db
        
        status = 'resolved' if auto_resolved else 'new'
        ai_topic = 'IA' if auto_resolved else ''"""

old_db_call = """        ticket_id = await db.create_crm_ticket(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            theme=theme,
            subtheme=subtheme,
            message=db_msg,
            status=status,
            is_ghost=auto_resolved,
            ai_topic=ai_topic,
            file_data=file_data,
            file_name=file_name
        )"""

new_db_call = """        ticket_id = await db.create_crm_ticket(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            theme=theme,
            subtheme=subtheme,
            message=db_msg,
            status=status,
            is_ghost=auto_resolved,
            ai_topic=ai_topic,
            file_data=file_data,
            file_name=file_name,
            ai_reply=ai_reply
        )"""

main_text = main_text.replace(old_main_vars, new_main_vars).replace(old_db_call, new_db_call)
with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_text)

print("Backend patched for AI ghost tickets")
