import re

with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    js = f.read()

js = re.sub(
    r'html \+= <div style="margin-bottom:12px; font-size:15px; color:var\(--text\); line-height:1\.6;"><strong>(.*?)</strong><br></div>;',
    r'html += <div style="margin-bottom:12px; font-size:15px; color:var(--text); line-height:1.6;"><strong>\1</strong><br></div>;',
    js
)

js = re.sub(
    r'html \+= <div style="margin-bottom:12px; background:var\(--surface-2\); padding:12px; border-radius:8px; border-right:3px solid var\(--primary\); font-size:14\.5px;"><span style="font-size:16px;">(.*?)</span> <strong>(.*?)</strong><br></div>;',
    r'html += <div style="margin-bottom:12px; background:var(--surface-2); padding:12px; border-radius:8px; border-right:3px solid var(--primary); font-size:14.5px;"><span style="font-size:16px;">\1</span> <strong>\2</strong><br></div>;',
    js
)

js = re.sub(
    r'html \+= <div style="font-size:13px; color:var\(--text-3\); margin-top:8px;">(.*?) <strong>(.*?)</strong> </div>;',
    r'html += <div style="font-size:13px; color:var(--text-3); margin-top:8px;">\1 <strong>\2</strong> </div>;',
    js
)

with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(js)
