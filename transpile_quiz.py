import re

with open('dashboard/quiz.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace async fetchQuestionsCustom
js = js.replace('''async fetchQuestionsCustom(options) {
        try {
            let url = '/api/student/quiz/custom';
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(options)
            });
            const data = await res.json();
            if (data.success) {
                this.init(data.questions, options.correctionMode || 'instant', options.timer || 0);
            } else {
                alert('خطأ في استرجاع الأسئلة');
            }
        } catch(e) {
            console.error(e);
            alert('حدث خطأ');
        }
    },''', '''fetchQuestionsCustom: function(options) {
        var self = this;
        var url = '/api/student/quiz/custom';
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(options)
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.success) {
                self.init(data.questions, options.correctionMode || 'instant', options.timer || 0);
            } else {
                alert('خطأ في استرجاع الأسئلة');
            }
        })
        .catch(function(e) {
            console.error(e);
            alert('حدث خطأ');
        });
    },''')

# Replace async fetchQuestions
js = js.replace('''async fetchQuestions(subject, lessonNum) {
        try {
            const res = await fetch('/api/student/quiz?subject=' + subject + '&lesson=' + lessonNum);
            const data = await res.json();
            if (data.success) {
                this.init(data.questions, 'instant', 0);
            } else {
                alert('خطأ في استرجاع الأسئلة');
            }
        } catch(e) {
            console.error(e);
            alert('حدث خطأ');
        }
    },''', '''fetchQuestions: function(subject, lessonNum) {
        var self = this;
        fetch('/api/student/quiz?subject=' + subject + '&lesson=' + lessonNum)
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.success) {
                self.init(data.questions, 'instant', 0);
            } else {
                alert('خطأ في استرجاع الأسئلة');
            }
        })
        .catch(function(e) {
            console.error(e);
            alert('حدث خطأ');
        });
    },''')

# Replace async submitReport
js = js.replace('''async submitReport() {
        const type = document.getElementById('report-type').value;
        const details = document.getElementById('report-details').value;
        
        if (!details.trim()) {
            alert('يرجى كتابة التفاصيل');
            return;
        }
        
        try {
            const res = await fetch('/api/student/quiz/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    questionId: this.currentQuestionId,
                    type: type,
                    details: details
                })
            });
            const data = await res.json();
            if (data.success) {
                alert('تم الإرسال بنجاح');
                this.closeReportModal();
            } else {
                alert('حدث خطأ في الإرسال');
            }
        } catch(e) {
            console.error(e);
            alert('حدث خطأ');
        }
    }''', '''submitReport: function() {
        var self = this;
        var type = document.getElementById('report-type').value;
        var details = document.getElementById('report-details').value;
        
        if (!details.trim()) {
            alert('يرجى كتابة التفاصيل');
            return;
        }
        
        fetch('/api/student/quiz/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                questionId: self.currentQuestionId,
                type: type,
                details: details
            })
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.success) {
                alert('تم الإرسال بنجاح');
                self.closeReportModal();
            } else {
                alert('حدث خطأ في الإرسال');
            }
        })
        .catch(function(e) {
            console.error(e);
            alert('حدث خطأ');
        });
    }''')

# Also convert shorthand methods
js = re.sub(r'^    ([a-zA-Z0-9_]+)\((.*?)\)\s*\{', r'    \1: function(\2) {', js, flags=re.MULTILINE)

with open('dashboard/quiz.js', 'w', encoding='utf-8') as f:
    f.write(js)
