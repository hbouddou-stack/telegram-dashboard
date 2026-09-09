import io
import re

with io.open('dashboard/ask.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the entire support-form div with the new Chat-like UI
new_support_form = """<div id="support-form">
                <div class="header" style="margin-bottom: 25px;">
                    <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(46,204,113,0.12); border:1px solid rgba(46,204,113,0.3); border-radius:20px; padding:6px 14px; font-size:0.82rem; color:#2ecc71; margin-bottom:12px;">
                        <span style="width:8px; height:8px; border-radius:50%; background:#2ecc71; box-shadow:0 0 8px #2ecc71; display:inline-block;"></span>
                        المساعد الذكي متصل حالياً
                    </div>
                    <div class="header-icon">&#129302;</div>
                    <h1>كيف يمكنني مساعدتك؟</h1>
                    <p class="subtitle" id="step-subtitle">اكتب سؤالك وسأحاول إجابتك فوراً، أو تحويلك للإدارة.</p>
                </div>
                
                <div class="step-container active" id="step-3" style="display:block;">
                    <div class="input-group">
                        <textarea id="message" placeholder="اكتب رسالتك أو مشكلتك هنا..." oninput="livePredictiveFaqSearch(this.value)" style="min-height: 120px; font-size: 1.05rem;"></textarea>
                    </div>
                    
                    <!-- Live Predictive FAQ Container -->
                    <div id="predictive-faq-box" style="display:none; margin-top:12px; background:rgba(241,196,15,0.06); border:1px solid rgba(241,196,15,0.25); border-radius:14px; padding:14px;">
                        <div style="font-size:0.88rem; font-weight:bold; color:var(--accent); margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                            <span>💡</span> هل تجد إجابتك هنا مباشرة؟
                        </div>
                        <div id="predictive-faq-results"></div>
                    </div>

                    <div class="input-group" style="margin-top:10px;">
                        <label style="font-size:0.85rem; color:var(--text-2);">إرفاق صورة أو ملف (اختياري):</label>
                        <input type="file" id="attachment" accept="image/*,.pdf" style="padding:10px; background:var(--surface); border:1px dashed rgba(255,255,255,0.2); border-radius:12px; color:var(--text-1); width:100%; box-sizing:border-box;">
                    </div>
                    <div style="display:flex; gap:10px; margin-top:15px;">
                        <button class="btn-primary" id="btn-submit" onclick="submitTicket()" style="width:100%; padding:14px; font-size:1.1rem;">&#128640; إرسال</button>
                    </div>
                </div>
            </div>"""

html = re.sub(r'<div id=\"support-form\">.*?</div>\s*<!-- SUCCESS SCREEN -->', new_support_form + '\n            <!-- SUCCESS SCREEN -->', html, flags=re.DOTALL)

# Ensure selectedTheme is handled
old_submit = """async function submitTicket() {"""
new_submit = """async function submitTicket() {
            if (typeof selectedTheme === 'undefined' || !selectedTheme) selectedTheme = 'عام';
            if (typeof selectedSubtheme === 'undefined' || !selectedSubtheme) selectedSubtheme = 'سؤال';"""
html = html.replace(old_submit, new_submit)

with io.open('dashboard/ask.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('UI simplified successfully')
