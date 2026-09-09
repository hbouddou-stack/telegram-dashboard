import io, re

with io.open('live_html.html', 'r', encoding='utf-8') as f:
    live = f.read()

# Find the full card building code around div.onclick
idx = live.find('div.onclick')
chunk = live[idx-2000:idx+500]
with io.open('card_onclick_context.txt', 'w', encoding='utf-8') as f:
    f.write(chunk)

# Also check logs-overlay HTML element
for needle in ['id="logs-overlay"', "id='logs-overlay'", 'logs-overlay']:
    idx2 = live.find(needle)
    if idx2 != -1:
        print(f'Found "{needle}" at {idx2}:')
        ctx = live[idx2-30:idx2+100]
        with io.open('overlay_context.txt', 'w', encoding='utf-8') as f:
            f.write(ctx)
        print(repr(ctx[:200]))
        break

# Check profile-name-text exists in HTML
for needle in ['id="profile-name-text"', "id='profile-name-text'"]:
    if needle in live:
        print(f'profile-name-text EXISTS in HTML')
        break
else:
    print('ERROR: profile-name-text MISSING from HTML')

# Check profile-import-text
for needle in ['id="profile-import-text"', "id='profile-import-text'"]:
    if needle in live:
        print(f'profile-import-text EXISTS in HTML')
        break
else:
    print('ERROR: profile-import-text MISSING from HTML - THIS WOULD CRASH THE FUNCTION')
