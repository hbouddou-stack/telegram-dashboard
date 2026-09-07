async function submitTicket() {
            const customTitleInput = document.getElementById('custom-ticket-title');
            if (selectedSubtheme === 'مشكلة أخرى' && customTitleInput) {
                const ct = customTitleInput.value.trim();
                if (!ct) { alert("يرجى كتابة عنوان مختصر للموضوع."); return; }
                selectedSubtheme = ct;
            }
            const msg = document.getElementById('message').value.trim();
            if (!msg) { alert("يرجى كتابة رسالتك بوضوح."); return; }
            const btn = document.getElementById('btn-submit');
            btn.textContent = "جاري البحث...";
            btn.disabled = true;
            try {
                const ragRes = await fetch(`${BOT_BASE}/api/support/rag_check`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ theme: selectedTheme, subtheme: selectedSubtheme, message: msg })
                });
                const ragData = await ragRes.json();
                if (ragData.found) {
                    document.getElementById('rag-answer-text').innerText = ragData.answer;
                    goToStep(4);
                    btn.textContent = "&#128640; إرسال";
                    btn.disabled = false;
                    return;
                }
            } catch (e) { console.error("RAG Error", e); }
            escalateTicket(false);
        }

        async function resolveTicket() {
            const msg = document.getElementById('message').value.trim();
            const tid = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.id : null) || null;
            const uname = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.username : "") || "";
            const fname = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.first_name : "") || "";
            try {
                await fetch(`${BOT_BASE}/api/support`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ theme: selectedTheme, subtheme: selectedSubtheme, message: msg, telegram_id: tid, username: uname, first_name: fname, rag_failed: false, auto_resolved: true })
                });
            } catch(e) { console.error(e); }
            document.getElementById('support-form').style.display = 'none';
            document.getElementById('success-msg').innerText = "يسعدنا أن المشكلة حُلت! تم حفظ الاستفسار لغرض التحسين.";
            document.getElementById('success-screen').style.display = 'block';
        }

        async function escalateTicket(ragFailed = true) {
            const msg = document.getElementById('message').value.trim();
            const tid = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.id : null) || null;
            const username = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.username : "") || "";
            const first_name = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.first_name : "") || "";
            
            const fileInput = document.getElementById('attachment');
            let initialFileData = null;
            let initialFileName = null;
            
            if (fileInput && fileInput.files && fileInput.files[0]) {
                const file = fileInput.files[0];
                initialFileName = file.name;
                initialFileData = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.onerror = () => resolve(null);
                    reader.readAsDataURL(file);
                });
            }
            
            try {
                await fetch(`${BOT_BASE}/api/support`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        theme: selectedTheme, 
                        subtheme: selectedSubtheme, 
                        message: msg, 
                        telegram_id: tid, 
                        username, 
                        first_name, 
                        rag_failed: ragFailed,
                        file_data: initialFileData,
                        file_name: initialFileName
                    })
                });
                document.getElementById('support-form').style.display = 'none';
                document.getElementById('success-screen').style.display = 'block';
            } catch (e) {
                alert("حدث خطأ في الإرسال. يرجى المحاولة لاحقاً.");
                const btn = document.getElementById('btn-submit');
                if (btn) { btn.textContent = "&#128640; إرسال"; btn.disabled = false; }
                goToStep(3);
            }
        }

        // Analytics Tracking
        async function trackAnalytics(event_type, keyword = '', has_results = false, tab_name = '') {
            const uid = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.id : null) || 0;
            try {
                await fetch('/api/analytics/track', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ event_type, keyword, has_results, tab_name, user_id: uid })
                });
            } catch (e) { console.error('Analytics error:', e); }
        }

        // Tabs Logic
        
        
