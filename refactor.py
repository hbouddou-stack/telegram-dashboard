with open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

funnel_start = text.find('<!-- FUNNEL ANALYTICS PRO -->')
students_list = text.find('<div id="students-list"></div>')

funnel_html = text[funnel_start:students_list]

text = text[:funnel_start] + text[students_list:]

new_tab = '\n    <!-- TAB: Overview -->\n    <div id="tab-overview" class="tab-content active">\n        ' + funnel_html + '\n    </div>\n'

text = text.replace('<div id="tab-students" class="tab-content active">', '<div id="tab-students" class="tab-content">')
text = text.replace('<!-- TAB: ?????? -->', new_tab + '\n    <!-- TAB: ?????? -->')

with open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
