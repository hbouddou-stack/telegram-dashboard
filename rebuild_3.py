import re

with open('dashboard/exam.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Add goToStep4, and update startQuiz to send timer & correctionMode
new_funcs = '''goToStep4() {
        document.getElementById('exam-step-3').style.display = 'none';
        document.getElementById('exam-step-4').style.display = 'block';
    },

    startQuiz() {
        if (this.selectedIds.length === 0) return;
        
        const limitInput = document.getElementById('exam-limit-input');
        const limit = limitInput ? parseInt(limitInput.value) : 10;
        const timerSelect = document.getElementById('exam-timer-mode');
        const correctionSelect = document.getElementById('exam-correction-mode');
        
        switchTab('practice');
        quizEngine.fetchQuestionsCustom({
            subject: this.subject,
            courseNumbers: this.selectedIds,
            mode: this.mode,
            limit: limit,
            timer: timerSelect ? parseInt(timerSelect.value) : 0,
            correctionMode: correctionSelect ? correctionSelect.value : 'instant'
        });
    }'''

js = js.replace('''startQuiz() {
        if (this.selectedIds.length === 0) return;
        
        const limitInput = document.getElementById('exam-limit-input');
        const limit = limitInput ? parseInt(limitInput.value) : 10;
        
        switchTab('practice');
        quizEngine.fetchQuestionsCustom({
            subject: this.subject,
            courseNumbers: this.selectedIds,
            mode: this.mode,
            limit: limit
        });
    }''', new_funcs)

with open('dashboard/exam.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("exam.js patched safely")
