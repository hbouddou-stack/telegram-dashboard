const quizEngine = {
    questions: [],
    currentIndex: 0,
    score: 0,
    lives: 3,
    currentSubject: null,
    currentLessonNum: null,
    audioSuccess: new Audio('https://assets.mixkit.co/sfx/preview/mixkit-correct-answer-tone-2870.mp3'),
    audioFail: new Audio('https://assets.mixkit.co/sfx/preview/mixkit-wrong-answer-fail-notification-946.mp3'),
    
    
    fetchQuestionsCustom: function(options) {
        this.currentSubject = options.subject;
        this.currentLessonNum = null;
        this.timer = options.timer || 0;
        this.correctionMode = options.correctionMode || 'instant';
        this.wrongAnswers = [];
        
        document.getElementById('practice-active-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-loading').style.display = 'block';
        
        var self = this;
        fetch('/api/student/quiz/setup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: 1, 
                subject: options.subject,
                courseNumbers: options.courseNumbers,
                source: 'all',
                mode: options.mode,
                limit: options.limit
            })
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.success && data.questions && data.questions.length > 0) {
                self.questions = data.questions;
                self.start();
            } else {
                document.getElementById('practice-loading').style.display = 'none';
                alert('?? ??? ?????? ??? ?????');
                switchTab('exams');
            }
        })
        .catch(function(e) {
            console.error(e);
            alert('??? ???');
            switchTab('exams');
        });
    },

    fetchQuestions: function(subject, lessonNum) {
        this.currentSubject = subject;
        this.currentLessonNum = lessonNum;
        this.timer = 0;
        this.correctionMode = 'instant';
        this.wrongAnswers = [];
        
        document.getElementById('practice-active-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-loading').style.display = 'block';
        
        var self = this;
        fetch('/api/student/quiz/setup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: 1, 
                subject: subject,
                courseNumbers: [lessonNum],
                source: 'all',
                limit: 10
            })
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.success && data.questions && data.questions.length > 0) {
                self.questions = data.questions;
                self.start();
            } else {
                document.getElementById('practice-loading').style.display = 'none';
                alert('لم يتم العثور على أسئلة');
                switchTab('exams');
            }
        })
        .catch(function(e) {
            console.error(e);
            alert('حدث خطأ');
            switchTab('exams');
        });
    }
    },
    
    start: function() {
        this.currentIndex = 0;
        this.score = 0;
        this.lives = 3;
        
        document.getElementById('practice-loading').style.display = 'none';
        document.getElementById('practice-empty-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-active-state').style.display = 'block';
        
        this.showQuestion();
    },
    
        formatExplanationHtml(explanation) {
        if (!explanation) return "";
        let text = explanation;
        text = text.replace("­ƒôî <b>┘à┘äÏºÏ¡Ï©Ï® Ïº┘äÏúÏ│Ï¬ÏºÏ░</b> :", "­ƒôî <b>┘à┘äÏºÏ¡Ï©Ï® Ïº┘äÏúÏ│Ï¬ÏºÏ░ :</b>");
        text = text.replace("­ƒôî <b>┘à┘äÏºÏ¡Ï©Ï® Ïº┘äÏúÏ│Ï¬ÏºÏ░</b>", "­ƒôî <b>┘à┘äÏºÏ¡Ï©Ï® Ïº┘äÏúÏ│Ï¬ÏºÏ░ :</b>");
        
        let pedagogicalText = "";
        let profNote = "";
        let sourceText = "";
        
        if (text.includes("­ƒÆí <b>Ïº┘äÏ┤Ï▒Ï¡ Ïº┘äÏ¬Ï▒Ï¿┘ê┘è</b> :")) {
            let parts = text.split("­ƒÆí <b>Ïº┘äÏ┤Ï▒Ï¡ Ïº┘äÏ¬Ï▒Ï¿┘ê┘è</b> :");
            let afterTitle = parts[1] || "";
            if (text.includes("­ƒôî <b>┘à┘äÏºÏ¡Ï©Ï® Ïº┘äÏúÏ│Ï¬ÏºÏ░ :</b>")) {
                let subparts = afterTitle.split("­ƒôî <b>┘à┘äÏºÏ¡Ï©Ï® Ïº┘äÏúÏ│Ï¬ÏºÏ░ :</b>");
                pedagogicalText = subparts[0];
                let rest = subparts[1];
                if (text.includes("­ƒôÜ <b>Ïº┘ä┘àÏÁÏ»Ï▒ :</b>")) {
                    let subsub = rest.split("­ƒôÜ <b>Ïº┘ä┘àÏÁÏ»Ï▒ :</b>");
                    profNote = subsub[0];
                    sourceText = subsub[1];
                } else {
                    profNote = rest;
                }
            } else if (text.includes("­ƒôÜ <b>Ïº┘ä┘àÏÁÏ»Ï▒ :</b>")) {
                let subparts = afterTitle.split("­ƒôÜ <b>Ïº┘ä┘àÏÁÏ»Ï▒ :</b>");
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
            html += `<div style="margin-bottom:12px; font-size:15px; color:var(--text); line-height:1.6;"><strong>Ïº┘äÏ┤Ï▒Ï¡ Ïº┘äÏ¬Ï▒Ï¿┘ê┘è:</strong><br>${pedagogicalText.trim()}</div>`;
        }
        if (profNote.trim()) {
            html += `<div style="margin-bottom:12px; background:var(--surface-2); padding:12px; border-radius:8px; border-right:3px solid var(--primary); font-size:14.5px;"><span style="font-size:16px;">­ƒôî</span> <strong>┘à┘äÏºÏ¡Ï©Ï® Ïº┘äÏúÏ│Ï¬ÏºÏ░:</strong><br>${profNote.trim()}</div>`;
        }
        if (sourceText.trim()) {
            html += `<div style="font-size:13px; color:var(--text-3); margin-top:8px;">­ƒôÜ <strong>Ïº┘ä┘àÏÁÏ»Ï▒:</strong> ${sourceText.trim()}</div>`;
        }
        if(!html) {
            html = `<div style="margin-bottom:12px; font-size:15px;">${text}</div>`;
        }
        return html;
    },

    showQuestion: function() {
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
    
    checkAnswer: function(selectedId, correctId, btnEl) {
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

    showExplanation: function(q, isCorrect) {
        const expContainer = document.getElementById('quiz-explanation-container');
        const expContent = document.getElementById('quiz-explanation-content');
        expContainer.style.display = 'block';
        
        let title = isCorrect 
            ? '<div style="color:var(--success,#10b981); font-weight:bold; margin-bottom:12px; font-size:18px;">ÏÑÏ¼ÏºÏ¿Ï® ÏÁÏ¡┘èÏ¡Ï® Ô£à</div>'
            : '<div style="color:#ef4444; font-weight:bold; margin-bottom:12px; font-size:18px;">ÏÑÏ¼ÏºÏ¿Ï® Ï«ÏºÏÀÏªÏ® ÔØî</div>';
            
        let html = this.formatExplanationHtml(q.explanation);
        expContent.innerHTML = title + html;
    },
    
    nextQuestion: function() {
        document.getElementById('quiz-explanation-container').style.display = 'none';
        this.currentIndex++;
        this.showQuestion();
    },
    
    reportQuestion: function() {
        document.getElementById('report-modal').style.display = 'flex';
    },
    
    closeReportModal: function() {
        document.getElementById('report-modal').style.display = 'none';
        document.getElementById('report-details').value = '';
    },
    
    submitReport: function() {
        var type = document.getElementById('report-type').value;
        var details = document.getElementById('report-details').value;
        var self = this;
        var q = self.questions[self.currentIndex];
        
        document.getElementById('report-modal').style.display = 'none';
        
        fetch('/api/student/quiz/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                questionId: q.id,
                type: type,
                details: details
            })
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {})
        .catch(function(e) { console.error(e); });
    }
    },

    
    showResult: function() {
        document.getElementById('practice-active-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'block';
        
        const maxScore = this.questions.length;
        const pct = Math.round((this.score / maxScore) * 100);
        
        document.getElementById('quiz-final-score').textContent = pct + '%';
        
        setTimeout(() => {
            document.getElementById('quiz-final-circle').style.strokeDasharray = `${pct}, 100`;
        }, 100);
        
                const msgEl = document.getElementById('quiz-final-msg');
        const errorsContainer = document.getElementById('quiz-errors-container');
        const errorsList = document.getElementById('quiz-errors-list');
        if (this.wrongAnswers && this.wrongAnswers.length > 0) {
            errorsContainer.style.display = 'block';
            let html = '';
            this.wrongAnswers.forEach((q, idx) => {
                let expHtml = this.formatExplanationHtml(q.explanation);
                html += `
                    <div style="margin-bottom:16px; border-bottom:1px solid var(--surface-2); padding-bottom:16px;">
                        <p style="font-weight:bold; color:var(--text); margin-bottom:8px;">Ïº┘äÏ│ÏñÏº┘ä: ${q.question}</p>
                        <div style="font-size:14px; color:var(--text-2); background:#fef2f2; padding:8px; border-radius:8px; margin-bottom:8px;">Ïº┘äÏÑÏ¼ÏºÏ¿Ï® Ïº┘äÏÁÏ¡┘èÏ¡Ï® ┘âÏº┘åÏ¬: <strong>${q['choice_' + q.correct_answer]}</strong></div>
                        <div style="font-size:14px;">${expHtml}</div>
                    </div>
                `;
            });
            errorsList.innerHTML = html;
        } else {
            if(errorsContainer) errorsContainer.style.display = 'none';
        }
        const subEl = document.getElementById('quiz-final-sub');
        
        if (this.lives <= 0) {
            msgEl.textContent = 'Ïº┘åÏ¬┘çÏ¬ Ïº┘ä┘àÏ¡Ïº┘ê┘äÏºÏ¬ ­ƒÆö';
            msgEl.style.color = '#ef4444';
            subEl.textContent = '┘äÏº Ï¿ÏúÏ│Ïî ┘è┘à┘â┘å┘â ÏÑÏ╣ÏºÏ»Ï® ┘àÏ▒ÏºÏ¼Ï╣Ï® Ïº┘äÏ»Ï▒Ï│ ┘êÏº┘ä┘àÏ¡Ïº┘ê┘äÏ® ┘àÏ¼Ï»Ï»Ïº┘ï.';
            document.getElementById('quiz-final-circle').style.stroke = '#ef4444';
        } else if (pct === 100) {
            msgEl.textContent = '┘à┘àÏ¬ÏºÏ▓ Ï¼Ï»Ïº┘ï! ­ƒîƒ';
            msgEl.style.color = '#10b981';
            subEl.textContent = '┘ä┘éÏ» ÏúÏ¬┘é┘åÏ¬ ┘çÏ░Ïº Ïº┘äÏ»Ï▒Ï│ Ï¬┘àÏº┘àÏº┘ï.';
            document.getElementById('quiz-final-circle').style.stroke = '#10b981';
        } else if (pct >= 50) {
            msgEl.textContent = 'Ï¼┘èÏ» Ï¼Ï»Ïº┘ï! ­ƒæì';
            msgEl.style.color = 'var(--primary)';
            subEl.textContent = '┘ä┘éÏ» ÏºÏ¼Ï¬Ï▓Ï¬ Ïº┘äÏ¬Ï»Ï▒┘èÏ¿Ïî ┘ä┘â┘å ┘è┘à┘â┘å┘â Ï¬Ï¡Ï│┘è┘å ┘åÏ¬┘èÏ¼Ï¬┘â.';
            document.getElementById('quiz-final-circle').style.stroke = 'var(--primary)';
        } else {
            msgEl.textContent = 'Ï¡Ïº┘ê┘ä ┘àÏ¼Ï»Ï»Ïº┘ï ­ƒñö';
            msgEl.style.color = '#f59e0b';
            subEl.textContent = '┘å┘åÏÁÏ¡┘â Ï¿┘àÏ▒ÏºÏ¼Ï╣Ï® Ïº┘äÏ»Ï▒Ï│ ┘àÏ▒Ï® ÏúÏ«Ï▒┘ë.';
            document.getElementById('quiz-final-circle').style.stroke = '#f59e0b';
        }
    },
    
    quit: function() {
        switchTab('reader');
    }
};
