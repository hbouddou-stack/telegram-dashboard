import re

with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update quizEngine properties
js = js.replace('''    currentSubject: null,
    currentLessonNum: null,''', '''    currentSubject: null,
    currentLessonNum: null,
    timer: 0,
    correctionMode: 'instant',
    timerInterval: null,
    timeLeft: 0,
    wrongAnswers: [],''')

# 2. Update fetchQuestionsCustom
js = js.replace('''this.currentSubject = options.subject;
        this.currentLessonNum = null;''', '''this.currentSubject = options.subject;
        this.currentLessonNum = null;
        this.timer = options.timer || 0;
        this.correctionMode = options.correctionMode || 'instant';
        this.wrongAnswers = [];''')

# 3. Update fetchQuestions (set defaults for quick practice)
js = js.replace('''this.currentSubject = subject;
        this.currentLessonNum = lessonNum;''', '''this.currentSubject = subject;
        this.currentLessonNum = lessonNum;
        this.timer = 0;
        this.correctionMode = 'instant';
        this.wrongAnswers = [];''')

with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(js)
print('reader.js properties updated')
