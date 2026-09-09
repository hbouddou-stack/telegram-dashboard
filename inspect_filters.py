with open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()
    idx1 = text.find('id="tab-students"')
    idx2 = text.find('id="students-grid"')
    print(text[idx1:idx2].encode('ascii', 'ignore').decode('ascii'))
