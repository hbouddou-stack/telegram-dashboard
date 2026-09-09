with open('main.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'send_email' in line or 'log_wa' in line or 'action' in line.lower() and 'gateway' in line:
            print(f"{i+1}: {line.strip()[:120]}")
