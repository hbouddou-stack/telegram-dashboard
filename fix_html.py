import re

with open('dashboard/reader.html', 'r', encoding='utf-8') as f:
    html = f.read()

# I need to insert exam-step-4 after exam-step-3
step4 = '''
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
              </div>
'''

if 'id="exam-step-4"' not in html:
    html = html.replace('</button>\n              </div>\n          </div>', '</button>\n              </div>\n' + step4 + '\n          </div>')
    with open('dashboard/reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
