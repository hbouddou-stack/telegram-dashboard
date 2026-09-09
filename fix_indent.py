import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if l.startswith("app.router.add_"):
        lines[i] = "    " + l

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
