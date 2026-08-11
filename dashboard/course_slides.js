Telegram.WebApp.ready();
Telegram.WebApp.expand();

document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const subject = urlParams.get('subject');
    const lessonNum = parseInt(urlParams.get('lessonNum'));

    if (!subject || !lessonNum) {
        showError("لم يتم العثور على الدرس.");
        return;
    }

    try {
        const response = await fetch('transcripts.json');
        if (!response.ok) throw new Error("Failed to load transcripts");
        const transcripts = await response.json();

        const lesson = transcripts.find(t => 
            (t.subject === subject || t.subjectLabel.includes(subject)) && 
            t.lessonNum === lessonNum
        );

        if (!lesson) {
            showError("الدرس غير موجود في قاعدة البيانات.");
            return;
        }

        buildSlides(lesson);
    } catch (e) {
        console.error(e);
        showError("حدث خطأ أثناء تحميل الدرس.");
    }
});

function showError(msg) {
    const container = document.getElementById('slidesContainer');
    container.innerHTML = `
        <div class="slide" style="justify-content:center; align-items:center;">
            <h2>خطأ</h2>
            <p>${msg}</p>
        </div>
    `;
}

function buildSlides(lesson) {
    const container = document.getElementById('slidesContainer');
    container.innerHTML = ''; // Clear loading

    let slideCount = 0;

    // 1. Summary Slide
    slideCount++;
    const summarySlide = document.createElement('div');
    summarySlide.className = 'slide';
    
    // Convert basic markdown to HTML for summary
    const formattedSummary = (lesson.summary || lesson.full_text || 'لا يوجد ملخص متاح.')
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/\*(.*?)\*/g, '<i>$1</i>')
        .replace(/\n/g, '<br>');

    summarySlide.innerHTML = `
        <h1>${lesson.subjectLabel} - ${lesson.lesson}</h1>
        <div class="summary-card">
            <h2>خلاصة الدرس</h2>
            <p>${formattedSummary}</p>
        </div>
    `;
    container.appendChild(summarySlide);

    // 2. Video Slide (If available)
    if (lesson.video_url) {
        slideCount++;
        const videoSlide = document.createElement('div');
        videoSlide.className = 'slide';
        
        let embedUrl = lesson.video_url;
        if (embedUrl.includes('youtube.com/watch?v=')) {
            embedUrl = embedUrl.replace('watch?v=', 'embed/');
        } else if (embedUrl.includes('youtu.be/')) {
            embedUrl = embedUrl.replace('youtu.be/', 'youtube.com/embed/');
        }

        videoSlide.innerHTML = `
            <h1>الشرح المرئي</h1>
            <p>شاهد الفيديو لتوضيح المفاهيم بشكل كامل.</p>
            <div class="video-wrapper">
                <iframe src="${embedUrl}" frameborder="0" allowfullscreen></iframe>
            </div>
        `;
        container.appendChild(videoSlide);
    }

    // 3. Quiz Slide (Only for Sira for now, mocked or loaded dynamically)
    if (lesson.subject === 'sira' || lesson.subjectLabel.includes('سيرة')) {
        slideCount++;
        const quizSlide = document.createElement('div');
        quizSlide.className = 'slide';
        quizSlide.innerHTML = `
            <div class="quiz-container">
                <div class="quiz-question">سؤال سريع لاختبار معلوماتك حول هذا الدرس:</div>
                <div class="quiz-options">
                    <button class="quiz-option" onclick="checkAnswer(this, true)">إجابة صحيحة (مثال)</button>
                    <button class="quiz-option" onclick="checkAnswer(this, false)">إجابة خاطئة (مثال)</button>
                </div>
                <div class="quiz-explanation" id="quizExpl">أحسنت! هذه هي الإجابة الصحيحة بناءً على ما ورد في الدرس.</div>
            </div>
        `;
        container.appendChild(quizSlide);
    }

    setupNavigation(slideCount);
}

function checkAnswer(btn, isCorrect) {
    const parent = btn.parentElement;
    const buttons = parent.querySelectorAll('.quiz-option');
    buttons.forEach(b => b.disabled = true); // Disable all
    
    if (isCorrect) {
        btn.classList.add('correct');
        document.getElementById('quizExpl').style.display = 'block';
        document.getElementById('quizExpl').style.color = 'var(--success)';
    } else {
        btn.classList.add('wrong');
        // Find correct one to highlight
        buttons.forEach(b => {
            if (b.getAttribute('onclick').includes('true')) {
                b.classList.add('correct');
            }
        });
    }
}

function setupNavigation(count) {
    const dotsContainer = document.getElementById('navDots');
    dotsContainer.innerHTML = '';
    
    for (let i = 0; i < count; i++) {
        const dot = document.createElement('div');
        dot.className = 'dot' + (i === 0 ? ' active' : '');
        dotsContainer.appendChild(dot);
    }

    const container = document.getElementById('slidesContainer');
    const dots = document.querySelectorAll('.dot');
    
    container.addEventListener('scroll', () => {
        // Calculate which slide is currently most visible
        const slideWidth = container.clientWidth;
        const scrollPosition = container.scrollLeft;
        // scrollLeft is negative or positive depending on RTL, let's use Math.abs
        const currentIndex = Math.round(Math.abs(scrollPosition) / slideWidth);
        
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentIndex);
        });
    });
}
