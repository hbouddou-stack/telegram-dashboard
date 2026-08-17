var quizEngine = {
    questions: [],
    currentIndex: 0,
    score: 0,
    
    currentSubject: null,
    currentLessonNum: null,

    playSound: function(type) {
        try {
            if (!window.AudioContext && !window.webkitAudioContext) return;
            const Ctx = window.AudioContext || window.webkitAudioContext;
            if (!this.audioCtx) this.audioCtx = new Ctx();
            const ctx = this.audioCtx;
            if (ctx.state === 'suspended') ctx.resume();
            
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            
            const now = ctx.currentTime;
            if (type === 'success') {
                osc.type = 'sine';
                osc.frequency.setValueAtTime(659.25, now); // E5
                osc.frequency.exponentialRampToValueAtTime(1318.51, now + 0.1); // E6
                gain.gain.setValueAtTime(0, now);
                gain.gain.linearRampToValueAtTime(0.3, now + 0.05);
                gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4);
                osc.start(now);
                osc.stop(now + 0.4);
            } else {
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(200, now);
                osc.frequency.exponentialRampToValueAtTime(100, now + 0.2);
                gain.gain.setValueAtTime(0, now);
                gain.gain.linearRampToValueAtTime(0.3, now + 0.02);
                gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
                osc.start(now);
                osc.stop(now + 0.3);
            }
        } catch(e) { console.warn('Audio failed:', e); }
    },

    // audio properties removed in favor of synthesized sounds
    // audio properties removed in favor of synthesized sounds
    
    
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
                alert('لم يتم العثور على أسئلة');
                switchTab('exams');
            }
        })
        .catch(function(e) {
            console.error(e);
            alert('حدث خطأ');
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
    },
    
    start: function() {
        this.currentIndex = 0;
        this.score = 0;
        
        
        document.getElementById('practice-loading').style.display = 'none';
        document.getElementById('practice-empty-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-active-state').style.display = 'block';
        
        this.showQuestion();
    },
    
        formatExplanationHtml(explanation) {
        if (!explanation) return "";
        let text = explanation;
        
        let pedagogicalText = "";
        let profNote = "";
        let sourceText = "";
        
        let pedMatch = text.match(/💡\s*<b>\s*التفسير التربوي\s*:\s*<\/b>\s*(?:<br>|\n)*\s*<blockquote>([\s\S]*?)<\/blockquote>/);
        if (pedMatch) pedagogicalText = pedMatch[1];
        
        let profMatch = text.match(/📖\s*<b>\s*قول الشيخ\s*:\s*<\/b>\s*(?:<br>|\n)*\s*<blockquote>([\s\S]*?)<\/blockquote>/);
        if (profMatch) profNote = profMatch[1];
        
        let srcMatch = text.match(/📍\s*<b>\s*المصدر\s*:\s*<\/b>\s*(?:<br>|\n)*\s*<blockquote>([\s\S]*?)<\/blockquote>/);
        if (srcMatch) sourceText = srcMatch[1];
        
        if (!pedagogicalText && !profNote && !sourceText) {
            pedagogicalText = text;
        }
        
        if (sourceText) {
            let q = this.questions[this.currentIndex] || {};
            let subj = q.subject || this.currentSubject;
            let lessonNum = q.course_number || q.lessonNum || q.lesson_id || this.currentLessonNum;
            
            sourceText = sourceText.replace(/<a\s+href="https?:\/\/www\.youtube\.com\/watch\?.*?&t=(\d+)s?".*?>([\s\S]*?)<\/a>/gi, function(match, seconds, content) {
                return `<button onclick="openSearchResult('${subj}', ${lessonNum}, ${seconds})" style="background:var(--primary); color:white; border:none; padding:4px 10px; border-radius:6px; cursor:pointer; font-size:12px; font-weight:bold; margin-right:6px; display:inline-flex; align-items:center; gap:4px;">▶️ مشاهدة في اللوحة ${content.replace(/<\/?b>/g, '')}</button>`;
            });
        }
        
        let html = "";
        if (pedagogicalText.trim()) {
            html += `<div style="margin-bottom:14px; padding:14px 16px; background:linear-gradient(135deg, #f0fdf4, #dcfce7); border-radius:12px; border-right:4px solid #22c55e; font-size:14.5px; color:#15803d; line-height:1.7; text-align:right;">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px; font-weight:900; font-size:15px; color:#166534;">
                    <span style="font-size:18px;">💡</span> التفسير التربوي
                </div>
                ${pedagogicalText.trim()}
            </div>`;
        }
        if (profNote.trim()) {
            html += `<div style="margin-bottom:14px; padding:14px 16px; background:linear-gradient(135deg, #fffbeb, #fef3c7); border-radius:12px; border-right:4px solid #f59e0b; font-size:14px; color:#92400e; line-height:1.7; font-style:italic; text-align:right;">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px; font-weight:900; font-size:15px; color:#b45309; font-style:normal;">
                    <span style="font-size:18px;">📖</span> قول الشيخ
                </div>
                « ${profNote.trim()} »
            </div>`;
        }
        if (sourceText.trim()) {
            html += `<div style="margin-bottom:8px; padding:12px 14px; background:linear-gradient(135deg, #f8fafc, #f1f5f9); border-radius:10px; border-right:4px solid #94a3b8; font-size:13px; color:#475569; line-height:1.6; text-align:right;">
                <div style="display:flex; align-items:center; gap:6px; margin-bottom:8px; font-weight:800; font-size:14px; color:#334155;">
                    <span style="font-size:18px;">📍</span> المصدر
                </div>
                ${sourceText.trim()}
            </div>`;
        }
        
        return html;
    },

    showQuestion: function() {
        if (this.currentIndex >= this.questions.length ) {
            this.showResult();
            return;
        }
        
        const q = this.questions[this.currentIndex];
        const qType = q.question_type || 'mcq';
        
        // lives display removed
        const progressPercent = (this.currentIndex / this.questions.length) * 100;
        document.getElementById('quiz-progress-bar').style.width = progressPercent + '%';
        
        document.getElementById('quiz-question-text').textContent = q.question;
        document.getElementById('quiz-explanation-container').style.display = 'none';
        
        const optsContainer = document.getElementById('quiz-options-container');
        optsContainer.innerHTML = '';
        
        // Handle image media
        if (q.media_url) {
            const img = document.createElement('img');
            img.src = q.media_url;
            img.style.maxWidth = '100%';
            img.style.borderRadius = '12px';
            img.style.marginBottom = '16px';
            optsContainer.appendChild(img);
        }
        
        const choices = [];
        if (q.choice_a) choices.push({ id: 'a', text: q.choice_a });
        if (q.choice_b) choices.push({ id: 'b', text: q.choice_b });
        if (q.choice_c) choices.push({ id: 'c', text: q.choice_c });
        if (q.choice_d) choices.push({ id: 'd', text: q.choice_d });
        
        if (qType === 'ordering') {
            const list = document.createElement('ul');
            list.id = 'ordering-list';
            list.style.listStyle = 'none';
            list.style.padding = '0';
            list.style.margin = '0 0 20px 0';
            
            // Shuffle choices for ordering
            const shuffledChoices = choices.sort(() => Math.random() - 0.5);
            
            shuffledChoices.forEach(c => {
                const li = document.createElement('li');
                li.className = 'quiz-option-btn';
                li.style.cursor = 'grab';
                li.dataset.id = c.id;
                li.innerHTML = `<span class="opt-letter">☰</span><span class="opt-text">${c.text}</span>`;
                list.appendChild(li);
            });
            optsContainer.appendChild(list);
            
            // Initialize Sortable
            if (typeof Sortable !== 'undefined') {
                new Sortable(list, {
                    animation: 150,
                    ghostClass: 'sortable-ghost'
                });
            }
            
            // Validate button
            const validateBtn = document.createElement('button');
            validateBtn.className = 'quiz-option-btn';
            validateBtn.style.background = 'var(--primary)';
            validateBtn.style.color = 'white';
            validateBtn.style.fontWeight = 'bold';
            validateBtn.style.justifyContent = 'center';
            validateBtn.innerHTML = `تحقق من الترتيب`;
            validateBtn.onclick = () => {
                const currentOrder = Array.from(list.children).map(li => li.dataset.id).join(',');
                this.checkAnswer(currentOrder, q.correct_answer, validateBtn);
            };
            optsContainer.appendChild(validateBtn);
            
        } else if (qType === 'true_false') {
            const tfChoices = [
                { id: 'a', text: 'صحيح', color: '#10b981' },
                { id: 'b', text: 'خطأ', color: '#ef4444' }
            ];
            
            const tfContainer = document.createElement('div');
            tfContainer.style.display = 'grid';
            tfContainer.style.gridTemplateColumns = '1fr 1fr';
            tfContainer.style.gap = '16px';
            
            tfChoices.forEach(c => {
                const btn = document.createElement('button');
                btn.className = 'quiz-option-btn';
                btn.style.justifyContent = 'center';
                btn.style.fontSize = '20px';
                btn.style.fontWeight = 'bold';
                btn.style.border = `2px solid ${c.color}`;
                btn.style.color = c.color;
                btn.innerHTML = c.text;
                btn.onclick = () => {
                    btn.style.background = c.color;
                    btn.style.color = 'white';
                    this.checkAnswer(c.id, q.correct_answer, btn);
                };
                tfContainer.appendChild(btn);
            });
            optsContainer.appendChild(tfContainer);
            
        } else {
            // Default MCQ
            choices.forEach(c => {
                const btn = document.createElement('button');
                btn.className = 'quiz-option-btn';
                btn.innerHTML = `<span class="opt-letter">${c.id.toUpperCase()}</span><span class="opt-text">${c.text}</span>`;
                btn.onclick = () => this.checkAnswer(c.id, q.correct_answer, btn);
                optsContainer.appendChild(btn);
            });
        }

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
                this.playSound('success');
                this.showExplanation(q, true);
            } else {
                this.nextQuestion();
            }
        } else {
            if (btnEl) btnEl.classList.add('wrong');
            this.lives--;
            this.wrongAnswers.push(q);
            // lives display removed
            
            if (this.correctionMode === 'instant') {
                allBtns.forEach(b => {
                    if (b.querySelector('.opt-letter').textContent.toLowerCase() === correctId.toLowerCase()) {
                        b.classList.add('correct');
                    }
                });
                this.playSound('fail');
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
            ? '<div style="color:var(--success,#10b981); font-weight:bold; margin-bottom:12px; font-size:18px;">إجابة صحيحة ✅</div>'
            : '<div style="color:#ef4444; font-weight:bold; margin-bottom:12px; font-size:18px;">إجابة خاطئة ❌</div>';
            
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
                        <p style="font-weight:bold; color:var(--text); margin-bottom:8px;">السؤال: ${q.question}</p>
                        <div style="font-size:14px; color:var(--text-2); background:#fef2f2; padding:8px; border-radius:8px; margin-bottom:8px;">الإجابة الصحيحة كانت: <strong>${q['choice_' + q.correct_answer]}</strong></div>
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
    
    quit: function() {
        switchTab('reader');
    }
};
