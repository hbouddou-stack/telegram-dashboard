import re

with open('dashboard/admin_gateway.html', 'rb') as f:
    c = f.read()

scripts = re.findall(rb'<script[^>]*>(.*?)</script>', c, re.DOTALL)
main_script = max(scripts, key=len)
start = main_script.find(b'async function openStudentCard')
depth = 0
end = start
in_string = False
string_char = None
for i in range(start, len(main_script)):
    ch = main_script[i:i+1]
    if in_string:
        if ch == string_char and main_script[i-1:i] != b'\\':
            in_string = False
    elif ch in (b'"', b"'", b'`'):
        in_string = True
        string_char = ch
    elif ch == b'{':
        depth += 1
    elif ch == b'}':
        depth -= 1
        if depth == 0:
            end = i
            break

func = main_script[start:end+1]
ids_in_func = re.findall(rb"getElementById\('([^']+)'\)", func)
ids_in_func += re.findall(rb'getElementById\("([^"]+)"\)', func)

missing = []
for eid in ids_in_func:
    eid_str = eid.decode('utf-8')
    if b'id="' + eid + b'"' in c or b"id='" + eid + b"'" in c:
        pass
    else:
        missing.append(eid_str)

print('MISSING IDs:', missing)
print('All OK!' if not missing else f'{len(missing)} elements still missing!')
