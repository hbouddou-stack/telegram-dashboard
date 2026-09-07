import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where BOT_STARTED or bot_started_at is set
for i, l in enumerate(lines):
    if 'bot_started_at' in l and 'UPDATE' in l.upper():
        print(i, l.strip()[:150])

# Also find pending_verifications usage
for i, l in enumerate(lines):
    if 'pending_verifications' in l and ('INSERT' in l.upper() or 'insert' in l.lower()):
        print(i, l.strip()[:150])

# Find the /start equivalent
for i, l in enumerate(lines):
    if ('message_handler' in l or 'MessageHandler' in l) and 'start' in l.lower():
        print(i, l.strip()[:150])
