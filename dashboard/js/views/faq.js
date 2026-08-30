// faq.js - FAQ / RAG Knowledge Base Manager

export function initFaqView(container) {
    container.innerHTML = `
        <section class="view active module-view" style="position:relative; background: var(--bg); overflow-y: auto;">
            <header class="app-header" style="border-bottom: 1px solid var(--border);">
                <div class="header-left">
                    <button class="hamburger-btn" onclick="toggleSidebar()">☰</button>
                    <div class="header-titles">
                        <h1>🧠 مدير الذكاء الاصطناعي (الأسئلة الشائعة)</h1>
                        <span class="header-subtitle">قاعدة معرفة الردود التلقائية</span>
                    </div>
                </div>
                <button class="btn-primary" onclick="alert('سيتم إضافة سؤال جديد قريباً')" style="padding: 8px 15px; border-radius: 20px; font-weight: bold; display: flex; gap: 5px; align-items: center; border: none; background: var(--accent); color: white; cursor: pointer;">
                    <span>+</span> إضافة سؤال
                </button>
            </header>
            
            <div style="padding: 20px; max-width: 900px; margin: 0 auto;">
                <div class="alert-info" style="background: rgba(52, 152, 219, 0.1); border: 1px solid #3498db; padding: 15px; border-radius: 8px; margin-bottom: 20px; color: var(--text-1);">
                    💡 <strong>كيف يعمل؟</strong> الإجابات هنا تستخدم من قبل "الطيار الآلي" (Copilot) لاقتراح ردود فورية عليك عند فتح التذاكر.
                </div>

                <div class="faq-category" style="margin-bottom: 30px;">
                    <h2 style="color: var(--accent); margin-bottom: 15px; border-bottom: 2px solid var(--border); padding-bottom: 5px;">⚙️ القسم التقني (Tech)</h2>
                    
                    <div class="faq-card" style="background: var(--surface-solid); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; padding: 15px;">
                        <div style="font-weight: bold; color: var(--text-1); margin-bottom: 10px;">س: لا أستطيع الدخول إلى حسابي / نسيت كلمة المرور</div>
                        <div style="color: var(--text-muted); background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px;">
                            ج: مرحباً، يمكنك إعادة ضبط كلمة المرور من خلال النقر على "نسيت كلمة المرور" في صفحة الدخول، وستصلك رسالة عبر التلغرام لتعيين كلمة جديدة.
                        </div>
                        <div style="margin-top: 10px; text-align: left;">
                            <button class="btn-icon" style="color: #3498db; font-size: 0.9rem;">✏️ تعديل</button>
                            <button class="btn-icon" style="color: #e74c3c; font-size: 0.9rem;">🗑️ حذف</button>
                        </div>
                    </div>
                    
                    <div class="faq-card" style="background: var(--surface-solid); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; padding: 15px;">
                        <div style="font-weight: bold; color: var(--text-1); margin-bottom: 10px;">س: الفيديو لا يعمل أو يتقطع</div>
                        <div style="color: var(--text-muted); background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px;">
                            ج: يرجى التأكد من جودة اتصالك بالإنترنت. إذا استمرت المشكلة، حاول مسح ذاكرة التخزين المؤقت (Cache) للمتصفح أو استخدام متصفح آخر مثل Chrome.
                        </div>
                        <div style="margin-top: 10px; text-align: left;">
                            <button class="btn-icon" style="color: #3498db; font-size: 0.9rem;">✏️ تعديل</button>
                            <button class="btn-icon" style="color: #e74c3c; font-size: 0.9rem;">🗑️ حذف</button>
                        </div>
                    </div>
                </div>

                <div class="faq-category" style="margin-bottom: 30px;">
                    <h2 style="color: #2ecc71; margin-bottom: 15px; border-bottom: 2px solid var(--border); padding-bottom: 5px;">💳 القسم المالي (Finance)</h2>
                    
                    <div class="faq-card" style="background: var(--surface-solid); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; padding: 15px;">
                        <div style="font-weight: bold; color: var(--text-1); margin-bottom: 10px;">س: هل يمكنني تقسيط رسوم الدورة؟</div>
                        <div style="color: var(--text-muted); background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px;">
                            ج: نعم، نوفر خطط تقسيط مرنة. يرجى تزويدنا برقمك التسلسلي وسنقوم بتفعيل خيار التقسيط في حسابك فوراً.
                        </div>
                        <div style="margin-top: 10px; text-align: left;">
                            <button class="btn-icon" style="color: #3498db; font-size: 0.9rem;">✏️ تعديل</button>
                            <button class="btn-icon" style="color: #e74c3c; font-size: 0.9rem;">🗑️ حذف</button>
                        </div>
                    </div>
                </div>

            </div>
        </section>
    `;
}
