import sys

file_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\dashboard\admin.js'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('// --- Curriculum Mapping (Miller Columns) ---'):
        break
    new_lines.append(line)

js_code = r'''
// --- Curriculum Mapping (Miller Columns) ---
let curriculumData = { programs: [], nodes: [], unassigned_questions: [] };
let selectedPath = { 1: null, 2: null, 3: null, 4: null };

async function loadAdminThematics() {
    const subject = document.getElementById('curriculum-subject-filter').value;
    try {
        const response = await fetch('/admin/thematics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: state.userId, subject: subject })
        });
        const data = await response.json();
        if (data.success) {
            curriculumData = data;
            selectedPath = { 1: null, 2: null, 3: null, 4: null };
            renderCurriculum();
        } else {
            console.error("Failed to load thematics:", data.error);
        }
    } catch (e) {
        console.error(e);
    }
}

function renderCurriculum() {
    const container = document.getElementById('miller-columns-container');
    container.innerHTML = '';
    
    // Level 1: Programs
    renderMillerColumn(1, null);
    
    renderMillerInbox();
}

function renderMillerColumn(level, parentId) {
    const container = document.getElementById('miller-columns-container');
    
    // Remove any columns >= level
    const existingCols = container.querySelectorAll('.miller-column');
    existingCols.forEach(col => {
        if (parseInt(col.dataset.level) >= level) {
            col.remove();
        }
    });

    let items = [];
    if (level === 1) {
        items = curriculumData.programs;
    } else {
        items = curriculumData.nodes.filter(n => n.level === level && (level === 2 ? n.program_id == parentId : n.parent_id == parentId));
    }

    if (items.length === 0 && level > 1) return;

    const colDiv = document.createElement('div');
    colDiv.className = 'miller-column';
    colDiv.dataset.level = level;
    
    const titles = { 1: 'البرامج/المواد', 2: 'الدروس', 3: 'المحاور', 4: 'الجزئيات' };
    
    let headerHtml = `
        <div class="miller-column-header">
            <span>${titles[level]}</span>
            <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.8rem;" onclick="addCurriculumNode(${level}, ${parentId})">➕</button>
        </div>
        <div class="miller-column-body" id="miller-col-body-${level}" ondragover="allowDrop(event)" ondrop="dropQuestionToNode(event, ${level})">
    `;
    
    items.sort((a,b) => (a.order_index || 0) - (b.order_index || 0)).forEach(item => {
        const isSelected = selectedPath[level] === item.id;
        const title = level === 1 ? item.name : item.title;
        headerHtml += `
            <div class="miller-item ${isSelected ? 'selected' : ''}" onclick="selectCurriculumNode(${level}, ${item.id})" data-id="${item.id}">
                <span>${title}</span>
                <div class="miller-item-actions">
                    <button class="miller-item-btn" title="تعديل" onclick="event.stopPropagation(); editCurriculumNode(${level}, ${item.id}, '${title.replace(/'/g, "\\'")}')">✏️</button>
                    <button class="miller-item-btn" title="حذف" onclick="event.stopPropagation(); deleteCurriculumNode(${level}, ${item.id})">🗑️</button>
                </div>
            </div>
        `;
    });
    
    headerHtml += '</div>';
    colDiv.innerHTML = headerHtml;
    container.appendChild(colDiv);
    
    // Auto-select first item if exists and not selected
    if (items.length > 0 && !selectedPath[level]) {
        selectCurriculumNode(level, items[0].id);
    }
}

function selectCurriculumNode(level, id) {
    selectedPath[level] = id;
    // Clear sub-levels
    for (let l = level + 1; l <= 4; l++) selectedPath[l] = null;
    
    renderCurriculum();
}

function renderMillerInbox() {
    const list = document.getElementById('miller-inbox-list');
    list.innerHTML = '';
    
    if (!curriculumData.unassigned_questions || curriculumData.unassigned_questions.length === 0) {
        list.innerHTML = '<div style="text-align:center; color: var(--text-secondary); padding: 20px;">لا يوجد أسئلة غير مصنفة</div>';
        return;
    }
    
    curriculumData.unassigned_questions.forEach(q => {
        list.innerHTML += `
            <div class="draggable-question" draggable="true" ondragstart="dragQuestion(event, ${q.id})">
                <span class="question-id-badge">#${q.id}</span>
                <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 5px;">${q.theme_id || ''} - سؤال ${q.difficulty}</div>
                <div>${q.question_text.substring(0, 100)}...</div>
            </div>
        `;
    });
}

function dragQuestion(ev, questionId) {
    ev.dataTransfer.setData("questionId", questionId);
}

function allowDrop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.add('drag-over');
}

async function dropQuestionToNode(ev, level) {
    ev.preventDefault();
    ev.currentTarget.classList.remove('drag-over');
    
    const questionId = ev.dataTransfer.getData("questionId");
    if (!questionId) return;
    
    const nodeId = selectedPath[level];
    if (!nodeId && level > 1) {
        alert("الرجاء تحديد عنصر أولاً");
        return;
    }
    
    try {
        const response = await fetch('/admin/thematics/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                userId: state.userId, 
                action: 'assign_question',
                question_id: parseInt(questionId),
                node_id: level === 1 ? null : nodeId
            })
        });
        const data = await response.json();
        if (data.success) {
            loadAdminThematics();
        }
    } catch(e) { console.error(e); }
}

async function dropQuestionToInbox(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.remove('drag-over');
    
    const questionId = ev.dataTransfer.getData("questionId");
    if (!questionId) return;
    
    try {
        const response = await fetch('/admin/thematics/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                userId: state.userId, 
                action: 'assign_question',
                question_id: parseInt(questionId),
                node_id: null
            })
        });
        const data = await response.json();
        if (data.success) {
            loadAdminThematics();
        }
    } catch(e) { console.error(e); }
}

async function addCurriculumNode(level, parentId) {
    let payload = { userId: state.userId };
    
    if (level === 1) {
        const subject = prompt("رمز المادة (مثال: fiqh):");
        if (!subject) return;
        const name = prompt("اسم البرنامج (مثال: الفقه الميسر):");
        if (!name) return;
        payload.action = 'add_program';
        payload.subject = subject;
        payload.name = name;
    } else {
        const title = prompt("عنوان العقدة:");
        if (!title) return;
        payload.action = 'add_node';
        payload.title = title;
        payload.level = level;
        if (level === 2) {
            payload.program_id = parentId;
            payload.parent_id = null;
        } else {
            const parent = curriculumData.nodes.find(n => n.id == parentId);
            payload.program_id = parent ? parent.program_id : null;
            payload.parent_id = parentId;
        }
    }
    
    try {
        const response = await fetch('/admin/thematics/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (data.success) {
            loadAdminThematics();
        } else {
            alert("خطأ: " + data.error);
        }
    } catch(e) { console.error(e); }
}

async function editCurriculumNode(level, id, oldTitle) {
    if (level === 1) {
        alert("تعديل البرامج غير متاح حالياً من الواجهة. يرجى إضافته كبرنامج جديد.");
        return;
    }
    const newTitle = prompt("عنوان العقدة:", oldTitle);
    if (!newTitle || newTitle === oldTitle) return;
    
    try {
        const response = await fetch('/admin/thematics/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                userId: state.userId, 
                action: 'update_node',
                node_id: id,
                title: newTitle
            })
        });
        const data = await response.json();
        if (data.success) {
            loadAdminThematics();
        }
    } catch(e) { console.error(e); }
}

async function deleteCurriculumNode(level, id) {
    if (!confirm("هل أنت متأكد من الحذف؟ سيتم حذف جميع العقد الفرعية المرتبطة!")) return;
    
    if (level === 1) {
        alert("حذف البرامج غير متاح حالياً للبرامج.");
        return;
    }
    
    try {
        const response = await fetch('/admin/thematics/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                userId: state.userId, 
                action: 'delete_node',
                node_id: id
            })
        });
        const data = await response.json();
        if (data.success) {
            loadAdminThematics();
        }
    } catch(e) { console.error(e); }
}

// Hook into tab switching to load data
const originalSwitchTab = window.switchTab;
window.switchTab = function(tabName) {
    if (originalSwitchTab) {
        originalSwitchTab(tabName);
    }
    if (tabName === 'curriculum') {
        loadAdminThematics();
    }
};

document.addEventListener('dragleave', (ev) => {
    if (ev.target.classList && (ev.target.classList.contains('miller-column-body') || ev.target.classList.contains('miller-inbox-list'))) {
        ev.target.classList.remove('drag-over');
    }
});
'''

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    f.write(js_code)
