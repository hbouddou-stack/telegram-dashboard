import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

target = '<div id="students-list" class="list-container">'
replacement = '<div id="students-count-display" style="padding: 10px 15px; font-weight: 800; color: var(--text1); font-size: 0.9rem; background: rgba(0, 132, 255, 0.05); border-bottom: 1px solid var(--border);"></div>\n          <div id="students-list" class="list-container">'

c = c.replace(target, replacement)

js_target = '''            if (elTotal) elTotal.textContent = filtered.length;
            if (elLinked) elLinked.textContent = linkedCount;
            if (elPct) elPct.textContent = filtered.length ? Math.round(linkedCount / filtered.length * 100) + '%' : '';'''

js_replacement = js_target + '''\n            const countDisplay = document.getElementById('students-count-display');
            if (countDisplay) {
                countDisplay.innerHTML = `📊 <span>العدد الإجمالي: <span style="color:#0084ff;">${filtered.length}</span> طالب</span> <span style="color:var(--text2); font-size:0.8rem; margin-right:10px;">(منهم ${linkedCount} مربوط)</span>`;
            }'''

c = c.replace(js_target, js_replacement)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Added student count badge')
