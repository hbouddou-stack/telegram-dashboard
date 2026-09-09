import io
import re

with io.open('dashboard/ask.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_tab_new = """        <!-- NEW TICKET TAB -->
        <div class="tab-content" id="tab-new" style="padding-bottom:100px;">
            
            <div id="support-form">
                <div class="header">
                    <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(46,204,113,0.12); border:1px solid rgba(46,204,113,0.3); border-radius:20px; padding:6px 14px; font-size:0.82rem; color:#2ecc71; margin-bottom:12px;">
                        <span style="width:8px; height:8px; border-radius:50%; background:#2ecc71; box-shadow:0 0 8px #2ecc71; display:inline-block;"></span>
                        فريق الدعم متصل حالياً — متوسط سرعة الرد: 15 دقيقة
                    </div>
                    <div class="header-icon">&#129302;</div>
                    <h1>مركز الدعم الذكي</h1>
                    <p class="subtitle" id="step-subtitle">ما هو نوع المشكلة التي تواجهها؟</p>
                    <div class="step-indicator">
                        <div class="dot active" id="dot-1"></div>
                        <div class="dot" id="dot-2"></div>
                        <div class="dot" id="dot-3"></div>
                    </div>
                </div>
                <div class="step-container active" id="step-1">
                    <div class="grid-cards" id="theme-grid"></div>
                </div>
                <div class="step-container" id="step-2">
                    <div class="grid-cards" id="subtheme-grid"></div>
                    <button class="btn-secondary" onclick="goToStep(1)">&#128281; رجوع</button>
                </div>
                <div class="step-container" id="step-3">
                    <div class="input-group">
                        <label>اشرح مشكلتك بالتفصيل:</label>
                        <textarea id="message" placeholder="اكتب هنا كافة التفاصيل التي قد تساعدنا في حل مشكلتك..." oninput="livePredictiveFaqSearch(this.value)"></textarea>
                    </div>
                    <!-- Live Predictive FAQ Container -->
                    <div id="predictive-faq-box" style="display:none; background:var(--surface); border:1px solid var(--accent); border-radius:12px; padding:12px; margin-bottom:15px;">
                        <div style="font-size:0.8rem; color:var(--accent); margin-bottom:8px;">💡 هل تقصد أحد هذه الأسئلة؟</div>
                        <div id="predictive-faq-list" style="display:flex; flex-direction:column; gap:8px;"></div>
                    </div>

                    <div class="input-group">
                        <label>إرفاق صورة أو ملف (اختياري):</label>
                        <input type="file" id="attachment" accept="image/*,.pdf" style="padding:10px; background:var(--surface); border:1px dashed rgba(255,255,255,0.2); border-radius:12px; color:var(--text-1); width:100%; box-sizing:border-box;">
                    </div>
                    <div style="display:flex; gap:10px;">
                        <button class="btn-secondary" onclick="goToStep(2)">&#128281; رجوع</button>
                        <button class="btn-primary" id="btn-submit" onclick="submitTicket()">&#128640; إرسال</button>
                    </div>
                </div>
            </div>"""

new_tab_new = """        <!-- NEW TICKET TAB -->
        <div class="tab-content" id="tab-new" style="padding-bottom:100px;">
            
            <div id="support-form">
                <div class="header" style="margin-bottom: 25px;">
                    <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(46,204,113,0.12); border:1px solid rgba(46,204,113,0.3); border-radius:20px; padding:6px 14px; font-size:0.82rem; color:#2ecc71; margin-bottom:12px;">
                        <span style="width:8px; height:8px; border-radius:50%; background:#2ecc71; box-shadow:0 0 8px #2ecc71; display:inline-block;"></span>
                        المساعد الذكي متصل حالياً
                    </div>
                    <div class="header-icon">&#129302;</div>
                    <h1>كيف يمكنني مساعدتك؟</h1>
                    <p class="subtitle" id="step-subtitle">اكتب سؤالك وسأحاول إجابتك فوراً، أو تحويلك للإدارة.</p>
                </div>
                
                <div class="step-container active" id="step-3">
                    <div class="input-group">
                        <textarea id="message" placeholder="اكتب رسالتك أو مشكلتك هنا..." oninput="livePredictiveFaqSearch(this.value)" style="min-height: 120px; font-size: 1.05rem;"></textarea>
                    </div>
                    <!-- Live Predictive FAQ Container -->
                    <div id="predictive-faq-box" style="display:none; background:var(--surface); border:1px solid var(--accent); border-radius:12px; padding:12px; margin-bottom:15px;">
                        <div style="font-size:0.8rem; color:var(--accent); margin-bottom:8px;">💡 هل تقصد أحد هذه الأسئلة؟</div>
                        <div id="predictive-faq-list" style="display:flex; flex-direction:column; gap:8px;"></div>
                    </div>

                    <div class="input-group">
                        <label style="font-size:0.85rem; color:var(--text-2);">إرفاق صورة أو ملف (اختياري):</label>
                        <input type="file" id="attachment" accept="image/*,.pdf" style="padding:10px; background:var(--surface); border:1px dashed rgba(255,255,255,0.2); border-radius:12px; color:var(--text-1); width:100%; box-sizing:border-box;">
                    </div>
                    <div style="display:flex; gap:10px;">
                        <button class="btn-primary" id="btn-submit" onclick="submitTicket()" style="width:100%; padding:14px; font-size:1.1rem;">&#128640; إرسال</button>
                    </div>
                </div>
            </div>"""

if old_tab_new in html:
    html = html.replace(old_tab_new, new_tab_new)
else:
    print("Could not find old HTML to replace! Check exact string.")

# Let's ensure selectedTheme and selectedSubtheme fallback properly in submitTicket
old_submit = """async function submitTicket() {
            const customTitleInput = document.getElementById('custom-ticket-title');"""

new_submit = """async function submitTicket() {
            if (typeof selectedTheme === 'undefined' || !selectedTheme) selectedTheme = 'عام';
            if (typeof selectedSubtheme === 'undefined' || !selectedSubtheme) selectedSubtheme = 'سؤال';
            const customTitleInput = document.getElementById('custom-ticket-title');"""

if old_submit in html:
    html = html.replace(old_submit, new_submit)

with io.open('dashboard/ask.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('UI simplified')
