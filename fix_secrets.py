import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

if 'import secrets' not in c:
    # Inject it right after import sys
    c = c.replace('import sys\n', 'import sys\nimport secrets\n')
    
    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Injected import secrets")
else:
    print("Already imported")
