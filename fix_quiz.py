import codecs
file = 'dashboard/quiz.js'
content = codecs.open(file, 'r', 'utf-8').read()
content = content.replace('var quizEngine = {', 'window.quizEngine = {')
content = content.replace('};\nwindow.quizEngine = quizEngine;\nObject.assign(quizEngine, {\n', '')
content = content.replace('});\n', '};\n')
content = content.replace("audioSuccess: new Audio('https://assets.mixkit.co/sfx/preview/mixkit-correct-answer-tone-2870.mp3')", "audioSuccess: (typeof Audio !== 'undefined') ? new Audio('https://assets.mixkit.co/sfx/preview/mixkit-correct-answer-tone-2870.mp3') : null")
content = content.replace("audioFail: new Audio('https://assets.mixkit.co/sfx/preview/mixkit-wrong-answer-fail-notification-946.mp3')", "audioFail: (typeof Audio !== 'undefined') ? new Audio('https://assets.mixkit.co/sfx/preview/mixkit-wrong-answer-fail-notification-946.mp3') : null")
content = content.replace('this.audioSuccess.play()', 'if (this.audioSuccess) this.audioSuccess.play()')
content = content.replace('this.audioFail.play()', 'if (this.audioFail) this.audioFail.play()')
codecs.open(file, 'w', 'utf-8').write(content)