// ========================
// STORIES & MEDIATHEQUE ENGINE
// ========================
const ACADEMY_STORIES = [
    {
        title: "شرح المنصة",
        icon: "🗺️",
        slides: [
            { icon: "🏛️", title: "أهلاً بك في أُسوة!", text: "منصتك التعليمية الرائدة لدراسة العلوم الشرعية وتجويد القرآن الكريم بمنهجية عصرية ميسرة.", btnText: "التالي ➔", action: "next" },
            { icon: "📚", title: "تصفح المقررات", text: "يمكنك متابعة المحاضرات والملخصات من أي مكان، والاطلاع على الخطة الدراسية السنوية.", btnText: "التالي ➔", action: "next" },
            { icon: "🗺️", title: "دليل الطالب التفاعلي", text: "استخدم دليل المنصة للتعرف على جميع الميزات والوصول السريع للأقسام.", btnText: "فتح الدليل 📖", action: "guide" }
        ]
    },
    {
        title: "تفعيل الحساب",
        icon: "💳",
        slides: [
            { icon: "💳", title: "طرق الدفع المعتمدة", text: "نوفر الدفع عبر البطاقة البنكية، التحويل المباشر، أو وكالات كاش بلس / وفاكاش.", btnText: "التالي ➔", action: "next" },
            { icon: "📸", title: "إرسال وصل التحويل", text: "قم بتصوير وصل التحويل وإرفاقه في تذكرة دعم ليتم التحقق منه وتفعيل حسابك فوراً.", btnText: "التالي ➔", action: "next" },
            { icon: "⚡", title: "تفعيل فوري", text: "يقوم فريق الدعم بمطابقة الوصل وتفعيل اشتراكك خلال دقائق معدودة!", btnText: "طرح استفسار ✍️", action: "ask" }
        ]
    },
    {
        title: "تشغيل الدروس",
        icon: "🎥",
        slides: [
            { icon: "🎬", title: "مشاهدة الدروس بدقة HD", text: "تتوفر المحاضرات بجودات متعددة لتناسب سرعة الإنترنت لديك على الهاتف.", btnText: "التالي ➔", action: "next" },
            { icon: "📑", title: "تحميل الملخصات", text: "أسفل كل درس ستجد زر تحميل الملخص بصيغة PDF للطباعة والمراجعة.", btnText: "التالي ➔", action: "next" },
            { icon: "🎧", title: "التسجيلات الصوتية", text: "يمكنك الاستماع للتلاوات والشروحات الصوتية في أي وقت ومن دون انقطاع.", btnText: "الأسئلة الشائعة 📚", action: "faq" }
        ]
    },
    {
        title: "الاختبارات",
        icon: "📝",
        slides: [
            { icon: "✍️", title: "نظام الامتحانات الذكي", text: "اختبر فهمك بعد كل وحدة دراسية بأسئلة تفاعلية ومؤقت زمني دقيق.", btnText: "التالي ➔", action: "next" },
            { icon: "📊", title: "النتيجة والتصحيح النموذجي", text: "تظهر نتيجتك فوراً مع توضيح الإجابات الصحيحة وشرح أسبابها.", btnText: "التالي ➔", action: "next" },
            { icon: "🏆", title: "بنك الأخطاء والمراجعة", text: "تُحفظ الأسئلة التي أخطأت فيها تلقائياً لمساعدتك على مراجعتها لاحقاً!", btnText: "فهمت الفكرة 👍", action: "close" }
        ]
    },
    {
        title: "الشهادات",
        icon: "🎓",
        slides: [
            { icon: "🎯", title: "شروط الحصول على الشهادة", text: "إكمال 80% على الأقل من المحاضرات واجتياز الاختبار النهائي بنجاح.", btnText: "التالي ➔", action: "next" },
            { icon: "📜", title: "شهادة معتمدة برقم تسلسلي", text: "تحصل على شهادة رقمية موثقة يمكن طباعتها ومشاركتها بكل فخر.", btnText: "إغلاق الشرح ✨", action: "close" }
        ]
    }
];

let currentStoryIdx = 0;
let currentSlideIdx = 0;
let storySlideTimer = null;
const SLIDE_DURATION = 5000;
