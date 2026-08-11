import re

with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update quizEngine state and fetchQuestionsCustom
new_fetch = '''    async fetchQuestionsCustom(options) {
        this.currentSubject = options.subject;
        this.currentLessonNum = null;
        this.timer = options.timer || 0;
        this.correctionMode = options.correctionMode || 'instant';
        this.wrongAnswers = [];
        
        document.getElementById('practice-active-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-loading').style.display = 'block';
        
        try {
            const res = await fetch('/api/student/quiz/setup', {'''
js = js.replace('''    async fetchQuestionsCustom(options) {
        this.currentSubject = options.subject;
        this.currentLessonNum = null;
        
        document.getElementById('practice-active-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-loading').style.display = 'block';
        
        try {
            const res = await fetch('/api/student/quiz/setup', {''', new_fetch)

new_fetch2 = '''    async fetchQuestions(subject, lessonNum) {
        this.currentSubject = subject;
        this.currentLessonNum = lessonNum;
        this.timer = 0;
        this.correctionMode = 'instant';
        this.wrongAnswers = [];
        
        document.getElementById('practice-active-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-loading').style.display = 'block';
        
        try {
            const res = await fetch('/api/student/quiz/setup', {'''
js = js.replace('''    async fetchQuestions(subject, lessonNum) {
        this.currentSubject = subject;
        this.currentLessonNum = lessonNum;
        
        document.getElementById('practice-active-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-loading').style.display = 'block';
        
        try {
            const res = await fetch('/api/student/quiz/setup', {''', new_fetch2)


# 2. Add showQuestion, formatExplanationHtml, checkAnswer, etc.
new_methods = '''    formatExplanationHtml(explanation) {
        if (!explanation) return "";
        let text = explanation;
        text = text.replace("📌 <b>ملاحظة الأستاذ</b> :", "📌 <b>ملاحظة الأستاذ :</b>");
        text = text.replace("📌 <b>ملاحظة الأستاذ</b>", "📌 <b>ملاحظة الأستاذ :</b>");
        
        let pedagogicalText = "";
        let profNote = "";
        let sourceText = "";
        
        if (text.includes("💡 <b>الشرح التربوي</b> :")) {
            let parts = text.split("💡 <b>الشرح التربوي</b> :");
            let afterTitle = parts[1] || "";
            if (text.includes("📌 <b>ملاحظة الأستاذ :</b>")) {
                let subparts = afterTitle.split("📌 <b>ملاحظة الأستاذ :</b>");
                pedagogicalText = subparts[0];
                let rest = subparts[1];
                if (text.includes("📚 <b>المصدر :</b>")) {
                    let subsub = rest.split("📚 <b>المصدر :</b>");
                    profNote = subsub[0];
                    sourceText = subsub[1];
                } else {
                    profNote = rest;
                }
            } else if (text.includes("📚 <b>المصدر :</b>")) {
                let subparts = afterTitle.split("📚 <b>المصدر :</b>");
                pedagogicalText = subparts[0];
                sourceText = subparts[1];
            } else {
                pedagogicalText = afterTitle;
            }
        } else {
            let temp = document.createElement('div');
            temp.innerHTML = text;
            pedagogicalText = temp.textContent || "";
        }
        
        let html = "";
        if (pedagogicalText.trim()) {
            html += `<div style="margin-bottom:12px; font-size:15px; color:var(--text); line-height:1.6;"><strong>الشرح التربوي:</strong><br>${pedagogicalText.trim()}</div>`;
        }
        if (profNote.trim()) {
            html += `<div style="margin-bottom:12px; background:var(--surface-2); padding:12px; border-radius:8px; border-right:3px solid var(--primary); font-size:14.5px;"><span style="font-size:16px;">📌</span> <strong>ملاحظة الأستاذ:</strong><br>${profNote.trim()}</div>`;
        }
        if (sourceText.trim()) {
            html += `<div style="font-size:13px; color:var(--text-3); margin-top:8px;">📚 <strong>المصدر:</strong> ${sourceText.trim()}</div>`;
        }
        if(!html) {
            html = `<div style="margin-bottom:12px; font-size:15px;">${text}</div>`;
        }
        return html;
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
        document.getElementById('quiz-explanation-container').style.display = 'none';
        
        const optsContainer = document.getElementById('quiz-options-container');
        optsContainer.innerHTML = '';
        
        const choices = [];
        if (q.choice_a) choices.push({ id: 'a', text: q.choice_a });
        if (q.choice_b) choices.push({ id: 'b', text: q.choice_b });
        if (q.choice_c) choices.push({ id: 'c', text: q.choice_c });
        if (q.choice_d) choices.push({ id: 'd', text: q.choice_d });
        
        choices.forEach(c => {
            const btn = document.createElement('button');
            btn.className = 'quiz-option-btn';
            btn.innerHTML = `<span class="opt-letter">${c.id.toUpperCase()}</span><span class="opt-text">${c.text}</span>`;
            btn.onclick = () => this.checkAnswer(c.id, q.correct_answer, btn);
            optsContainer.appendChild(btn);
        });

        // Handle Timer
        if (this.timerInterval) clearInterval(this.timerInterval);
        const timerBar = document.getElementById('quiz-timer-bar');
        if (this.timer > 0) {
            timerBar.style.display = 'block';
            timerBar.style.width = '100%';
            timerBar.style.transition = 'none';
            
            // force reflow
            void timerBar.offsetWidth;
            
            this.timeLeft = this.timer;
            timerBar.style.transition = `width ${this.timer}s linear`;
            timerBar.style.width = '0%';
            
            this.timerInterval = setInterval(() => {
                this.timeLeft--;
                if (this.timeLeft <= 0) {
                    clearInterval(this.timerInterval);
                    this.checkAnswer(null, q.correct_answer, null); // Timeout
                }
            }, 1000);
        } else {
            timerBar.style.display = 'none';
        }
    },
    
    checkAnswer(selectedId, correctId, btnEl) {
        if (this.timerInterval) clearInterval(this.timerInterval);
        
        const isCorrect = selectedId && (selectedId.toLowerCase() === correctId.toLowerCase());
        const q = this.questions[this.currentIndex];
        
        const allBtns = document.querySelectorAll('.quiz-option-btn');
        allBtns.forEach(b => b.style.pointerEvents = 'none'); 
        
        if (isCorrect) {
            if (btnEl) btnEl.classList.add('correct');
            this.score++;
            if (this.correctionMode === 'instant') {
                this.audioSuccess.play().catch(e=>{});
                this.showExplanation(q, true);
            } else {
                this.nextQuestion();
            }
        } else {
            if (btnEl) btnEl.classList.add('wrong');
            this.lives--;
            this.wrongAnswers.push(q);
            document.getElementById('quiz-lives').textContent = this.lives;
            
            if (this.correctionMode === 'instant') {
                allBtns.forEach(b => {
                    if (b.querySelector('.opt-letter').textContent.toLowerCase() === correctId.toLowerCase()) {
                        b.classList.add('correct');
                    }
                });
                this.audioFail.play().catch(e=>{});
                this.showExplanation(q, false);
            } else {
                this.nextQuestion();
            }
        }
    },

    showExplanation(q, isCorrect) {
        const expContainer = document.getElementById('quiz-explanation-container');
        const expContent = document.getElementById('quiz-explanation-content');
        expContainer.style.display = 'block';
        
        let title = isCorrect 
            ? '<div style="color:var(--success,#10b981); font-weight:bold; margin-bottom:12px; font-size:18px;">إجابة صحيحة ✅</div>'
            : '<div style="color:#ef4444; font-weight:bold; margin-bottom:12px; font-size:18px;">إجابة خاطئة ❌</div>';
            
        let html = this.formatExplanationHtml(q.explanation);
        expContent.innerHTML = title + html;
    },
    
    nextQuestion() {
        document.getElementById('quiz-explanation-container').style.display = 'none';
        this.currentIndex++;
        this.showQuestion();
    },
    
    reportQuestion() {
        document.getElementById('report-modal').style.display = 'flex';
    },
    
    closeReportModal() {
        document.getElementById('report-modal').style.display = 'none';
        document.getElementById('report-details').value = '';
    },
    
    async submitReport() {
        const type = document.getElementById('report-type').value;
        const details = document.getElementById('report-details').value;
        const q = this.questions[this.currentIndex];
        
        document.getElementById('report-modal').style.display = 'none';
        
        try {
            await fetch('/api/student/quiz/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    questionId: q.id,
                    type: type,
                    details: details,
                    subject: this.currentSubject
                })
            });
            alert('تم إرسال التقرير بنجاح! شكراً لك.');
        } catch (e) {
            console.error('Report failed', e);
            alert('حدث خطأ أثناء الإرسال.');
        }
    },'''

