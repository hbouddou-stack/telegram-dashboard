import re

with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

js_content = r'''
const supportFlowIndex = {
    category: '', subcategory: '', message: '', currentOptsId: '',
    selectCategory: function(cat) {
        this.category = cat;
        this.addMessage(cat, 'user');
        document.getElementById('support-step-1-options-index').style.display = 'none';
        
        setTimeout(() => {
            let subText = ''; let subBtns = '';
            if(cat === 'تقنية') {
                subText = 'هل المشكلة متعلقة بـ:';
                subBtns = 
                    <button onclick="supportFlowIndex.selectSubcategory('الفيديو لا يعمل')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">الفيديو لا يعمل</button>
                    <button onclick="supportFlowIndex.selectSubcategory('لا يوجد صوت')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">لا يوجد صوت</button>
                    <button onclick="supportFlowIndex.selectSubcategory('مشكلة في التطبيق')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">مشكلة في التطبيق</button>
                ;
            } else if(cat === 'إدارية') {
                subText = 'المرجو تحديد المشكلة:';
                subBtns = 
                    <button onclick="supportFlowIndex.selectSubcategory('تجديد الاشتراك')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">تجديد الاشتراك</button>
                    <button onclick="supportFlowIndex.selectSubcategory('مشكلة في الدفع')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">مشكلة في الدفع</button>
                ;
            } else {
                subText = 'هل المشكلة في:';
                subBtns = 
                    <button onclick="supportFlowIndex.selectSubcategory('فهم الدرس')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">فهم الدرس</button>
                    <button onclick="supportFlowIndex.selectSubcategory('سؤال حول الاختبار')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">سؤال حول الاختبار</button>
                ;
            }
            this.addMessage(subText, 'bot');
            const optsId = 'subopts-idx-' + Date.now();
            const optsHtml = <div id="" style="display: flex; flex-wrap: wrap; gap: 8px; align-self: flex-start; max-width: 85%;"></div>;
            document.getElementById('support-chat-history-index').insertAdjacentHTML('beforeend', optsHtml);
            this.currentOptsId = optsId;
            this.scrollToBottom();
        }, 500);
    },
    selectSubcategory: function(sub) {
        this.subcategory = sub;
        this.addMessage(sub, 'user');
        if(this.currentOptsId) { document.getElementById(this.currentOptsId).style.display = 'none'; }
        
        setTimeout(() => {
            let tip = '';
            if (sub === 'الفيديو لا يعمل' || sub === 'لا يوجد صوت') { tip = '💡 نصيحة سريعة: 90% من مشاكل الفيديو تُحل بمجرد تحديث الصفحة أو مسح ذاكرة التخزين المؤقت (Cache). هل تريد تجربة ذلك؟<br><br>'; }
            else if (sub === 'مشكلة في الدفع' || sub === 'تجديد الاشتراك') { tip = '💡 ملاحظة: تفعيل الاشتراكات قد يأخذ ما بين 5 إلى 15 دقيقة للظهور في التطبيق بعد الدفع.<br><br>'; }
            else if (sub === 'فهم الدرس') { tip = '💡 هل تعلم؟ يمكنك استخدام "الخريطة الذهنية" أو "ملخص الدرس" المتوفرة في قائمة الدرس للحصول على فكرة أوضح قبل طرح السؤال.<br><br>'; }
            this.addMessage(tip + 'إذا كانت المشكلة مستمرة، يرجى كتابة التفاصيل أدناه:', 'bot');
            document.getElementById('support-chat-input-area-index').style.display = 'flex';
            document.getElementById('support-chat-input-index').focus();
            this.scrollToBottom();
        }, 500);
    },
    sendMessage: function() {
        const inp = document.getElementById('support-chat-input-index');
        const text = inp.value.trim();
        if(!text) return;
        this.message = text; inp.value = '';
        document.getElementById('support-chat-input-area-index').style.display = 'none';
        this.addMessage(text, 'user');
        setTimeout(() => {
            const typingId = 'typing-idx-' + Date.now();
            const typingHtml = <div id="" style="align-self: flex-start; background: white; padding: 12px 16px; border-radius: 16px 16px 0 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); display: flex; gap: 4px; align-items: center;"><span style="width: 8px; height: 8px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both;"></span><span style="width: 8px; height: 8px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.2s;"></span><span style="width: 8px; height: 8px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.4s;"></span><span style="font-size: 12px; color: #6b7280; margin-right: 8px;">جاري البحث...</span></div>;
            document.getElementById('support-chat-history-index').insertAdjacentHTML('beforeend', typingHtml);
            this.scrollToBottom();
            setTimeout(() => {
                document.getElementById(typingId).remove();
                this.showFaqAndEscalate();
            }, 2500);
        }, 400);
    },
    showFaqAndEscalate: function() {
        this.addMessage(للأسف لم أجد إجابة مباشرة. يمكنك تصفح الأسئلة الشائعة أو إرسال المشكلة للإدارة., 'bot');
        const faqs = <div style="background: white; border-radius: 12px; padding: 10px; align-self: flex-start; width: 100%; max-width: 90%; margin-top: 5px;"><details style="padding: 8px; border-bottom: 1px solid #f3f4f6;"><summary style="font-weight: bold; cursor: pointer;">كيف أجد ملخص الدرس؟</summary><p style="margin-top: 8px; font-size: 13px;">الملخص متوفر في قائمة الدرس عبر زر (الخريطة الذهنية).</p></details></div><div style="align-self: center; margin-top: 15px;"><button onclick="supportFlowIndex.escalateToAdmin()" style="background: #ef4444; color: white; border: none; padding: 12px 20px; border-radius: 24px; font-weight: bold; cursor: pointer;">إرسال المشكلة إلى الإدارة 📩</button></div>;
        document.getElementById('support-chat-history-index').insertAdjacentHTML('beforeend', faqs);
        this.scrollToBottom();
    },
    escalateToAdmin: function() {
        event.target.style.display = 'none';
        this.addMessage("إرسال المشكلة إلى الإدارة", "user");
        setTimeout(() => { this.addMessage("✅ تمت إحالة طلبك بنجاح. ستتلقى رداً في صندوق الوارد.", "bot"); }, 800);
    },
    addMessage: function(text, sender) {
        const isBot = sender === 'bot';
        const bg = isBot ? 'white' : 'var(--primary)';
        const color = isBot ? 'var(--text-1)' : 'white';
        const align = isBot ? 'flex-start' : 'flex-end';
        const radius = isBot ? '16px 16px 0 16px' : '16px 16px 16px 0';
        const html = <div style="align-self: ; background: ; color: ; padding: 12px 16px; border-radius: ; box-shadow: 0 1px 2px rgba(0,0,0,0.1); max-width: 85%;"></div>;
        document.getElementById('support-chat-history-index').insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();
    },
    scrollToBottom: function() { const hist = document.getElementById('support-chat-history-index'); hist.scrollTop = hist.scrollHeight; }
};
'''

html = html.replace('</script>', js_content + '\n</script>')

with open('dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
