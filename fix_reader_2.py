import re

with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    js = f.read()

js = js.replace(
    'html += <div style="margin-bottom:12px; font-size:15px; color:var(--text); line-height:1.6;"><strong>الشرح التربوي:</strong><br></div>;',
    'html += <div style="margin-bottom:12px; font-size:15px; color:var(--text); line-height:1.6;"><strong>الشرح التربوي:</strong><br></div>;'
)

js = js.replace(
    'html += <div style="margin-bottom:12px; background:var(--surface-2); padding:12px; border-radius:8px; border-right:3px solid var(--primary); font-size:14.5px;"><span style="font-size:16px;">📌</span> <strong>ملاحظة الأستاذ:</strong><br></div>;',
    'html += <div style="margin-bottom:12px; background:var(--surface-2); padding:12px; border-radius:8px; border-right:3px solid var(--primary); font-size:14.5px;"><span style="font-size:16px;">📌</span> <strong>ملاحظة الأستاذ:</strong><br></div>;'
)

js = js.replace(
    'html += <div style="font-size:13px; color:var(--text-3); margin-top:8px;">📚 <strong>المصدر:</strong> </div>;',
    'html += <div style="font-size:13px; color:var(--text-3); margin-top:8px;">📚 <strong>المصدر:</strong> </div>;'
)

with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(js)
