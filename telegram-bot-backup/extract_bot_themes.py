import ast
import json

file_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\keyboards.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

module = ast.parse(content)
themes_dict = None
for node in module.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        if getattr(node.targets[0], 'id', '') == 'THEMES':
            themes_dict = ast.literal_eval(node.value)
            break

# Format into a markdown string
md_lines = []
md_lines.append("# Thématiques utilisées dans le Mode Exercice (Bot Telegram)")
md_lines.append("\nVoici les thématiques que les étudiants voient lorsqu'ils révisent sur le bot :\n")

for subject_id, themes in themes_dict.items():
    md_lines.append(f"## Matière : {subject_id}")
    for theme_id, data in themes.items():
        label = data.get('label', theme_id)
        lessons = data.get('lessons', [])
        md_lines.append(f"- **{label}** (Leçons: {', '.join(map(str, lessons))})")
    md_lines.append("")

with open(r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\scratch\bot_themes_export.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))
