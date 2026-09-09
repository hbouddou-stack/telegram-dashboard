import io

with io.open('live_html.html', 'r', encoding='utf-8') as f:
    live = f.read()

# Find ALL getElementById calls in openStudentCard and check if their elements exist in HTML
import re

# Get the function
scripts = re.findall(r'<script[^>]*>(.*?)</script>', live, re.DOTALL)
main_script = max(scripts, key=len)

start = main_script.find('async function openStudentCard')
# Find function end
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

# Get all getElementById calls in the function
ids_in_func = re.findall(r"getElementById\('([^']+)'\)", func)
ids_in_func += re.findall(r'getElementById\("([^"]+)"\)', func)

print(f"Function uses {len(ids_in_func)} getElementById calls:")
missing = []
for eid in ids_in_func:
    if f'id="{eid}"' in live or f"id='{eid}'" in live:
        status = "✅"
    else:
        status = "❌ MISSING IN HTML"
        missing.append(eid)
    print(f"  {status}  #{eid}")

print()
print(f"MISSING ELEMENTS ({len(missing)}):")
for m in missing:
    print(f"  - #{m}")
