// Exam Generator Wizard Logic

let examWizard = {
    options: null,
    subject: null,
    mode: null,
    selectedIds: [],
    
    // Elements
    elSubjectGrid: null,
    elModeCards: null,
    elSelectionList: null,
    
    init() {
        this.elSubjectGrid = document.getElementById('exam-subject-grid');
        this.elModeCards = document.getElementById('exam-mode-cards');
        this.elSelectionList = document.getElementById('exam-selection-list');
    },
    
    async selectSubject(subj) {
        this.subject = subj;
        
        // Highlight active subject
        document.querySelectorAll('.exam-subject-card').forEach(c => {
            if (c.dataset.subject === subj) c.classList.add('active');
            else c.classList.remove('active');
        });
        
        // Fetch options from API
        try {
            const res = await fetch('/api/student/quiz/options?subject=' + subj);
            const data = await res.json();
            if (data.success) {
                this.options = data;
                
                // Show Mode Selection
                document.getElementById('exam-step-1').style.display = 'none';
                document.getElementById('exam-step-2').style.display = 'block';
                
                // If Sira, show Years mode. Otherwise hide it.
                const yearsCard = document.getElementById('exam-mode-years');
                if (yearsCard) {
                    yearsCard.style.display = (subj === 'sira') ? 'flex' : 'none';
                }
            } else {
                alert('خطأ في جلب البيانات');
            }
        } catch(e) {
            console.error(e);
            alert('خطأ في الاتصال');
        }
    },
    
    selectMode(mode) {
        this.mode = mode;
        this.selectedIds = [];
        
        document.getElementById('exam-step-2').style.display = 'none';
        document.getElementById('exam-step-3').style.display = 'block';
        
        const listDiv = document.getElementById('exam-selection-items');
        listDiv.innerHTML = '';
        
        let items = [];
        if (mode === 'lessons') {
            document.getElementById('exam-step-3-title').textContent = 'اختر الدروس';
            items = (this.options.lessons || []).map(l => ({id: l, title: 'الدرس ' + l}));
        } else if (mode === 'themes') {
            document.getElementById('exam-step-3-title').textContent = 'اختر المحاور';
            items = (this.options.themes || []).map(t => ({id: t.id, title: t.title}));
        } else if (mode === 'years') {
            document.getElementById('exam-step-3-title').textContent = 'اختر السنوات (السيرة)';
            items = (this.options.years || []).map(y => ({id: y, title: 'السنة ' + y}));
        }
        
        if (items.length === 0) {
            listDiv.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-3);">لا توجد بيانات متاحة</div>';
            return;
        }
        
        items.forEach(item => {
            const row = document.createElement('div');
            row.className = 'exam-selection-row';
            row.innerHTML = `
                <label style="display:flex; align-items:center; width:100%; cursor:pointer;">
                    <input type="checkbox" value="${item.id}" onchange="examWizard.toggleSelection('${item.id}', this.checked)" style="margin-left:12px; transform:scale(1.3);">
                    <span style="font-size:16px; font-weight:500;">${item.title}</span>
                </label>
            `;
            listDiv.appendChild(row);
        });
    },
    
    toggleSelection(id, isChecked) {
        // ID could be string or int
        const val = isNaN(id) ? id : parseInt(id);
        if (isChecked) {
            this.selectedIds.push(val);
        } else {
            this.selectedIds = this.selectedIds.filter(x => x !== val);
        }
        
        const startBtn = document.getElementById('exam-start-btn');
        if (this.selectedIds.length > 0) {
            startBtn.disabled = false;
            startBtn.style.opacity = '1';
        } else {
            startBtn.disabled = true;
            startBtn.style.opacity = '0.5';
        }
    },
    
    reset() {
        this.subject = null;
        this.mode = null;
        this.selectedIds = [];
        document.getElementById('exam-step-1').style.display = 'block';
        document.getElementById('exam-step-2').style.display = 'none';
        document.getElementById('exam-step-3').style.display = 'none';
        
        document.querySelectorAll('.exam-subject-card').forEach(c => c.classList.remove('active'));
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
    }
};

document.addEventListener('DOMContentLoaded', () => {
    examWizard.init();
});
