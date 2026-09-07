import io
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix the remaining bad reference
c = c.replace(
    "if(activeStudent) fetchCrmTimeline(activeStudentObj.student_id, activeStudentObj.telegram_id)",
    "if(activeStudentObj) fetchCrmTimeline(activeStudentObj.student_id, activeStudentObj.telegram_id)"
)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("Fixed")
