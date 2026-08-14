var quizEngine = {
    questions: [],
    currentIndex: 0,
    score: 0,
    
    currentSubject: null,
    currentLessonNum: null,
    audioSuccess: (typeof Audio !== 'undefined') ? new Audio('https://assets.mixkit.co/sfx/preview/mixkit-correct-answer-tone-2870.mp3') : null,
    audioFail: (typeof Audio !== 'undefined') ? new Audio('https://assets.mixkit.co/sfx/preview/mixkit-wrong-answer-fail-notification-946.mp3') : null,
    
    
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
        
        // Extract 💡 التفسير التربوي :
        let pedMatch = text.match(/💡\s*<b>\s*التفسير التربوي\s*:\s*<\/b>\s*(?:<br>|\n)*\s*<blockquote>([\s\S]*?)<\/blockquote>/);
        if (pedMatch) pedagogicalText = pedMatch[1];
        
        // Extract 📖 قول الشيخ :
        let profMatch = text.match(/📖\s*<b>\s*قول الشيخ\s*:\s*<\/b>\s*(?:<br>|\n)*\s*<blockquote>([\s\S]*?)<\/blockquote>/);
        if (profMatch) profNote = profMatch[1];
        
        // Extract 📍 المصدر :
        let srcMatch = text.match(/📍\s*<b>\s*المصدر\s*:\s*<\/b>\s*(?:<br>|\n)*\s*<blockquote>([\s\S]*?)<\/blockquote>/);
        if (srcMatch) sourceText = srcMatch[1];
        
        // Fallback if nothing matched
        if (!pedagogicalText && !profNote && !sourceText) {
            pedagogicalText = text;
        }
        
        // Rewrite YouTube links for the reader internally
        if (sourceText) {
            let q = this.questions[this.currentIndex] || {};
            let subj = q.subject || this.currentSubject;
            let lessonNum = q.lessonNum || q.lesson_id || this.currentLessonNum;
            
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
