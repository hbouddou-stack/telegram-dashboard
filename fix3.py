import os
import re

file_path = r"C:\Users\Houssam\Desktop\Telegram-Bot-Assets\main.py"

with open(file_path, "r", encoding="utf-8") as f:
    main_py = f.read()

clean_func = """async def api_support(request):
    try:
        content_type = request.content_type if request.content_type else ''
        file_data = None
        file_name = None
        
        if 'multipart/form-data' in content_type:
            reader = await request.multipart()
            data = {}
            async for field in reader:
                if field.name == 'attachment':
                    file_name = field.filename
                    file_data = await field.read()
                else:
                    data[field.name] = await field.text()
            
            theme = data.get('theme')
            subtheme = data.get('subtheme')
            msg = data.get('message')
            telegram_id = data.get('telegram_id')
            username = data.get('username', 'غير معروف')
            first_name = data.get('first_name', 'غير معروف')
            auto_resolved = data.get('auto_resolved') == 'true'
        else:
            data = await request.json()
            theme = data.get('theme')
            subtheme = data.get('subtheme')
            msg = data.get('message')
            telegram_id = data.get('telegram_id')
            username = data.get('username', 'غير معروف')
            first_name = data.get('first_name', 'غير معروف')
            auto_resolved = data.get('auto_resolved', False)

        import database as db
        
        status = 'resolved' if auto_resolved else 'new'
        ai_topic = 'IA' if auto_resolved else ''
        
        db_msg = msg
        if file_name:
            db_msg = msg + f"\\n\\n[مرفق: {file_name}]"
            
        ticket_id = await db.create_crm_ticket(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            theme=theme,
            subtheme=subtheme,
            message=db_msg,
            status=status,
            is_ghost=auto_resolved,
            ai_topic=ai_topic
        )
        
        if not auto_resolved:
            import requests
            from config import TELEGRAM_BOT_TOKEN, TELEGRAM_SUPPORT_GROUP_ID
            text = f'🆘 <b>طلب مساعدة / استفسار جديد #{ticket_id}</b>\\n\\n'
            text += f'👤 <b>الطالب:</b> {first_name} (@{username})\\n'
            text += f'🆔 <b>Telegram ID:</b> {telegram_id}\\n'
            text += f'📂 <b>القسم:</b> {theme}\\n'
            text += f'🔖 <b>التفاصيل:</b> {subtheme}\\n\\n'
            text += f'📝 <b>الرسالة:</b>\\n{msg}\\n\\n'
            text += f'🔗 للرد، يرجى الدخول إلى لوحة التحكم (Admin Dashboard /federer).'
            
            url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
            payload = {
                'chat_id': TELEGRAM_SUPPORT_GROUP_ID,
                'text': text,
                'parse_mode': 'HTML'
            }
            if file_data:
                files = {'document': (file_name, file_data)}
                payload['caption'] = text
                del payload['text']
                doc_url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument'
                requests.post(doc_url, data=payload, files=files)
            else:
                requests.post(url, json=payload)
        
        from aiohttp import web
        return web.json_response({'success': True, 'ticket_id': ticket_id})"""

pattern = re.compile(r'async def api_support\(request\):.*?return web\.json_response\(\{.*?ticket_id.*?\}\)', re.DOTALL)

if pattern.search(main_py):
    # USE LAMBDA TO AVOID RE.SUB ESCAPE PARSING
    main_py = pattern.sub(lambda m: clean_func, main_py)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(main_py)
    print("Replaced safely")
else:
    print("Could not find the function")
