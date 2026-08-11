import re
with open('dashboard/quiz.js', 'r', encoding='utf-8') as f:
    js = f.read()

# fetchQuestions
js = re.sub(
    r'async fetchQuestions\(subject, lessonNum\) \{.*?\n\s+try \{.*?\n\s+const res = await fetch\((.*?)\);.*?\n\s+const data = await res\.json\(\);.*?\n\s+if \(data\.success(.*?)\) \{.*?\n\s+this\.questions = data\.questions;\n\s+this\.start\(\);\n\s+\} else \{.*?\n\s+document\.getElementById\(\'practice-loading\'\)\.style\.display = \'none\';.*?\n\s+alert\((.*?)\);.*?\n\s+switchTab\(\'exams\'\);.*?\n\s+\}.*?\n\s+\} catch \(e\) \{.*?\n\s+console\.error\(e\);.*?\n\s+alert\((.*?)\);.*?\n\s+switchTab\(\'exams\'\);.*?\n\s+\}.*?\n\s+\},',
    r'''fetchQuestions: function(subject, lessonNum) {
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
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                userId: 1,
                subject: subject,
                courseNumbers: [lessonNum],
                source: 'all',
                mode: 'lessons',
                limit: 50
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
    },''',
    js, flags=re.DOTALL
)

# submitReport
js = re.sub(
    r'async submitReport\(\) \{.*?\n\s+try \{.*?\n\s+const res = await fetch\((.*?)\);.*?\n\s+const data = await res\.json\(\);.*?\n\s+if \(data\.success\) \{.*?\n\s+alert\((.*?)\);.*?\n\s+this\.closeReportModal\(\);.*?\n\s+\} else \{.*?\n\s+alert\((.*?)\);.*?\n\s+\}.*?\n\s+\} catch \(e\) \{.*?\n\s+console\.error\(e\);.*?\n\s+alert\((.*?)\);.*?\n\s+\}.*?\n\s+\}',
    r'''submitReport: function() {
        var type = document.getElementById('report-type').value;
        var details = document.getElementById('report-details').value;
        if (!details.trim()) { alert('???? ????? ????????'); return; }
        var self = this;
        fetch('/api/student/quiz/report', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                questionId: self.questions[self.currentIndex].id,
                type: type,
                details: details
            })
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.success) {
                alert('?? ??????? ?????');
                self.closeReportModal();
            } else {
                alert('??? ???');
            }
        })
        .catch(function(e) {
            console.error(e);
            alert('??? ???');
        });
    }''',
    js, flags=re.DOTALL
)

with open('dashboard/quiz.js', 'w', encoding='utf-8') as f:
    f.write(js)
