with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

import re

old = """                if(data.success) {
                    allStudents = data.students;
                    filterStudents();
                }"""

new = """                if(data.success) {
                    allStudents = data.students;
                    filterStudents();
                } else {
                    alert('FETCH ERROR: ' + data.error);
                }"""

text = text.replace(old, new)
with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
    f.write(text)
print("Added error alert!")
