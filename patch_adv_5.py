import re

# Update HTML
with open('dashboard/reader.html', 'r', encoding='utf-8') as f:
    html = f.read()

errors_container = '''
            <div id="quiz-errors-container" style="display:none; text-align:right; margin-bottom:24px; padding:16px; background:var(--surface); border-radius:12px; border:1px solid #ef4444;">
                <h3 style="color:#ef4444; margin-bottom:12px; font-size:18px;">الأسئلة التي أخطأت فيها:</h3>
                <div id="quiz-errors-list"></div>
            </div>
'''

if 'id="quiz-errors-container"' not in html:
    html = html.replace('<button onclick="quizEngine.start()"', errors_container + '\n            <button onclick="quizEngine.start()"')
    with open('dashboard/reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
        print('reader.html errors container added')

# Update JS
with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    js = f.read()

js_addition = '''
        const errorsContainer = document.getElementById('quiz-errors-container');
        const errorsList = document.getElementById('quiz-errors-list');
        if (this.wrongAnswers && this.wrongAnswers.length > 0) {
            errorsContainer.style.display = 'block';
            let html = '';
            this.wrongAnswers.forEach((q, idx) => {
                let expHtml = this.formatExplanationHtml(q.explanation);
                html += 
                    <div style="margin-bottom:16px; border-bottom:1px solid var(--surface-2); padding-bottom:16px;">
                        <p style="font-weight:bold; color:var(--text); margin-bottom:8px;">السؤال: </p>
                        <div style="font-size:14px; color:var(--text-2); background:#fef2f2; padding:8px; border-radius:8px; margin-bottom:8px;">الإجابة الصحيحة كانت: <strong></strong></div>
                        <div style="font-size:14px;"></div>
                    </div>
                ;
            });
            errorsList.innerHTML = html;
        } else {
            errorsContainer.style.display = 'none';
        }
'''

if "errorsContainer.style.display" not in js:
    # insert before msgEl.textContent = ...
    js = js.replace("const msgEl = document.getElementById('quiz-final-msg');", "const msgEl = document.getElementById('quiz-final-msg');\n" + js_addition)
    with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
        print('reader.js errors logic added')

