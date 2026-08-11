import re

# PATCH HTML
html_file = 'dashboard/reader.html'
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

practice_tab_html = """
    <!-- TAB: PRACTICE -->
    <div class="tab-panel" id="tab-practice" style="background: var(--bg); min-height: 100vh; padding-bottom: 80px;">
        <div id="practice-empty-state" style="padding: 40px 20px; text-align: center;">
            <div style="font-size:48px; margin-bottom:16px;">🎯</div>
            <h3 style="color:var(--text); font-weight:700; margin-bottom:8px;">التدريبات والمراجعة</h3>
            <p style="color:var(--text-3); font-size:14px; margin-bottom:24px;">اختر درساً للبدء في الاختبار والتأكد من فهمك.</p>
            <button onclick="switchTab('syllabus', this)" style="background:var(--primary); color:white; border:none; padding:12px 24px; border-radius:12px; font-weight:bold; cursor:pointer;">تصفح المقررات</button>
        </div>
        
        <div id="practice-loading" style="display:none; padding: 40px 20px; text-align: center;">
            <div class="spinner" style="margin: 0 auto 20px auto; width:40px; height:40px; border:4px solid var(--border-color); border-top:4px solid var(--primary); border-radius:50%; animation:spin 1s linear infinite;"></div>
            <p style="color:var(--text-2);">جاري تحميل الأسئلة...</p>
        </div>

        <div id="practice-active-state" style="display:none; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <button onclick="quizEngine.quit()" style="background:transparent; border:none; font-size:24px; color:var(--text-2); cursor:pointer;">✕</button>
                <div style="flex:1; margin: 0 16px; background:var(--surface); height:12px; border-radius:6px; overflow:hidden;">
                    <div id="quiz-progress-bar" style="height:100%; background:var(--primary); width:0%; transition:width 0.3s ease;"></div>
                </div>
                <div style="font-weight:bold; color:var(--primary);" id="quiz-score-badge">❤️ <span id="quiz-lives">3</span></div>
            </div>

            <div id="quiz-question-container" style="background:var(--surface); border-radius:16px; padding:24px; box-shadow:0 4px 15px rgba(0,0,0,0.05); margin-bottom:24px; text-align:center;">
                <h3 id="quiz-question-text" style="font-size:20px; color:var(--text); line-height:1.5; margin:0;"></h3>
            </div>

            <div id="quiz-options-container" style="display:flex; flex-direction:column; gap:12px;">
                <!-- Options injected via JS -->
            </div>
        </div>

        <div id="practice-result-state" style="display:none; padding: 40px 20px; text-align: center;">
            <div class="circular-chart-container" style="width: 150px; height: 150px; margin: 0 auto 24px auto;">
                <svg viewBox="0 0 36 36" class="circular-chart">
                    <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke="var(--border-color)" stroke-width="3" fill="none" />
                    <path class="circle" id="quiz-final-circle" stroke-dasharray="0, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke="var(--primary)" stroke-width="3" fill="none" stroke-linecap="round" style="transition: stroke-dasharray 1s ease-out;" />
                </svg>
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 28px; font-weight: bold; color: var(--primary);" id="quiz-final-score">0%</div>
            </div>
            
            <h2 id="quiz-final-msg" style="color:var(--text); margin-bottom:12px;">أحسنت!</h2>
            <p id="quiz-final-sub" style="color:var(--text-2); margin-bottom:32px;">لقد أنهيت التدريب بنجاح.</p>
            
            <button onclick="quizEngine.start()" style="background:var(--primary); color:white; border:none; padding:16px 32px; border-radius:12px; font-size:16px; font-weight:bold; width:100%; cursor:pointer; margin-bottom:12px; box-shadow: 0 4px 0 rgba(0,0,0,0.1);">إعادة التدريب</button>
            <button onclick="switchTab('reader', document.getElementById('btn-nav-reader'))" style="background:transparent; color:var(--text-2); border:2px solid var(--border-color); padding:14px 32px; border-radius:12px; font-size:16px; font-weight:bold; width:100%; cursor:pointer;">العودة للدرس</button>
        </div>
    </div>
"""

