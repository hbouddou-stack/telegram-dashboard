import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_rag = """                for question, answer in faq_data[theme].items():
                    # Simple heuristic: if subtheme is in question or any word overlaps heavily
                    if question in subtheme or subtheme in question:
                        return web.json_response({'found': True, 'answer': answer})"""

new_rag = """                for question, answer_obj in faq_data[theme].items():
                    if question in subtheme or subtheme in question:
                        if isinstance(answer_obj, dict):
                            ans_text = answer_obj.get('text', '')
                            story_id = answer_obj.get('story_id')
                            return web.json_response({'found': True, 'answer': ans_text, 'story_id': story_id})
                        else:
                            return web.json_response({'found': True, 'answer': answer_obj})"""

text = text.replace(old_rag, new_rag)

old_support = """        status = 'resolved' if auto_resolved else 'new'
        ai_topic = 'IA' if auto_resolved else ''
        
        db_msg = msg
        if file_name:
            db_msg = msg + f"\\n\\n[مرفق: {file_name}]"
            
        ticket_id = await db.create_crm_ticket("""

new_support = """        status = 'resolved' if auto_resolved else 'new'
        ai_topic = 'IA' if auto_resolved else ''
        
        story_id = data.get('story_id')
        if ai_reply and story_id is not None:
            ai_reply += f'<br><br><button onclick="openStoryViewer({story_id})" style="background:linear-gradient(135deg, #FF416C, #FF4B2B); color:white; border:none; padding:8px 16px; border-radius:12px; cursor:pointer; font-family:\\'Tajawal\\'; font-weight:bold; display:inline-flex; align-items:center; gap:6px;">🎬 عرض التوضيح المباشر (Story)</button>'
        
        db_msg = msg
        if file_name:
            db_msg = msg + f"\\n\\n[مرفق: {file_name}]"
            
        ticket_id = await db.create_crm_ticket("""

text = text.replace(old_support, new_support)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("RAG and Support endpoints patched to handle stories")
