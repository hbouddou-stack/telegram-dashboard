
with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('query += f\" AND q.thematic_node_id IN ({node_placeholders})\"', 'query += f\" AND q.thematic_node_id IN ({node_placeholders})\"\n                        params.extend(node_ids)')
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

