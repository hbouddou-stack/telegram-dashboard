import re
with open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()
    idx1 = text.find('function filterStudents()')
    idx2 = text.find('function sortStudents(', idx1)
    print(text[idx2-1000:idx2].encode('ascii', 'ignore').decode('ascii'))