nav_practice_html = """        <button class="nav-btn" id="btn-nav-practice" onclick="switchTab('practice', this)">
            <span class="icon">🎯</span><span>التدريبات</span>
        </button>
"""

if 'id="tab-practice"' not in html:
    html = html.replace('<!-- Bottom Sheet pour les Thématiques -->', practice_tab_html + '\\n    <!-- Bottom Sheet pour les Thématiques -->')

if 'id="btn-nav-practice"' not in html:
    html = html.replace('</nav>', nav_practice_html + '    </nav>')

with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html)

# PATCH JS
js_file = 'dashboard/reader.js'
with open(js_file, 'r', encoding='utf-8') as f:
    js = f.read()

quiz_engine_code = """
// ─── QUIZ ENGINE (PRACTICE TAB) ───
const quizEngine = {
    questions: [],
    currentIndex: 0,
    score: 0,
    lives: 3,
    currentSubject: null,
    currentLessonNum: null,
    audioSuccess: new Audio('https://assets.mixkit.co/sfx/preview/mixkit-correct-answer-tone-2870.mp3'),
    audioFail: new Audio('https://assets.mixkit.co/sfx/preview/mixkit-wrong-answer-fail-notification-946.mp3'),
    
    async fetchQuestions(subject, lessonNum) {
        this.currentSubject = subject;
        this.currentLessonNum = lessonNum;
        
        document.getElementById('practice-active-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-loading').style.display = 'block';
        
        try {
            const res = await fetch('/api/student/quiz/setup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    userId: 1, 
                    subject: subject,
                    courseNumbers: [lessonNum],
                    source: 'all',
                    limit: 10
                })
            });
            const data = await res.json();
            
            if (data.success && data.questions && data.questions.length > 0) {
                this.questions = data.questions;
                this.start();
            } else {
                document.getElementById('practice-loading').style.display = 'none';
                document.getElementById('practice-empty-state').innerHTML = `
                    <div style="font-size:48px; margin-bottom:16px;">🤷‍♂️</div>
                    <h3 style="color:var(--text); font-weight:700; margin-bottom:8px;">لا توجد أسئلة</h3>
                    <p style="color:var(--text-3); font-size:14px; margin-bottom:24px;">لم تتم إضافة تدريبات لهذا الدرس بعد.</p>
                `;
                document.getElementById('practice-empty-state').style.display = 'block';
            }
        } catch (e) {
            console.error("Error fetching quiz questions", e);
            document.getElementById('practice-loading').style.display = 'none';
            document.getElementById('practice-empty-state').innerHTML = `<p style="color:red;">خطأ في تحميل الأسئلة.</p>`;
            document.getElementById('practice-empty-state').style.display = 'block';
        }
    },
    
    start() {
        this.currentIndex = 0;
        this.score = 0;
        this.lives = 3;
        
        document.getElementById('practice-loading').style.display = 'none';
        document.getElementById('practice-empty-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-active-state').style.display = 'block';
        
        this.showQuestion();
    },
    
    showQuestion() {
        if (this.currentIndex >= this.questions.length || this.lives <= 0) {
            this.showResult();
            return;
        }
        
        const q = this.questions[this.currentIndex];
        
        document.getElementById('quiz-lives').textContent = this.lives;
        const progressPercent = (this.currentIndex / this.questions.length) * 100;
        document.getElementById('quiz-progress-bar').style.width = progressPercent + '%';
        
        document.getElementById('quiz-question-text').textContent = q.question;
        
        const optsContainer = document.getElementById('quiz-options-container');
        optsContainer.innerHTML = '';
        
        const choices = [];
        if (q.option_a) choices.push({ id: 'a', text: q.option_a });
        if (q.option_b) choices.push({ id: 'b', text: q.option_b });
        if (q.option_c) choices.push({ id: 'c', text: q.option_c });
        if (q.option_d) choices.push({ id: 'd', text: q.option_d });
        
        choices.forEach(c => {
            const btn = document.createElement('button');
            btn.className = 'quiz-option-btn';
            btn.innerHTML = `<span class="opt-letter">${c.id.toUpperCase()}</span><span class="opt-text">${c.text}</span>`;
            btn.onclick = () => this.checkAnswer(c.id, q.correct_choice, btn);
            optsContainer.appendChild(btn);
        });
    },
    
    checkAnswer(selectedId, correctId, btnEl) {
        const isCorrect = selectedId.toLowerCase() === correctId.toLowerCase();
        
        const allBtns = document.querySelectorAll('.quiz-option-btn');
        allBtns.forEach(b => b.style.pointerEvents = 'none'); 
        
        if (isCorrect) {
            btnEl.classList.add('correct');
            this.audioSuccess.play().catch(e=>{});
            this.score++;
            
            setTimeout(() => {
                this.currentIndex++;
                this.showQuestion();
            }, 1000);
            
        } else {
            btnEl.classList.add('wrong');
            this.audioFail.play().catch(e=>{});
            this.lives--;
            document.getElementById('quiz-lives').textContent = this.lives;
            
            allBtns.forEach(b => {
                if (b.querySelector('.opt-letter').textContent.toLowerCase() === correctId.toLowerCase()) {
                    b.classList.add('correct');
                }
            });
            
            setTimeout(() => {
                this.currentIndex++;
                this.showQuestion();
            }, 2000);
        }
    },
    
    showResult() {
        document.getElementById('practice-active-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'block';
        
        const maxScore = this.questions.length;
        const pct = Math.round((this.score / maxScore) * 100);
        
        document.getElementById('quiz-final-score').textContent = pct + '%';
        
        setTimeout(() => {
            document.getElementById('quiz-final-circle').style.strokeDasharray = `${pct}, 100`;
        }, 100);
        
        const msgEl = document.getElementById('quiz-final-msg');
        const subEl = document.getElementById('quiz-final-sub');
        
        if (this.lives <= 0) {
            msgEl.textContent = 'انتهت المحاولات 💔';
            msgEl.style.color = '#ef4444';
            subEl.textContent = 'لا بأس، يمكنك إعادة مراجعة الدرس والمحاولة مجدداً.';
            document.getElementById('quiz-final-circle').style.stroke = '#ef4444';
        } else if (pct === 100) {
            msgEl.textContent = 'ممتاز جداً! 🌟';
            msgEl.style.color = '#10b981';
            subEl.textContent = 'لقد أتقنت هذا الدرس تماماً.';
            document.getElementById('quiz-final-circle').style.stroke = '#10b981';
        } else if (pct >= 50) {
            msgEl.textContent = 'جيد جداً! 👍';
            msgEl.style.color = 'var(--primary)';
            subEl.textContent = 'لقد اجتزت التدريب، لكن يمكنك تحسين نتيجتك.';
            document.getElementById('quiz-final-circle').style.stroke = 'var(--primary)';
        } else {
            msgEl.textContent = 'حاول مجدداً 🤔';
            msgEl.style.color = '#f59e0b';
            subEl.textContent = 'ننصحك بمراجعة الدرس مرة أخرى.';
            document.getElementById('quiz-final-circle').style.stroke = '#f59e0b';
        }
    },
    
    quit() {
        switchTab('reader');
    }
};
"""

