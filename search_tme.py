with open('main.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 't.me/' in line and ('start' in line or 'bot' in line.lower()):
            print(f"{i+1}: {line.strip()[:120]}")
