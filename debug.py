with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()

old = """                if(data.success) {
                    allStudents = data.students;
                    filterStudents();
                } else {"""

new = """                if(data.success) {
                    alert('FETCH SUCCESS. Rows: ' + data.students.length);
                    allStudents = data.students;
                    filterStudents();
                } else {"""

text = text.replace(old, new)
with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
    f.write(text)
print("Added success alert!")
