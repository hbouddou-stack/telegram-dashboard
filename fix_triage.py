import re

with open('handlers/support.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace db.search_similar_triage(text_content) with db.search_similar_triage(text_content, use_ai=True)
content = content.replace(
    'matches = await db.search_similar_triage(text_content)', 
    'matches = await db.search_similar_triage(text_content, use_ai=True)'
)

with open('handlers/support.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Success")