if "const quizEngine" not in js:
    js = js + '\\n' + quiz_engine_code

js = js.replace("""    if(name === 'search') {
        setTimeout(() => document.getElementById('search-input').focus(), 100);
    }""", """    if(name === 'search') {
        setTimeout(() => document.getElementById('search-input').focus(), 100);
    }
    
    if (name === 'practice') {
        if (!currentLessonData) {
            document.getElementById('practice-empty-state').style.display = 'block';
            document.getElementById('practice-active-state').style.display = 'none';
            document.getElementById('practice-result-state').style.display = 'none';
            document.getElementById('practice-loading').style.display = 'none';
        } else {
            document.getElementById('practice-empty-state').style.display = 'none';
            if (!quizEngine.questions || quizEngine.questions.length === 0 || quizEngine.currentSubject !== currentLessonData.subject || quizEngine.currentLessonNum !== currentLessonData.lessonNum) {
                quizEngine.fetchQuestions(currentLessonData.subject, currentLessonData.lessonNum);
            } else {
                if (document.getElementById('practice-result-state').style.display !== 'block') {
                    document.getElementById('practice-active-state').style.display = 'block';
                }
            }
        }
    }""")

with open(js_file, 'w', encoding='utf-8') as f:
    f.write(js)

print("Patch applied")
