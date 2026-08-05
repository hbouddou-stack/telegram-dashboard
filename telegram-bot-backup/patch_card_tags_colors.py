import sys
import re

with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    js = f.read()

search = '''                            blocks.forEach((b, idx) => {
                                axesHtml += `<span style="background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-secondary); padding: 4px 10px; border-radius: 20px; font-size: 0.78rem; display: flex; align-items: center; gap: 4px;"><strong style="color: var(--primary); font-size: 0.85rem;">${idx + 1}.</strong> <span>${escapeHtml(b.title || 'محور')}</span></span>`;
                            });'''

replace = '''                            let tagColor = subColor.startsWith('var(') ? '#8b5cf6' : subColor;
                            blocks.forEach((b, idx) => {
                                axesHtml += `<span style="background: ${tagColor}15; border: 1px solid ${tagColor}40; color: ${tagColor}; padding: 4px 10px; border-radius: 20px; font-size: 0.78rem; display: flex; align-items: center; gap: 4px; font-weight: 600;"><strong style="color: ${tagColor}; font-size: 0.85rem; font-weight: 800;">${idx + 1}.</strong> <span>${escapeHtml(b.title || 'محور')}</span></span>`;
                            });'''

if search in js:
    js = js.replace(search, replace)
    with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print("Tags colors patched successfully!")
else:
    print("Could not find the search string to replace.")
