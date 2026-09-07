with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
# We need to target the EXACT `filtered.forEach(s => {` block that follows `const list = document.getElementById('students-list');`
# and ends with `list.appendChild(div);`

pattern = re.compile(r"(const list = document\.getElementById\('students-list'\);\s*list\.innerHTML = '';\s*if\(filtered\.length === 0\) \{\s*list\.innerHTML = '[^']+';\s*return;\s*\}\s*)(filtered\.forEach\(s => \{.*?list\.appendChild\(div\);\s*\}\);)(\s*if \(typeof renderStudents === 'function'\))", re.DOTALL)

def replacer(match):
    prefix = match.group(1)
    loop_code = match.group(2)
    suffix = match.group(3)

    # Extract the inner body of the forEach
    body_match = re.search(r"filtered\.forEach\(s => \{(.*?)\}\);", loop_code, re.DOTALL)
    if not body_match:
        return match.group(0) # fail safe
    
    body = body_match.group(1)
    body = body.replace("list.appendChild(div);", "fragment.appendChild(div);")
    
    new_loop = f"""const fragment = document.createDocumentFragment();
            const displayLimit = Math.min(filtered.length, 500);
            for(let i=0; i<displayLimit; i++) {{
                const s = filtered[i];
{body}
            }}
            list.appendChild(fragment);
            if(filtered.length > 500) {{
                const more = document.createElement('div');
                more.style.textAlign = 'center';
                more.style.padding = '15px';
                more.style.color = 'var(--text2)';
                more.innerHTML = `?? ????? ${{filtered.length - 500}} ???? ?????? ??????. ?????? ????? ?????? ?????.`;
                list.appendChild(more);
            }}"""
            
    return prefix + new_loop + suffix

# Fix both occurrences since the file is duplicated at the bottom
text = pattern.sub(replacer, text)

with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
    f.write(text)
print("Performance fix applied cleanly!")
