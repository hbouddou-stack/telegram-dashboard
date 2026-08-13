
with open('dashboard/reader.html', 'r', encoding='utf-8') as f:
    r_html = f.read()

r_html = r_html.replace('reader.js?v=practice-2', 'reader.js?v=practice-3')

with open('dashboard/reader.html', 'w', encoding='utf-8') as f:
    f.write(r_html)


with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    i_html = f.read()

i_html = i_html.replace('&v=p5', '&v=p6')

with open('dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(i_html)

print('Cache busters bumped!')

