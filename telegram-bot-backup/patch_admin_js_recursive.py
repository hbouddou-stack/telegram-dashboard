import re

def patch_js():
    with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Patch 1: loadAdminThematics
    old_load = """async function loadAdminThematics() {
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
        console.error("Error loading thematics:", e);
    }
}"""
    
    new_load = """async function loadAdminThematics() {
    const subject = document.getElementById('curriculum-subject-filter').value;
    const yearEl = document.getElementById('curriculum-year-filter');
    const year = yearEl ? yearEl.value : '';
    
    const container = document.getElementById('miller-columns-container');
    if (container) {
        container.className = 'miller-columns-container'; // reset
        if (subject) container.classList.add('theme-' + subject);
    }
    
    try {
        const response = await fetch('/admin/thematics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: state.userId, subject: subject, academic_year: year })
        });
        const data = await response.json();
        if (data.success) {
            curriculumData = data;
            selectedPath = {};
            renderCurriculum();
        } else {
            console.error("Failed to load thematics:", data.error);
        }
    } catch (e) {
        console.error("Error loading thematics:", e);
    }
}"""
    content = content.replace(old_load, new_load)
    
    # Patch 2: renderCurriculum
    old_rc = """function renderCurriculum() {
    const container = document.getElementById('miller-columns-container');
    container.innerHTML = '';
    
    // Level 1: Programs
    renderMillerColumn(1, null);
    
    renderMillerInbox();
}"""
    new_rc = """function renderCurriculum() {
    const container = document.getElementById('miller-columns-container');
    if (!container) return;
    container.innerHTML = '';
    
    // Level 1: Root Nodes
    renderMillerColumn(1, null);
    
    // Recursively render child columns
    let level = 1;
    while(selectedPath[level] != null) {
        renderMillerColumn(level + 1, selectedPath[level]);
        level++;
    }
    
    renderMillerInbox();
}"""
    content = content.replace(old_rc, new_rc)
    
    # Patch 3: selectCurriculumNode
    old_sc = """function selectCurriculumNode(level, id) {
    selectedPath[level] = id;
    // Clear sub-levels
    for (let l = level + 1; l <= 4; l++) selectedPath[l] = null;
    
    renderCurriculum();
}"""
    new_sc = """function selectCurriculumNode(level, id) {
    selectedPath[level] = id;
    // Clear all sub-levels beyond current
    const maxKeys = Math.max(...Object.keys(selectedPath).map(Number), level);
    for (let l = level + 1; l <= maxKeys; l++) {
        delete selectedPath[l];
    }
    renderCurriculum();
}"""
    content = content.replace(old_sc, new_sc)
    
    # Patch 4: toggleNodeVisibility
    toggle_node = """
async function toggleNodeVisibility(nodeId) {
    try {
        const response = await fetch('/admin/curriculum/toggle-visibility', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: state.userId, node_id: nodeId })
        });
        const data = await response.json();
        if (data.success) {
            loadAdminThematics();
        } else {
            alert('خطأ: ' + data.error);
        }
    } catch (e) {
        console.error(e);
        alert('حدث خطأ أثناء الاتصال بالخادم.');
    }
}
"""
    if "async function toggleNodeVisibility" not in content:
        content = content.replace("async function loadAdminThematics()", toggle_node + "\nasync function loadAdminThematics()")

    # Patch 5: renderMillerColumn
    # I will replace the whole function using regex to be safe
    # It starts at `function renderMillerColumn(level, parentId) {` and ends before `function renderMillerInbox()`
    rmc_pattern = re.compile(r'function renderMillerColumn\(level, parentId\) \{.*?(?=function renderMillerInbox\(\))', re.DOTALL)
    
    new_rmc = """function renderMillerColumn(level, parentId) {
    const container = document.getElementById('miller-columns-container');
    if (!container) return;
    
    // Remove any columns >= level
    const existingCols = container.querySelectorAll('.miller-column');
    existingCols.forEach(col => {
        if (parseInt(col.dataset.level) >= level) {
            col.remove();
        }
    });

    let items = [];
    if (level === 1) {
        // Level 1: Root nodes
        items = curriculumData.nodes.filter(n => n.parent_id == null);
    } else {
        items = curriculumData.nodes.filter(n => n.parent_id == parentId);
    }

    if (items.length === 0 && level > 1) return;

    const colDiv = document.createElement('div');
    colDiv.className = 'miller-column';
    colDiv.dataset.level = level;
    
    const depthTitles = ['المجلدات الرئيسية', 'المجلدات الفرعية', 'المحاور', 'الجزئيات', 'مستوى 5', 'مستوى 6'];
    const titleHeader = depthTitles[level - 1] || `مستوى ${level}`;
    
    let headerHtml = `
        <div class="miller-column-header">
            <span>${titleHeader}</span>
            <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.8rem;" onclick="addCurriculumNode(${level}, ${parentId})">➕</button>
        </div>
        <div class="miller-column-body" id="miller-col-body-${level}" ondragover="allowDrop(event)" ondrop="dropQuestionToNode(event, ${level})">
    `;
    
    items.sort((a,b) => {
        const orderDiff = (a.order_index || 0) - (b.order_index || 0);
        if (orderDiff !== 0) return orderDiff;
        const titleA = (a.name || a.title || '').toString();
        const titleB = (b.name || b.title || '').toString();
        return titleA.localeCompare(titleB, 'ar');
    }).forEach(item => {
        const isSelected = selectedPath[level] === item.id;
        const title = item.title || item.name;
        const isHidden = item.is_active === 0;
        const eyeIcon = isHidden ? '🚫' : '👁️';
        const opacityStyle = isHidden ? 'opacity: 0.5;' : '';
        
        headerHtml += `
            <div class="miller-item ${isSelected ? 'selected' : ''}" onclick="selectCurriculumNode(${level}, ${item.id})" data-id="${item.id}" style="${opacityStyle}">
                <span class="miller-item-text">${title}</span>
                <span class="drag-handle" draggable="true" ondragstart="dragNode(event, ${level}, ${item.id})" ondragover="allowDrop(event)" ondragleave="dragLeaveNode(event)" ondrop="dropNode(event, ${level}, ${item.id})">⋮⋮</span>
                <div class="miller-item-actions">
                    <button class="miller-item-btn" title="تبديل الظهور" onclick="event.stopPropagation(); toggleNodeVisibility(${item.id})">${eyeIcon}</button>
                    <button class="miller-item-btn" title="عرض الأسئلة" onclick="event.stopPropagation(); viewNodeQuestions(${item.id}, '${title.replace(/'/g, "\\\\'")}')">📂</button>
                    <button class="miller-item-btn" title="تعديل" onclick="event.stopPropagation(); editCurriculumNode(${level}, ${item.id}, '${title.replace(/'/g, "\\\\'")}')">✏️</button>
                    <button class="miller-item-btn" title="حذف" onclick="event.stopPropagation(); deleteCurriculumNode(${level}, ${item.id})">🗑️</button>
                </div>
            </div>
        `;
    });
    
    headerHtml += '</div>';
    colDiv.innerHTML = headerHtml;
    container.appendChild(colDiv);
    
    setTimeout(() => {
        colDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
    }, 100);
}

"""
    content = rmc_pattern.sub(new_rmc, content)
    
    with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Patched admin.js successfully")

if __name__ == "__main__":
    patch_js()
