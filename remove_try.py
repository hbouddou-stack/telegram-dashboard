with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

import re

# Remove `            try {`
text = text.replace("            try {\n                const q = document.getElementById('search-input').value.toLowerCase();", "                const q = document.getElementById('search-input').value.toLowerCase();")

# Remove the catch block
#             } catch(err) {
#                 alert('UI Render Error: ' + err.message + '\n' + err.stack);
#             }            });
text = text.replace("""            } catch(err) {
                alert('UI Render Error: ' + err.message + '\\n' + err.stack);
            }            });""", "            });")


with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
    f.write(text)
print("try-catch removed!")
