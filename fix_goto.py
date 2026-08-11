import re

with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace goToChapter function in index.html to redirect to reader.html
new_goto = '''function goToChapter(event, subject, lessonNum, chapterIdx) {
    if (event) event.stopPropagation();
    window.location.href = 'reader.html?subject=' + subject + '&lesson=' + lessonNum + '&v=p5';
}'''

content = re.sub(
    r'function goToChapter.*?setTimeout.*?\}, 200\);\s*\}', 
    new_goto, 
    content, 
    flags=re.DOTALL
)

with open('dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Success goToChapter")
