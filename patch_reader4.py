import re

def patch_html():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Find the syllabus tab and add the toggle UI and progress bar
    syllabus_html = """
    <!-- TAB: SYLLABUS -->
    <div class="tab-panel" id="tab-syllabus">
        <div style="padding: 20px;">
            <h2 style="color:var(--primary); font-weight:800; margin-bottom:15px; text-align:center;">📚 المقررات</h2>
            
            <!-- Global Progress -->
            <div id="syllabus-global-progress" style="background:var(--surface); border-radius:12px; padding:15px; margin-bottom:20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border:1px solid var(--border);">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-weight:700; font-size:14px; color:var(--text);">
                    <span>التقدم العام</span>
                    <span id="syllabus-progress-text">0%</span>
                </div>
                <div style="height:8px; background:var(--bg); border-radius:99px; overflow:hidden;">
                    <div id="syllabus-progress-bar" style="height:100%; background:var(--primary); width:0%; border-radius:99px; transition:width 0.4s ease;"></div>
                </div>
            </div>

            <!-- View Toggle -->
            <div style="display:flex; justify-content:center; margin-bottom:20px;">
                <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; display:flex; overflow:hidden;">
                    <button id="toggle-grid-btn" onclick="setSyllabusMode('grid')" style="flex:1; padding:10px 20px; border:none; background:var(--primary); color:white; font-weight:bold; cursor:pointer;">الشبكة</button>
                    <button id="toggle-list-btn" onclick="setSyllabusMode('list')" style="flex:1; padding:10px 20px; border:none; background:transparent; color:var(--text-2); font-weight:bold; cursor:pointer;">البرنامج</button>
                </div>
            </div>

            <div id="subjects-list" class="subjects-accordion">
                <!-- Subjects and lessons injected here -->
            </div>
        </div>
    </div>
"""
    # Replace the old syllabus tab with the new one
    old_syllabus = re.search(r'<!-- TAB: SYLLABUS -->\s*<div class="tab-panel" id="tab-syllabus">.*?</div>\s*</div>\s*</div>', html, re.DOTALL)
    if old_syllabus:
        html = html.replace(old_syllabus.group(0), syllabus_html)
    else:
        print("Syllabus HTML not found for replacement.")

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML Patched.")