js = re.sub(r'showQuestion\(\) \{.*?\n    \},\s*checkAnswer\(selectedId, correctId, btnEl\) \{.*?\n    \},', new_methods + '\n', js, flags=re.DOTALL)

# 3. Add errors list to showResult
errors_logic = '''        const msgEl = document.getElementById('quiz-final-msg');
        const errorsContainer = document.getElementById('quiz-errors-container');
        const errorsList = document.getElementById('quiz-errors-list');
        if (this.wrongAnswers && this.wrongAnswers.length > 0) {
            errorsContainer.style.display = 'block';
            let html = '';
            this.wrongAnswers.forEach((q, idx) => {
                let expHtml = this.formatExplanationHtml(q.explanation);
                html += `
                    <div style="margin-bottom:16px; border-bottom:1px solid var(--surface-2); padding-bottom:16px;">
                        <p style="font-weight:bold; color:var(--text); margin-bottom:8px;">السؤال: ${q.question}</p>
                        <div style="font-size:14px; color:var(--text-2); background:#fef2f2; padding:8px; border-radius:8px; margin-bottom:8px;">الإجابة الصحيحة كانت: <strong>${q['choice_' + q.correct_answer]}</strong></div>
                        <div style="font-size:14px;">${expHtml}</div>
                    </div>
                `;
            });
            errorsList.innerHTML = html;
        } else {
            if(errorsContainer) errorsContainer.style.display = 'none';
        }'''
js = js.replace("const msgEl = document.getElementById('quiz-final-msg');", errors_logic)

with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("reader.js patched safely")
