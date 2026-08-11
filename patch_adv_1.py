import re
import os

# 1. Update reader.html
with open('dashboard/reader.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add step 4 (settings)
step4_html = '''
                <div id="exam-step-4" style="display:none;">
                    <h3 style="color:var(--text); margin-bottom:16px;">إعدادات الامتحان ⚙️</h3>
                    
                    <div style="margin-bottom:20px;">
                        <label style="display:block; margin-bottom:8px; font-weight:bold; color:var(--text);">طريقة التصحيح:</label>
                        <select id="exam-correction-mode" style="width:100%; padding:12px; border-radius:12px; border:2px solid var(--surface-2); background:var(--surface); color:var(--text); font-size:16px;">
                            <option value="instant">⚡ تصحيح فوري (إظهار النتيجة بعد كل سؤال)</option>
                            <option value="end">🤫 تصحيح في النهاية (امتحان صارم)</option>
                        </select>
                    </div>

                    <div style="margin-bottom:20px;">
                        <label style="display:block; margin-bottom:8px; font-weight:bold; color:var(--text);">الوقت لكل سؤال:</label>
                        <select id="exam-timer-mode" style="width:100%; padding:12px; border-radius:12px; border:2px solid var(--surface-2); background:var(--surface); color:var(--text); font-size:16px;">
                            <option value="0">♾️ بدون وقت محدد</option>
                            <option value="15">⏱️ 15 ثانية</option>
                            <option value="30">⏱️ 30 ثانية</option>
                            <option value="60">⏱️ 60 ثانية</option>
                        </select>
                    </div>

                    <button onclick="examWizard.startExam()" style="width:100%; padding:16px; background:var(--primary); color:#fff; font-size:18px; font-weight:bold; border:none; border-radius:12px; cursor:pointer; margin-top:10px;">🚀 بدء الامتحان</button>
                </div>
'''

if 'id="exam-step-4"' not in html:
    html = html.replace('id="exam-step-3"', 'id="exam-step-3"')
    html = html.replace('<!-- Step 3', '<!-- Step 3')
    html = re.sub(r'(<button onclick="examWizard\.goToStep3\(\)".*?</button>)', r'\1\n' + step4_html, html)
    # Actually wait, step 3 is where the button is.
    html = html.replace('<button onclick="examWizard.startExam()" style="width:100%; padding:16px; background:var(--primary); color:#fff; font-size:18px; font-weight:bold; border:none; border-radius:12px; cursor:pointer; margin-top:20px;">🚀 بدء الامتحان</button>', '<button onclick="examWizard.goToStep4()" style="width:100%; padding:16px; background:var(--primary); color:#fff; font-size:18px; font-weight:bold; border:none; border-radius:12px; cursor:pointer; margin-top:20px;">التالي ⬅️</button>')
    
# Update practice-active-state
if 'quiz-timer-bar' not in html:
    html = html.replace('<h3 id="quiz-question-text"', '<div id="quiz-timer-bar" style="height:4px; background:var(--primary); width:100%; margin-bottom:12px; border-radius:2px; transition: width 1s linear; display:none;"></div>\n                <h3 id="quiz-question-text"')
    
    explanation_html = '''
            <div id="quiz-explanation-container" style="display:none; margin-top:20px; text-align:right;">
                <div id="quiz-explanation-content"></div>
                <div style="display:flex; justify-content:space-between; margin-top:16px;">
                    <button onclick="quizEngine.reportQuestion()" style="background:#fee2e2; color:#ef4444; border:none; padding:10px 16px; border-radius:8px; font-weight:bold; cursor:pointer;">⚠️ إبلاغ عن خطأ</button>
                    <button onclick="quizEngine.nextQuestion()" style="background:var(--primary); color:#fff; border:none; padding:10px 24px; border-radius:8px; font-weight:bold; cursor:pointer;">التالي ⬅️</button>
                </div>
            </div>
'''
    html = html.replace('<!-- Options injected via JS -->\n            </div>', '<!-- Options injected via JS -->\n            </div>\n' + explanation_html)

# Add Report Modal
report_modal = '''
    <div id="report-modal" class="modal-overlay" style="display:none;">
        <div class="modal-content" style="text-align:right;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <button onclick="quizEngine.closeReportModal()" style="background:transparent; border:none; font-size:24px; cursor:pointer; color:var(--text-2);">✕</button>
                <h3 style="margin:0; font-size:20px; color:var(--text);">إبلاغ عن خطأ ⚠️</h3>
            </div>
            
            <p style="color:var(--text-2); margin-bottom:15px; font-size:14px;">ما هو نوع الخطأ في هذا السؤال؟</p>
            
            <select id="report-type" style="width:100%; padding:12px; border-radius:8px; border:1px solid var(--surface-2); background:var(--bg); margin-bottom:15px;">
                <option value="orthographe">خطأ إملائي</option>
                <option value="faux">إجابة خاطئة</option>
                <option value="technique">مشكلة تقنية / السؤال غير واضح</option>
                <option value="autre">أخرى</option>
            </select>
            
            <textarea id="report-details" rows="3" placeholder="تفاصيل إضافية (اختياري)..." style="width:100%; padding:12px; border-radius:8px; border:1px solid var(--surface-2); background:var(--bg); margin-bottom:20px; font-family:inherit; resize:vertical;"></textarea>
            
            <button onclick="quizEngine.submitReport()" style="width:100%; padding:14px; background:var(--primary); color:#fff; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">إرسال التقرير 🚀</button>
        </div>
    </div>
'''
if 'id="report-modal"' not in html:
    html = html.replace('</body>', report_modal + '\n</body>')

with open('dashboard/reader.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('reader.html updated')

# 2. Update exam.js
with open('dashboard/exam.js', 'r', encoding='utf-8') as f:
    exam_js = f.read()

if 'goToStep4()' not in exam_js:
    exam_js = exam_js.replace('startExam() {', '''goToStep4() {
        document.getElementById('exam-step-3').style.display = 'none';
        document.getElementById('exam-step-4').style.display = 'block';
    },

    startExam() {''')
    exam_js = exam_js.replace("limit: limit", "limit: limit,\n            timer: parseInt(document.getElementById('exam-timer-mode').value),\n            correctionMode: document.getElementById('exam-correction-mode').value")
    
with open('dashboard/exam.js', 'w', encoding='utf-8') as f:
    f.write(exam_js)
print('exam.js updated')

