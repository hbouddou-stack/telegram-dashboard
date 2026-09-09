import io, re

with io.open('live_html.html', 'r', encoding='utf-8') as f:
    live = f.read()

# Extract ALL script blocks
scripts = re.findall(r'<script[^>]*>(.*?)</script>', live, re.DOTALL)
print(f'Found {len(scripts)} script blocks')

# Find the main script (biggest one)
main_script = max(scripts, key=len)
print(f'Main script size: {len(main_script)}')

# Save it
with io.open('live_script.js', 'w', encoding='utf-8') as f:
    f.write(main_script)
print('Saved live_script.js')

# Count braces to check balance
opens = main_script.count('{')
closes = main_script.count('}')
print(f'Brace balance: {{ = {opens}, }} = {closes}, diff = {opens - closes}')

# Find openStudentCard and extract it
start = main_script.find('async function openStudentCard')
if start == -1:
    print('ERROR: openStudentCard NOT FOUND in script!')
else:
    # Find the function end by counting braces
    depth = 0
    end = start
    in_string = False
    string_char = None
    for i in range(start, len(main_script)):
        c = main_script[i]
        if in_string:
            if c == string_char and main_script[i-1] != '\\':
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
    print(f'openStudentCard: lines {main_script[:start].count(chr(10))+1} to {main_script[:end].count(chr(10))+1}')
    print(f'Function length: {len(func)} chars, {func.count(chr(10))} lines')
    
    # Check for logs-overlay
    if "logs-overlay" in func:
        idx = func.find("logs-overlay")
        print(f'logs-overlay found at position {idx}')
        print('Context:', repr(func[idx-50:idx+80]))
    else:
        print('ERROR: logs-overlay NOT FOUND inside function!')
    
    with io.open('live_open_card.js', 'w', encoding='utf-8') as f:
        f.write(func)
    print('Saved live_open_card.js')
