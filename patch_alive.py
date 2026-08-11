import re

with open('telegram-bot-backup/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace finally block to keep web server alive
target = """    finally:
        await bot.session.close()"""

replacement = """    finally:
        await bot.session.close()
        
    # Keep web server alive even if polling stops (Railway conflict)
    while True:
        await asyncio.sleep(3600)"""

if "Keep web server alive" not in content:
    content = content.replace(target, replacement)

with open('telegram-bot-backup/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("main.py patched to keep webserver alive.")