def patch_js():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Add syllabusCompletion and mode
    if 'let syllabusCompletion =' not in js:
        js = js.replace('let pendingSeekTime = null;', "let pendingSeekTime = null;\nlet syllabusCompletion = JSON.parse(localStorage.getItem('academy_syllabus_completions')) || {};\nlet syllabusMode = 'grid';\n")

    # 2. Add setSyllabusMode and toggleChapterCompletion functions
    new_funcs = """
function setSyllabusMode(mode) {
    syllabusMode = mode;
    const gridBtn = document.getElementById('toggle-grid-btn');
    const listBtn = document.getElementById('toggle-list-btn');
    if (mode === 'grid') {
        gridBtn.style.background = 'var(--primary)';
        gridBtn.style.color = 'white';
        listBtn.style.background = 'transparent';
        listBtn.style.color = 'var(--text-2)';
    } else {
        listBtn.style.background = 'var(--primary)';
        listBtn.style.color = 'white';
        gridBtn.style.background = 'transparent';
        gridBtn.style.color = 'var(--text-2)';
    }
    buildSyllabusTab(DB);
}

function toggleChapterCompletion(event, subject, lessonNum, chapterIdx) {
    if (event) event.stopPropagation();
    const key = `${subject}_${lessonNum}_${chapterIdx}`;
    syllabusCompletion[key] = !syllabusCompletion[key];
    localStorage.setItem('academy_syllabus_completions', JSON.stringify(syllabusCompletion));
    
    updateGlobalProgress();
    
    // Only re-render the list view to show checks
    if(syllabusMode === 'list') {
        buildSyllabusTab(DB);
    }
}

function updateGlobalProgress() {
    let total = 0;
    let completed = 0;
    DB.forEach(l => {
        if (l.thematic_blocks) {
            l.thematic_blocks.forEach((b, idx) => {
                total++;
                if (syllabusCompletion[`${l.subject}_${l.lessonNum}_${idx}`]) {
                    completed++;
                }
            });
        }
    });
    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    const txt = document.getElementById('syllabus-progress-text');
    const bar = document.getElementById('syllabus-progress-bar');
    if(txt) txt.textContent = percent + '%';
    if(bar) bar.style.width = percent + '%';
}
"""
    if 'function setSyllabusMode' not in js:
        js += new_funcs

    # 3. Update buildSyllabusTab to support 'list' mode
    old_build = re.search(r'function buildSyllabusTab\(transcripts\) \{[\s\S]*?listContainer\.appendChild\(subjContent\);\n    \}\);\n\}', js)
    if old_build:
        new_build = """function buildSyllabusTab(transcripts) {
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
                    <div style="padding:12px; background:var(--surface); border-bottom:1px solid var(--border); font-weight:bold; display:flex; justify-content:space-between; align-items:center;" onclick="openLessonFromList('${l.subject}', ${l.lessonNum})">
                        <span>الدرس ${l.lessonNum} - ${l.title || ''}</span>
                    </div>
                    <div style="padding:10px;">`;
                
                if (l.thematic_blocks && l.thematic_blocks.length) {
                    l.thematic_blocks.forEach((b, idx) => {
                        const compKey = `${l.subject}_${l.lessonNum}_${idx}`;
                        const isComp = !!syllabusCompletion[compKey];
                        html += `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px; background:white; margin-bottom:6px; border-radius:8px; border:1px solid ${isComp ? 'var(--primary)' : 'var(--border)'};">
                            <button onclick="toggleChapterCompletion(event, '${l.subject}', ${l.lessonNum}, ${idx})" style="width:24px; height:24px; border-radius:50%; border:2px solid ${isComp ? 'var(--primary)' : '#cbd5e1'}; background:${isComp ? 'var(--primary)' : 'none'}; color:white; font-size:12px; cursor:pointer; display:flex; justify-content:center; align-items:center; flex-shrink:0;">${isComp ? '✓' : ''}</button>
                            <span onclick="openLessonFromList('${l.subject}', ${l.lessonNum}, ${b.start_seconds})" style="flex:1; margin-right:12px; font-size:13px; color:var(--text); cursor:pointer; text-align:right;">${b.title}</span>
                        </div>`;
                    });
                }
                html += `</div></div>`;
                const d = document.createElement('div');
                d.innerHTML = html;
                subjContent.appendChild(d);
            });
        }

        subjHeader.onclick = () => {
            document.querySelectorAll('.subject-content').forEach(c => {
                if (c !== subjContent) c.classList.remove('open');
            });
            document.querySelectorAll('.subject-header').forEach(h => {
                if (h !== subjHeader) h.classList.remove('open');
            });
            subjContent.classList.toggle('open');
            subjHeader.classList.toggle('open');
        };

        listContainer.appendChild(subjHeader);
        listContainer.appendChild(subjContent);
    });
    updateGlobalProgress();
}

function openLessonFromList(subject, lessonNum, startSec = null) {
    const lesson = DB.find(l => l.subject === subject && l.lessonNum === lessonNum);
    if(lesson) {
        openLesson(lesson);
        switchTab('reader');
        if (startSec !== null) {
            pendingSeekTime = startSec;
            if(player && typeof player.seekTo === 'function') {
                const state = player.getPlayerState();
                if (state === YT.PlayerState.PLAYING || state === YT.PlayerState.PAUSED || state === YT.PlayerState.CUED) {
                    player.seekTo(startSec, true);
                    player.playVideo();
                    pendingSeekTime = null;
                } else {
                    player.playVideo();
                }
            }
            const idx = thematicData.findIndex(t => t.startTime <= startSec && t.endTime > startSec);
            if(idx !== -1) {
                switchThemeTab(idx, false);
            }
        }
    }
}
"""
        js = js.replace(old_build.group(0), new_build)

    # 4. Inject 'Terminer ce chapitre' button in switchThemeTab
    old_switch = re.search(r'function switchThemeTab\(index, shouldSeek = true\) \{[\s\S]*?\}\s*function createQuizElement', js)
    if old_switch:
        switch_str = old_switch.group(0)
        # We need to append the button before `contentArea.appendChild(contentDiv);`
        if '// Mark completed button' not in switch_str:
            btn_logic = """
    // Mark completed button
    let markBtnWrapper = document.createElement('div');
    markBtnWrapper.style.textAlign = 'center';
    markBtnWrapper.style.marginTop = '24px';
    markBtnWrapper.style.marginBottom = '24px';
    
    let isCompleted = false;
    if (currentLessonData) {
        const compKey = `${currentLessonData.subject}_${currentLessonData.lessonNum}_${index}`;
        isCompleted = !!syllabusCompletion[compKey];
    }
    
    let markBtn = document.createElement('button');
    markBtn.style.padding = '12px 24px';
    markBtn.style.borderRadius = '12px';
    markBtn.style.border = 'none';
    markBtn.style.fontSize = '14px';
    markBtn.style.fontWeight = 'bold';
    markBtn.style.cursor = 'pointer';
    markBtn.style.fontFamily = 'inherit';
    
    if (isCompleted) {
        markBtn.style.background = '#e2e8f0';
        markBtn.style.color = '#64748b';
        markBtn.textContent = '✓ مكتمل';
        markBtn.disabled = true;
    } else {
        markBtn.style.background = 'var(--primary)';
        markBtn.style.color = 'white';
        markBtn.textContent = '✅ إنهاء هذا المحور';
        markBtn.onclick = () => {
            if (currentLessonData) {
                toggleChapterCompletion(null, currentLessonData.subject, currentLessonData.lessonNum, index);
                markBtn.style.background = '#e2e8f0';
                markBtn.style.color = '#64748b';
                markBtn.textContent = '✓ مكتمل';
                markBtn.disabled = true;
                
                // Show completion toast or visual effect
                let tst = document.createElement('div');
                tst.textContent = 'تم تسجيل التقدم!';
                tst.style.position = 'fixed';
                tst.style.bottom = '80px';
                tst.style.left = '50%';
                tst.style.transform = 'translateX(-50%)';
                tst.style.background = '#10b981';
                tst.style.color = 'white';
                tst.style.padding = '8px 16px';
                tst.style.borderRadius = '20px';
                tst.style.zIndex = '9999';
                document.body.appendChild(tst);
                setTimeout(() => tst.remove(), 2000);
            }
        };
    }
    
    markBtnWrapper.appendChild(markBtn);
    contentDiv.appendChild(markBtnWrapper);
"""
            # Insert just before the contentArea append
            switch_str = switch_str.replace("    contentArea.appendChild(contentDiv);", btn_logic + "\n    contentArea.appendChild(contentDiv);")
            js = js.replace(old_switch.group(0), switch_str)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print("JS Patched.")

if __name__ == '__main__':
    patch_html()
    patch_js()
