import re

with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

# Replace list.innerHTML = ''; filtered.forEach(s => ... list.appendChild(div); });
# with the document fragment and limits.

pattern = re.compile(r"const list = document\.getElementById\('students-list'\);\s*list\.innerHTML = '';\s*filtered\.forEach\(s => \{.*?list\.appendChild\(div\);\s*\}\);", re.DOTALL)

def replacer(match):
    original = match.group(0)
    # inside original, replace filtered.forEach with a for loop
    body = re.search(r"filtered\.forEach\(s => \{(.*?)\}\);", original, re.DOTALL).group(1)
    
    # We replace list.appendChild(div) with fragment.appendChild(div)
    body = body.replace("list.appendChild(div);", "fragment.appendChild(div);")
    
    new_code = f"""const list = document.getElementById('students-list');
            const fragment = document.createDocumentFragment();
            const displayLimit = Math.min(filtered.length, 500);
            for(let i=0; i<displayLimit; i++) {{
                const s = filtered[i];
{body}
            }}
            list.innerHTML = '';
            list.appendChild(fragment);
            if (filtered.length > 500) {{
                const more = document.createElement('div');
                more.style.textAlign = 'center';
                more.style.padding = '15px';
                more.style.color = 'var(--text2)';
                more.innerHTML = `?? ????? ${{filtered.length - 500}} ???? ?????? ??????. ?????? ????? ?????? ?????.`;
                list.appendChild(more);
            }}"""
    return new_code

text = pattern.sub(replacer, text)
with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
    f.write(text)
print("Regex replace done!")
