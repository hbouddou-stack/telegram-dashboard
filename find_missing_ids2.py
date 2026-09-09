import io

with io.open('live_html.html', 'r', encoding='utf-8') as f:
    live = f.read()

import re

scripts = re.findall(r'<script[^>]*>(.*?)</script>', live, re.DOTALL)
main_script = max(scripts, key=len)

start = main_script.find('async function openStudentCard')
depth = 0
end = start
in_string = False
string_char = None
for i in range(start, len(main_script)):
    c = main_script[i]
    if in_string:
        if c == string_char and (i == 0 or main_script[i-1] != '\\'):
            in_string = False
    elif c in ('"', "'", '`'):
        in_string = True
        string_char = c
    elif c == '{':
        depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0:
            end = i
            break

func = main_script[start:end+1]

ids_in_func = re.findall(r"getElementById\('([^']+)'\)", func)
ids_in_func += re.findall(r'getElementById\("([^"]+)"\)', func)

missing = []
present = []
for eid in ids_in_func:
    if f'id="{eid}"' in live or f"id='{eid}'" in live:
        present.append(eid)
    else:
        missing.append(eid)

with io.open('dom_report.txt', 'w', encoding='utf-8') as out:
    out.write(f"PRESENT ({len(present)}):\n")
    for p in present:
        out.write(f"  OK  #{p}\n")
    out.write(f"\nMISSING ({len(missing)}):\n")
    for m in missing:
        out.write(f"  MISSING  #{m}\n")

print(f"PRESENT: {len(present)}, MISSING: {len(missing)}")
print("Missing IDs:")
for m in missing:
    print(" -", m)
