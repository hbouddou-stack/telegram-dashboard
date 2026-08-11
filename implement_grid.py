import re

def implement_dashboard_and_grid():
    # --- UPDATE reader.css ---
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    new_css = """
/* --- DASHBOARD CARDS (IDEA 3) --- */
.subject-dashboard-card {
    background: var(--surface);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    cursor: pointer;
    border: 1px solid var(--border-color);
    transition: transform 0.2s, box-shadow 0.2s;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.subject-dashboard-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
}
.subject-dashboard-card .card-info {
    display: flex;
    flex-direction: column;
}
.subject-dashboard-card .card-info h3 {
    margin: 0 0 8px 0;
    font-size: 20px;
    color: var(--text);
}
.subject-dashboard-card .card-info p {
    margin: 0;
    color: var(--text-2);
    font-size: 14px;
}
.circular-progress-wrap {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    /* using conic-gradient dynamically via style */
    display: flex;
    justify-content: center;
    align-items: center;
}
.circular-progress-wrap span {
    background: var(--surface);
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 13px;
    font-weight: bold;
    color: var(--text);
}

/* --- SUBJECT DETAIL & SMART GRID (IDEA 4) --- */
.subject-detail-header {
    display: flex;
    align-items: center;
    margin-bottom: 24px;
    background: var(--surface);
    padding: 16px;
    border-radius: 12px;
    border: 1px solid var(--border-color);
}
.subject-detail-header .back-btn {
    background: var(--surface-2);
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    margin-left: 16px;
    font-weight: bold;
    color: var(--text);
    transition: background 0.2s;
}
.subject-detail-header .back-btn:hover {
    background: var(--border-color);
}
.subject-detail-header h2 {
    margin: 0;
    color: var(--text);
    font-size: 18px;
}
.smart-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(75px, 1fr));
    gap: 16px;
    justify-items: center;
}
.smart-lesson-btn {
    background: transparent;
    border: none;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 0;
    transition: transform 0.2s;
}
.smart-lesson-btn:hover {
    transform: scale(1.05);
}
.smart-lesson-btn .ring {
    width: 70px;
    height: 70px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}
.smart-lesson-btn .inner {
    width: 58px;
    height: 58px;
    border-radius: 50%;
    background: var(--surface);
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 20px;
    font-weight: bold;
    color: var(--text);
    transition: all 0.2s;
}
.smart-lesson-btn.completed .inner {
    background: var(--subject-color, var(--primary, var(--accent-color)));
    color: white;
}
.smart-lesson-btn .lesson-title-label {
    margin-top: 8px;
    font-size: 12px;
    color: var(--text-2);
    text-align: center;
    max-width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
"""

    if "/* --- DASHBOARD CARDS (IDEA 3) --- */" not in css:
        css += "\n" + new_css

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)

    # --- UPDATE reader.js ---
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    old_build_func = """function buildSyllabusTab(transcripts) {
    const subjectsMap = new Map();
    transcripts.forEach(t => {
        if (!subjectsMap.has(t.subject)) {
            subjectsMap.set(t.subject, {
                label: t.subjectLabel || t.subject,
                lessons: []
            });
        }
        subjectsMap.get(t.subject).lessons.push(t);
    });

    const listContainer = document.getElementById('subjects-list');
    if (!listContainer) return;
    listContainer.innerHTML = '';

    subjectsMap.forEach((data, subjectKey) => {
        data.lessons.sort((a,b) => a.lessonNum - b.lessonNum);
        
        const subjHeader = document.createElement('div');
        subjHeader.className = 'subject-header';
        subjHeader.innerHTML = `<h3>${data.label}</h3><span class="chev">▼</span>`;
        
        const subjContent = document.createElement('div');
        subjContent.className = syllabusMode === 'grid' ? 'subject-content subject-grid' : 'subject-content subject-list';
        
        let colorClass = 'subject-default';
        if (subjectKey.includes('sira') || subjectKey.includes('sirah')) colorClass = 'subject-sira';
        else if (subjectKey.includes('fiqh')) colorClass = 'subject-fiqh';
        else if (subjectKey.includes('tahawi') || subjectKey.includes('aqida') || subjectKey.includes('aqeeda')) colorClass = 'subject-tahawi';
        else if (subjectKey.includes('adab') || subjectKey.includes('nahw')) colorClass = 'subject-adab';
        else colorClass = 'subject-sira';
        
        if (syllabusMode === 'grid') {
            data.lessons.forEach(l => {
                const btn = document.createElement('button');
                btn.className = `lesson-3d-btn ${colorClass}`;
                btn.textContent = l.lessonNum;
                btn.onclick = () => {
                    openLesson(l);
                    switchTab('reader');
                };
                subjContent.appendChild(btn);
            });
        } else {
            // Mode Programme (List)
            data.lessons.forEach(l => {
                let html = `<div style="background:var(--bg); border-radius:12px; margin-bottom:10px; overflow:hidden;">
                    <div style="padding:12px; background:var(--surface); border-bottom:1px solid var(--border-color); font-weight:bold; display:flex; justify-content:space-between; align-items:center;" onclick="openLessonFromList('${l.subject}', ${l.lessonNum})">
                        <span>الدرس ${l.lessonNum} - ${l.title || ''}</span>
                    </div>
                    <div style="padding:10px;">`;
                
                if (l.thematic_blocks && l.thematic_blocks.length) {
                    l.thematic_blocks.forEach((b, idx) => {
                        const compKey = `${l.subject}_${l.lessonNum}_${idx}`;
                        const isComp = !!syllabusCompletion[compKey];
                        html += `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px; background:white; margin-bottom:6px; border-radius:8px; border:1px solid ${isComp ? 'var(--primary)' : 'var(--border-color)'};">
                            <button onclick="toggleChapterCompletion(event, '${l.subject}', ${l.lessonNum}, ${idx})" style="width:24px; height:24px; border-radius:50%; border:2px solid ${isComp ? 'var(--primary)' : '#cbd5e1'}; background:${isComp ? 'var(--primary)' : 'none'}; color:white; font-size:12px; cursor:pointer; display:flex; justify-content:center; align-items:center; flex-shrink:0;">${isComp ? '✓' : ''}</button>
                            <span onclick="openLessonFromList('${l.subject}', ${l.lessonNum}, ${b.start_seconds})" style="flex:1; margin-right:12px; font-size:13px; color:var(--text); cursor:pointer; text-align:right;">${b.title}</span>
                        </div>`;
                    });
                }
                html += `</div></div>`;
                subjContent.innerHTML += html;
            });
        }
        
        subjHeader.onclick = () => {
            subjContent.classList.toggle('active');
            subjHeader.classList.toggle('active');
        };
        
        listContainer.appendChild(subjHeader);
        listContainer.appendChild(subjContent);
    });
}"""

    new_build_func = """function buildSyllabusTab(transcripts) {
    const subjectsMap = new Map();
    transcripts.forEach(t => {
        if (!subjectsMap.has(t.subject)) {
            subjectsMap.set(t.subject, {
                label: t.subjectLabel || t.subject,
                lessons: []
            });
        }
        subjectsMap.get(t.subject).lessons.push(t);
    });

    const listContainer = document.getElementById('subjects-list');
    if (!listContainer) return;
    listContainer.innerHTML = '';

    subjectsMap.forEach((data, subjectKey) => {
        data.lessons.sort((a,b) => a.lessonNum - b.lessonNum);
        
        let colorClass = 'subject-default';
        if (subjectKey.includes('sira') || subjectKey.includes('sirah')) colorClass = 'subject-sira';
        else if (subjectKey.includes('fiqh')) colorClass = 'subject-fiqh';
        else if (subjectKey.includes('tahawi') || subjectKey.includes('aqida') || subjectKey.includes('aqeeda')) colorClass = 'subject-tahawi';
        else if (subjectKey.includes('adab') || subjectKey.includes('nahw')) colorClass = 'subject-adab';
        else colorClass = 'subject-sira';
        
        // Calculate completion
        let totalBlocks = 0;
        let completedBlocks = 0;
        data.lessons.forEach(l => {
            if (l.thematic_blocks && l.thematic_blocks.length) {
                l.thematic_blocks.forEach((b, idx) => {
                    totalBlocks++;
                    if (syllabusCompletion[`${l.subject}_${l.lessonNum}_${idx}`]) {
                        completedBlocks++;
                    }
                });
            } else {
                totalBlocks++;
            }
        });
        let progressPercent = totalBlocks > 0 ? Math.round((completedBlocks / totalBlocks) * 100) : 0;
        let deg = (progressPercent / 100) * 360;
        
        if (syllabusMode === 'grid') {
            // IDEA 3: Dashboard Cards
            const card = document.createElement('div');
            card.className = `subject-dashboard-card ${colorClass}`;
            card.innerHTML = `
                <div class="card-info">
                    <h3>${data.label}</h3>
                    <p>${data.lessons.length} cours &bull; ${completedBlocks}/${totalBlocks} terminés</p>
                </div>
                <div class="card-progress">
                    <div class="circular-progress-wrap" style="background: conic-gradient(var(--subject-color, var(--primary, var(--accent-color))) ${deg}deg, var(--surface-2) 0deg);">
                        <span>${progressPercent}%</span>
                    </div>
                </div>
            `;
            
            card.onclick = () => {
                openSubjectDetail(data, colorClass);
            };
            
            listContainer.appendChild(card);
        } else {
            // Mode Programme (List) - Old Accordion
            const subjHeader = document.createElement('div');
            subjHeader.className = 'subject-header';
            subjHeader.innerHTML = `<h3>${data.label}</h3><span class="chev">▼</span>`;
            
            const subjContent = document.createElement('div');
            subjContent.className = 'subject-content subject-list';
            
            data.lessons.forEach(l => {
                let html = `<div style="background:var(--bg); border-radius:12px; margin-bottom:10px; overflow:hidden;">
                    <div style="padding:12px; background:var(--surface); border-bottom:1px solid var(--border-color); font-weight:bold; display:flex; justify-content:space-between; align-items:center;" onclick="openLessonFromList('${l.subject}', ${l.lessonNum})">
                        <span>الدرس ${l.lessonNum} - ${l.title || ''}</span>
                    </div>
                    <div style="padding:10px;">`;
                
                if (l.thematic_blocks && l.thematic_blocks.length) {
                    l.thematic_blocks.forEach((b, idx) => {
                        const compKey = `${l.subject}_${l.lessonNum}_${idx}`;
                        const isComp = !!syllabusCompletion[compKey];
                        html += `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px; background:white; margin-bottom:6px; border-radius:8px; border:1px solid ${isComp ? 'var(--primary)' : 'var(--border-color)'};">
                            <button onclick="toggleChapterCompletion(event, '${l.subject}', ${l.lessonNum}, ${idx})" style="width:24px; height:24px; border-radius:50%; border:2px solid ${isComp ? 'var(--primary)' : '#cbd5e1'}; background:${isComp ? 'var(--primary)' : 'none'}; color:white; font-size:12px; cursor:pointer; display:flex; justify-content:center; align-items:center; flex-shrink:0;">${isComp ? '✓' : ''}</button>
                            <span onclick="openLessonFromList('${l.subject}', ${l.lessonNum}, ${b.start_seconds})" style="flex:1; margin-right:12px; font-size:13px; color:var(--text); cursor:pointer; text-align:right;">${b.title}</span>
                        </div>`;
                    });
                }
                html += `</div></div>`;
                subjContent.innerHTML += html;
            });
            
            subjHeader.onclick = () => {
                subjContent.classList.toggle('active');
                subjHeader.classList.toggle('active');
            };
            
            listContainer.appendChild(subjHeader);
            listContainer.appendChild(subjContent);
        }
    });
}

function openSubjectDetail(data, colorClass) {
    const listContainer = document.getElementById('subjects-list');
    listContainer.innerHTML = '';
    
    const header = document.createElement('div');
    header.className = `subject-detail-header ${colorClass}`;
    header.innerHTML = `
        <button class="back-btn" onclick="buildSyllabusTab(DB)">← رجوع</button>
        <h2 style="color: var(--subject-color, var(--primary, var(--accent-color)));">${data.label}</h2>
    `;
    listContainer.appendChild(header);
    
    const grid = document.createElement('div');
    grid.className = 'smart-grid';
    
    data.lessons.forEach(l => {
        let total = 0, comp = 0;
        if (l.thematic_blocks && l.thematic_blocks.length) {
            l.thematic_blocks.forEach((b, idx) => {
                total++;
                if (syllabusCompletion[`${l.subject}_${l.lessonNum}_${idx}`]) comp++;
            });
        } else {
            total = 1;
            // No easy generic completion for now, assume 0
        }
        let p = total > 0 ? (comp / total) * 100 : 0;
        let deg = (p / 100) * 360;
        
        const btn = document.createElement('button');
        btn.className = `smart-lesson-btn ${colorClass} ${p === 100 ? 'completed' : ''}`;
        
        btn.innerHTML = `
            <div class="ring" style="background: conic-gradient(var(--subject-color, var(--primary, var(--accent-color))) ${deg}deg, var(--surface-2) 0deg);">
                <div class="inner">${l.lessonNum}</div>
            </div>
            <div class="lesson-title-label">الدرس ${l.lessonNum}</div>
        `;
        
        btn.onclick = () => {
            openLesson(l);
            switchTab('reader');
        };
        grid.appendChild(btn);
    });
    
    listContainer.appendChild(grid);
}"""

    # Use regex to replace the function as string matching might fail due to arabic encoding/spacing
    js = re.sub(r'function buildSyllabusTab\([^\}]+\{\n.*?\}\n\}\n', new_build_func + "\n\n", js, flags=re.DOTALL)
    
    # If regex failed, maybe try a simpler one:
    if "function openSubjectDetail" not in js:
        js = js.replace(old_build_func, new_build_func)
    
    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    # --- UPDATE reader.html ---
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=44', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=44', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Success")

if __name__ == '__main__':
    implement_dashboard_and_grid()
