with open('main.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        l = line.lower()
        if 'commandstart' in l or 'start_bot' in l or 'start_polling' in l or 'magic_token' in l or 'auth_router' in l:
            print(f"{i+1}: {line.strip()[:120]}")
