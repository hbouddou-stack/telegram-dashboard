import re

with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    content = f.read()

custom_fetch = '''
    async fetchQuestionsCustom(options) {
        this.currentSubject = options.subject;
        this.currentLessonNum = null;
        
        document.getElementById('practice-active-state').style.display = 'none';
        document.getElementById('practice-result-state').style.display = 'none';
        document.getElementById('practice-loading').style.display = 'block';
        
        try {
            const res = await fetch('/api/student/quiz/setup', {
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
            });
            const data = await res.json();
            
            if (data.success && data.questions && data.questions.length > 0) {
                this.questions = data.questions;
                this.start();
            } else {
                document.getElementById('practice-loading').style.display = 'none';
                alert('عذراً، لا توجد أسئلة متاحة لهذه الخيارات.');
                switchTab('exams');
            }
        } catch (e) {
            console.error(e);
            alert('حدث خطأ أثناء تحميل الأسئلة');
            switchTab('exams');
        }
    },
'''

content = content.replace('async fetchQuestions(subject, lessonNum) {', custom_fetch + '\n    async fetchQuestions(subject, lessonNum) {')

with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
