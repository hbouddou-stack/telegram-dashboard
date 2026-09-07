with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

import re

# Remove the fetch success alert
text = re.sub(r"alert\('FETCH SUCCESS[^;]+;\s*", "", text)

# Remove the fetch error alert
#     } else { alert('FETCH ERROR: ' + data.error); }
text = re.sub(r"\} else \{\s*alert\('FETCH ERROR: ' \+ data\.error\);\s*\}", "}", text)


with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
    f.write(text)
print("Alerts removed!")
