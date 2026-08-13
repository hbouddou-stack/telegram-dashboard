
with open('telegram-bot/keyboards.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('?v=6', '?v=7')

with open('telegram-bot/keyboards.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Bot WebApp URL bumped')

