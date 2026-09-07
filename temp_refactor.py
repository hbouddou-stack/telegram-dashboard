with open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the escaped quotes
content = content.replace(\"onclick=\\"switchTab(\\'overview\\')\\\"\", 'onclick=\"switchTab(\'overview\')\"')

# Force create overview tab
funnel_start = content.find('<!-- FUNNEL ANALYTICS PRO -->')
students_list_start = content.find('<div id=\"students-list\"></div>')

if funnel_start != -1 and students_list_start != -1:
    extracted = content[funnel_start:students_list_start]
    content = content[:funnel_start] + content[students_list_start:]
    
    new_tab = '''
    <!-- TAB: Overview -->
    <div id="tab-overview" class="tab-content active">
        ''' + extracted + '''
    </div>
    '''
    
    # turn off tab-students
    content = content.replace('<div id="tab-students" class="tab-content active">', '<div id="tab-students" class="tab-content">')
    
    # insert before tab-students
    idx2 = content.find('<div id="tab-students"')
    if idx2 != -1:
        content = content[:idx2] + new_tab + content[idx2:]

with open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(content)
