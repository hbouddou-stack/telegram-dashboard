// Exam Generator Wizard Logic

let examWizard = {
    options: null,
    subject: null,
    mode: null,
    selectedIds: [],
    currentStep: 1,
    
    init() {
        this.reset();
    },
    
    async selectSubject(subj) {
        this.subject = subj;
        this.currentStep = 2;
        this.updateStepVisibility();
        
        // Highlight active subject
        document.querySelectorAll('.exam-subject-card').forEach(c => {
            if (c.dataset.subject === subj) c.classList.add('active');
            else c.classList.remove('active');
        });
        
        // Fetch options from API with Fallback
        try {
            const res = await fetch('/api/student/quiz/options?subject=' + subj);
            const data = await res.json();
            if (data && data.success) {
                this.options = data;
            } else {
                this.useFallbackOptions(subj);
            }
        } catch(e) {
            console.warn('API options fetch failed, using fallback options', e);
            this.useFallbackOptions(subj);
        }
        
        // If Sira, show Years mode. Otherwise hide it.
        const yearsCard = document.getElementById('exam-mode-years');
        if (yearsCard) {
            yearsCard.style.display = (subj === 'sira') ? 'block' : 'none';
        }
    },

    useFallbackOptions(subj) {
        // Fallback: 30 lessons per subject if API is unreachable
        const lessons = Array.from({length: 30}, (_, i) => i + 1);
        this.options = {
            success: true,
            lessons: lessons,
            themes: [
                {id: 1, title: 'المحور الأول: الأحكام العامة'},
                {id: 2, title: 'المحور الثاني: الفرائض والشروط'},
                {id: 3, title: 'المحور الثالث: المندوبات والآداب'},
                {id: 4, title: 'المحور الرابع: المبطلات والنواقض'}
            ],
            years: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        };
    },
    
    selectMode(mode) {
        this.mode = mode;
        this.selectedIds = [];
        this.currentStep = 3;
        this.updateStepVisibility();
        
        const listDiv = document.getElementById('exam-selection-items');
        listDiv.innerHTML = '';
        
        let items = [];
        if (mode === 'lessons') {
            document.getElementById('exam-step-3-title').textContent = '3️⃣ اختر الدروس المراد مراجعتها:';
            items = (this.options.lessons || []).map(l => ({id: l, title: 'الدرس ' + l}));
            
            // Render as Grid for lessons for maximum UX!
            listDiv.style.display = 'grid';
            listDiv.style.gridTemplateColumns = 'repeat(auto-fill, minmax(80px, 1fr))';
            listDiv.style.gap = '8px';

            items.forEach(item => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'exam-grid-chip';
                btn.dataset.id = item.id;
                btn.style.cssText = 'padding:10px 4px; border-radius:10px; border:2px solid var(--border-color); background:var(--bg); color:var(--text); font-weight:bold; cursor:pointer; font-size:14px; text-align:center; transition:all 0.15s;';
                btn.textContent = item.title;
                btn.onclick = () => this.toggleChipSelection(item.id, btn);
                listDiv.appendChild(btn);
            });
            return;
        } else {
            listDiv.style.display = 'flex';
            listDiv.style.flexDirection = 'column';
            listDiv.style.gap = '10px';

            if (mode === 'themes') {
                document.getElementById('exam-step-3-title').textContent = '3️⃣ اختر المحاور العلميّة:';
                items = (this.options.themes || []).map(t => ({id: t.id, title: t.title}));
            } else if (mode === 'years') {
                document.getElementById('exam-step-3-title').textContent = '3️⃣ اختر السنوات الهجرية:';
                items = (this.options.years || []).map(y => ({id: y, title: 'السنة ' + y + ' هـ'}));
            }
        }
        
        if (items.length === 0) {
            listDiv.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-3);">لا توجد بيانات متاحة حالياً</div>';
            return;
        }
        
        items.forEach(item => {
            const row = document.createElement('div');
            row.style.cssText = 'background:var(--bg); border:1px solid var(--border-color); padding:10px 14px; border-radius:10px; display:flex; align-items:center; cursor:pointer;';
            row.innerHTML = `
                <label style="display:flex; align-items:center; width:100%; cursor:pointer;">
                    <input type="checkbox" value="${item.id}" onchange="examWizard.toggleSelection('${item.id}', this.checked)" style="margin-left:12px; transform:scale(1.3); accent-color:var(--primary);">
                    <span style="font-size:15px; font-weight:600; color:var(--text);">${item.title}</span>
                </label>
            `;
            listDiv.appendChild(row);
        });
    },

    toggleChipSelection(id, btn) {
        const val = isNaN(id) ? id : parseInt(id);
        const idx = this.selectedIds.indexOf(val);
        if (idx > -1) {
            this.selectedIds.splice(idx, 1);
            btn.style.background = 'var(--bg)';
            btn.style.borderColor = 'var(--border-color)';
            btn.style.color = 'var(--text)';
        } else {
            this.selectedIds.push(val);
            btn.style.background = 'var(--primary)';
            btn.style.borderColor = 'var(--primary)';
            btn.style.color = '#ffffff';
        }
        this.updateStartButton();
    },
    
    toggleSelection(id, isChecked) {
        const val = isNaN(id) ? id : parseInt(id);
        if (isChecked) {
            if (!this.selectedIds.includes(val)) this.selectedIds.push(val);
        } else {
            this.selectedIds = this.selectedIds.filter(x => x !== val);
        }
        this.updateStartButton();
    },

    selectAll(select) {
        if (this.mode === 'lessons') {
            const chips = document.querySelectorAll('.exam-grid-chip');
            this.selectedIds = [];
            chips.forEach(btn => {
                const id = isNaN(btn.dataset.id) ? btn.dataset.id : parseInt(btn.dataset.id);
                if (select) {
                    this.selectedIds.push(id);
                    btn.style.background = 'var(--primary)';
                    btn.style.borderColor = 'var(--primary)';
                    btn.style.color = '#ffffff';
                } else {
                    btn.style.background = 'var(--bg)';
                    btn.style.borderColor = 'var(--border-color)';
                    btn.style.color = 'var(--text)';
                }
            });
        } else {
            const checkboxes = document.querySelectorAll('#exam-selection-items input[type="checkbox"]');
            this.selectedIds = [];
            checkboxes.forEach(cb => {
                cb.checked = select;
                if (select) {
                    const val = isNaN(cb.value) ? cb.value : parseInt(cb.value);
                    this.selectedIds.push(val);
                }
            });
        }
        this.updateStartButton();
    },

    updateStartButton() {
        const startBtn = document.getElementById('exam-start-btn');
        if (this.selectedIds.length > 0) {
            startBtn.disabled = false;
            startBtn.style.opacity = '1';
            startBtn.textContent = `ابدأ الاختبار الآن (${this.selectedIds.length} محدد) 🚀`;
        } else {
            startBtn.disabled = true;
            startBtn.style.opacity = '0.5';
            startBtn.textContent = 'اختر درساً واحداً على الأقل للبدء';
        }
    },

    updateStepVisibility() {
        document.getElementById('exam-step-1').style.display = (this.currentStep === 1) ? 'block' : 'none';
        document.getElementById('exam-step-2').style.display = (this.currentStep === 2) ? 'block' : 'none';
        document.getElementById('exam-step-3').style.display = (this.currentStep === 3) ? 'block' : 'none';

        const backBtn = document.getElementById('exam-back-btn');
        if (backBtn) backBtn.style.display = (this.currentStep > 1) ? 'inline-block' : 'none';
    },

    goBack() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.updateStepVisibility();
        }
    },
    
    reset() {
        this.subject = null;
        this.mode = null;
        this.selectedIds = [];
        this.currentStep = 1;
        this.updateStepVisibility();
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
