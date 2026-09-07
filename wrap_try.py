with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

import re

pattern = re.compile(r"(function filterStudents\(\) \{)(.*?)(^\s*\})", re.DOTALL | re.MULTILINE)

def replacer(match):
    prefix = match.group(1)
    body = match.group(2)
    suffix = match.group(3)
    
    if "try {" in body:
        return match.group(0) # already wrapped
        
    wrapped = f"""
            try {{
{body}
            }} catch(err) {{
                alert('UI Render Error: ' + err.message + '\\n' + err.stack);
            }}"""
    return prefix + wrapped + suffix

text = pattern.sub(replacer, text)
with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
    f.write(text)
print("Wrapped filterStudents in try-catch!")
