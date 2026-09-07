with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

# Fix chips
text = text.replace("?? ????", "?? ????")
text = text.replace("?? ?????? ????????", "?? ???? ?????????")
text = text.replace("?? ?? ?????? ???", "?? ?? ???? ???")
text = text.replace("?? ????? ??? ????", "?? ?? ??? ????????")
text = text.replace("? ?????", "? ??????")

# Fix DOM bottleneck
old_loop = """            const list = document.getElementById('students-list');
            list.innerHTML = '';
            filtered.forEach(s => {
                const div = document.createElement('div');
                div.className = 'list-item';
                div.onclick = () => openStudentCard(s);"""

new_loop = """            const list = document.getElementById('students-list');
            const fragment = document.createDocumentFragment();
            const displayLimit = Math.min(filtered.length, 500);
            for(let i=0; i<displayLimit; i++) {
                const s = filtered[i];
                const div = document.createElement('div');
                div.className = 'list-item';
                div.onclick = () => openStudentCard(s);"""

old_append = """                list.appendChild(div);
            });
            if (typeof renderStudents === 'function') {"""

new_append = """                fragment.appendChild(div);
            }
            list.innerHTML = '';
            list.appendChild(fragment);
            if (filtered.length > 500) {
                const more = document.createElement('div');
                more.style.textAlign = 'center';
                more.style.padding = '15px';
                more.style.color = 'var(--text2)';
                more.innerHTML = `?? ????? ${filtered.length - 500} ???? ?????? ??????. ?????? ????? ?????? ?????.`;
                list.appendChild(more);
            }
            if (typeof renderStudents === 'function') {"""

if old_loop in text and old_append in text:
    text = text.replace(old_loop, new_loop)
    text = text.replace(old_append, new_append)
    with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
        f.write(text)
    print("Patched correctly!")
else:
    print("Could not find blocks to patch.")
