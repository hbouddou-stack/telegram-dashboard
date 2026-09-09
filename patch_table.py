import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace TABLE VIEW container
old_grid = r"<div style=\"display:grid; grid-template-columns:repeat(\${Math.min(group.length, 2)}, 1fr); gap:0;\">"
new_flex = r"<div style=\"display:flex; overflow-x:auto; gap:0; padding-bottom:8px; scroll-snap-type: x mandatory;\">"
text = text.replace(old_grid, new_flex)

# Replace TABLE VIEW cards
old_card = r"<div style=\"padding:12px; border-left:${idx > 0 ? '1px solid var(--border)' : 'none'};"
new_card = r"<div style=\"flex:0 0 260px; scroll-snap-align: start; padding:12px; border-left:${idx > 0 ? '1px solid var(--border)' : 'none'};"
text = text.replace(old_card, new_card)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Patched table view')
