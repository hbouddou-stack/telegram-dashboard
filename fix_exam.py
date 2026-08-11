import re

with open('dashboard/exam.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Add goToStep4
js = js.replace('startQuiz() {', '''goToStep4() {
        document.getElementById('exam-step-3').style.display = 'none';
        document.getElementById('exam-step-4').style.display = 'block';
    },

    startQuiz() {''')

with open('dashboard/exam.js', 'w', encoding='utf-8') as f:
    f.write(js)

with open('dashboard/reader.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('onclick="examWizard.startExam()"', 'onclick="examWizard.startQuiz()"')

with open('dashboard/reader.html', 'w', encoding='utf-8') as f:
    f.write(html)
