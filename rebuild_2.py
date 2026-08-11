import re

with open('dashboard/reader.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Timer bar, Error container, and report modal into reader.html
timer_bar_html = '''<div id="quiz-question-container" style="background:var(--surface); border-radius:16px; padding:24px; box-shadow:0 4px 15px rgba(0,0,0,0.05); margin-bottom:24px; text-align:center;">
                <div id="quiz-timer-bar" style="height:4px; background:var(--primary); width:100%; margin-bottom:12px; border-radius:2px; display:none;"></div>'''
html = html.replace('<div id="quiz-question-container" style="background:var(--surface); border-radius:16px; padding:24px; box-shadow:0 4px 15px rgba(0,0,0,0.05); margin-bottom:24px; text-align:center;">', timer_bar_html)

explanation_html = '''<div id="quiz-options-container" style="display:flex; flex-direction:column; gap:12px;">
                <!-- Options injected via JS -->
            </div>

            <div id="quiz-explanation-container" style="display:none; margin-top:20px; text-align:right;">
                <div id="quiz-explanation-content"></div>
                <div style="display:flex; justify-content:space-between; margin-top:16px;">
                    <button onclick="quizEngine.reportQuestion()" style="background:#fee2e2; color:#ef4444; border:none; padding:10px 16px; border-radius:8px; font-weight:bold; cursor:pointer;">⚠️ إبلاغ عن خطأ</button>
                    <button onclick="quizEngine.nextQuestion()" style="background:var(--primary); color:#fff; border:none; padding:10px 24px; border-radius:8px; font-weight:bold; cursor:pointer;">التالي ⬅️</button>
                </div>
            </div>'''
html = html.replace('''<div id="quiz-options-container" style="display:flex; flex-direction:column; gap:12px;">
                <!-- Options injected via JS -->
            </div>''', explanation_html)

errors_container = '''
            <div id="quiz-errors-container" style="display:none; text-align:right; margin-bottom:24px; padding:16px; background:var(--surface); border-radius:12px; border:1px solid #ef4444;">
                <h3 style="color:#ef4444; margin-bottom:12px; font-size:18px;">الأسئلة التي أخطأت فيها:</h3>
                <div id="quiz-errors-list"></div>
            </div>
'''
html = html.replace('<button onclick="quizEngine.start()" style="background:var(--primary);', errors_container + '\n            <button onclick="quizEngine.start()" style="background:var(--primary);')

step4_html = '''</button>
              </div>
              <div id="exam-step-4" style="display:none;">
                  <h3 style="color:var(--text-2); margin-bottom:12px; font-size:16px;">4. إعدادات الاختبار</h3>
                  
                  <label style="display:block; margin-bottom:8px; font-weight:bold; color:var(--text);">الوقت لكل سؤال:</label>
                  <select id="exam-timer-mode" style="width:100%; padding:14px; border-radius:12px; border:1px solid var(--border-color); font-size:16px; margin-bottom:20px;">
                      <option value="0">بدون وقت</option>
                      <option value="15">15 ثانية</option>
                      <option value="30">30 ثانية</option>
                      <option value="60">60 ثانية</option>
                  </select>
                  
                  <label style="display:block; margin-bottom:8px; font-weight:bold; color:var(--text);">وضع التصحيح:</label>
                  <select id="exam-correction-mode" style="width:100%; padding:14px; border-radius:12px; border:1px solid var(--border-color); font-size:16px; margin-bottom:24px;">
                      <option value="instant">تصحيح فوري (مع الشرح)</option>
                      <option value="end">تصحيح في النهاية (مثل الامتحان)</option>
                  </select>
                  
                  <button id="exam-final-start-btn" onclick="examWizard.startQuiz()" style="background:var(--primary); color:white; border:none; padding:16px 32px; border-radius:12px; font-size:18px; font-weight:bold; width:100%; cursor:pointer; box-shadow: 0 4px 15px rgba(79,70,229,0.3);">ابدأ الاختبار 🚀</button>
              </div>'''
html = html.replace('ابدأ التدريب 🚀</button>\n              </div>', step4_html)

# Also fix the startQuiz button in step 3 to goToStep4 instead
html = html.replace('onclick="examWizard.startQuiz()"', 'onclick="examWizard.goToStep4()"', 1) # Only the first one which is in step 3

modal_html = '''
    <div id="report-modal" class="modal-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; align-items:center; justify-content:center;">
        <div class="modal-content" style="background:var(--surface); padding:24px; border-radius:16px; width:90%; max-width:400px; text-align:right;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <button onclick="quizEngine.closeReportModal()" style="background:transparent; border:none; font-size:24px; cursor:pointer; color:var(--text-2);">✕</button>
                <h3 style="margin:0; font-size:20px; color:var(--text);">إبلاغ عن خطأ ⚠️</h3>
            </div>
            
            <p style="color:var(--text-2); margin-bottom:15px; font-size:14px;">ما هو نوع الخطأ في هذا السؤال؟</p>
            
            <select id="report-type" style="width:100%; padding:12px; border-radius:8px; border:1px solid var(--border-color); background:var(--bg); margin-bottom:15px; font-size:16px;">
                <option value="orthographe">خطأ إملائي</option>
                <option value="faux">إجابة خاطئة</option>
                <option value="technique">مشكلة تقنية / السؤال غير واضح</option>
                <option value="autre">أخرى</option>
            </select>
            
            <textarea id="report-details" rows="3" placeholder="تفاصيل إضافية (اختياري)..." style="width:100%; padding:12px; border-radius:8px; border:1px solid var(--border-color); background:var(--bg); margin-bottom:20px; font-family:inherit; resize:vertical; font-size:16px;"></textarea>
            
            <button onclick="quizEngine.submitReport()" style="width:100%; padding:14px; background:var(--primary); color:#fff; border:none; border-radius:8px; font-weight:bold; cursor:pointer; font-size:16px;">إرسال التقرير 🚀</button>
        </div>
    </div>

</body>'''
html = html.replace('</body>', modal_html)

with open('dashboard/reader.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("reader.html patched safely")
