import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_rag_logic = """            if theme in faq_data:
                # Basic exact/keyword match for MVP
                for question, answer_obj in faq_data[theme].items():
                    if question in subtheme or subtheme in question:
                        if isinstance(answer_obj, dict):
                            ans_text = answer_obj.get('text', '')
                            story_id = answer_obj.get('story_id')
                            return web.json_response({'found': True, 'answer': ans_text, 'story_id': story_id})
                        else:
                            return web.json_response({'found': True, 'answer': answer_obj})"""

new_rag_logic = """            # Search globally across all themes if no theme specified or just global search anyway
            for t, questions in faq_data.items():
                for question, answer_obj in questions.items():
                    # Check if msg matches question or vice-versa
                    if msg and (question.lower() in msg or msg in question.lower() or any(word in question.lower() for word in msg.split() if len(word) > 4)):
                        if isinstance(answer_obj, dict):
                            ans_text = answer_obj.get('text', '')
                            story_id = answer_obj.get('story_id')
                            return web.json_response({'found': True, 'answer': ans_text, 'story_id': story_id})
                        else:
                            return web.json_response({'found': True, 'answer': answer_obj})
            
            return web.json_response({'found': False})"""

text = text.replace(old_rag_logic, new_rag_logic)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Patched RAG to search globally without themes')
