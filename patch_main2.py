import re

with open('telegram-bot-backup/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all occurrences of json.dump for transcripts_path
def replacer(match):
    return "await save_lesson_to_db(subject, lesson_num, lesson)"

# We find blocks starting with "with open(transcripts_path, 'w', encoding='utf-8') as f:"
# and ending after the git push, or just the with open block.

# First pass: replace the git push blocks
content = re.sub(
    r"with open\(transcripts_path, 'w', encoding='utf-8'\) as f:\s*json\.dump\(lessons, f, ensure_ascii=False.*?(?:\n\s*subprocess\.run\(\[\"git\", \"push\", \"origin\", \"main\"\].*?\n\s*except Exception as git_err:\n\s*logger\.error\(f\"Git auto-deploy failed: \{git_err\}\"\)\s*)?",
    "await save_lesson_to_db(subject, lesson_num, lesson)",
    content,
    flags=re.DOTALL
)

with open('telegram-bot-backup/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch 2 applied successfully.")
