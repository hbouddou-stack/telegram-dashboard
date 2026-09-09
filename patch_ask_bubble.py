import io

with io.open('dashboard/ask.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix text rendering in chat bubbles by adding dir="auto"
old_bubble = """<div id="msg-bubble-${idx}" style="background:${isStudent ? '#1e3a8a' : 'rgba(255,255,255,0.08)'}; border:1px solid ${isStudent ? '#3b82f6' : 'rgba(255,255,255,0.15)'}; padding:12px 16px; border-radius:14px; max-width:85%; font-size:0.9rem; line-height:1.5; color:#fff;">
                        ${(m.text || '').replace"""
new_bubble = """<div id="msg-bubble-${idx}" dir="auto" style="background:${isStudent ? '#1e3a8a' : 'rgba(255,255,255,0.08)'}; border:1px solid ${isStudent ? '#3b82f6' : 'rgba(255,255,255,0.15)'}; padding:12px 16px; border-radius:14px; max-width:85%; font-size:0.9rem; line-height:1.5; color:#fff;">
                        ${(m.text || '').replace"""

text = text.replace(old_bubble, new_bubble)

with io.open('dashboard/ask.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Chat bubble dir="auto" patched')
