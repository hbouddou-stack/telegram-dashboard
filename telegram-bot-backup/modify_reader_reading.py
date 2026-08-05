import sys

with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    content = f.read()

search = '''            if (isReadingMode) {
                let textToRender = b.search_text || "";'''
replace = '''            if (isReadingMode) {
                let textToRender = (b.reading_text && b.reading_text.trim() !== "") ? b.reading_text : (b.search_text || "");'''

content = content.replace(search, replace)

with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(content)
