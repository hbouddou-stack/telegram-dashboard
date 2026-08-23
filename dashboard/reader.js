let isReadingMode = false;
let player; 
let currentLessonData = null;
let currentSubject = null;
let currentLessonNum = null;
let currentTabIndex = 0;
let thematicData = []; // Array of objects { title, startTime, endTime, htmlContent, questions: [] }
let DB = [];
let wordIndex = [];
let pendingSeekTime = null;
let syllabusCompletion = JSON.parse(localStorage.getItem('academy_syllabus_completions')) || {};
let syllabusMode = 'grid';
let isSeekingTab = false;

function playCompletionSound() {
    try {
        if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
            window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
        }
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, ctx.currentTime); 
        osc.frequency.exponentialRampToValueAtTime(1760, ctx.currentTime + 0.1); 
        
        gain.gain.setValueAtTime(0, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.5, ctx.currentTime + 0.05);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
        
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.3);
    } catch(e) {}
}

const SUBJECT_LABELS = {
    'sira': 'Ã˜Â§Ã™â€žÃ˜Â³Ã™Å Ø±Ø© Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Ë†Ã™Å Ø©',
    'fiqh': 'Ã˜Â§Ã™â€žÃ™ÂÃ™â€šÃ™â€¡',
    'tahawi': 'Ã˜Â§Ã™â€žÃ˜Â¹Ã™â€šÃ™Å Ø¯Ø© Ã˜Â§Ã™â€žÃ˜Â·Ã˜Â­Ã˜Â§Ã™Ë†Ã™Å Ø©',
    'adab': 'Ã˜Â§Ã™â€žØ£Ø¯Ø¨',
    'nahw': 'Ã˜Â§Ã™â€žÃ™â€ Ø­Ùˆ'
};


// UI State
let currentTheme = localStorage.getItem('readerTheme') || 'sepia';
let fontSizeBase = parseInt(localStorage.getItem('readerFontSize')) || 18; 
if(currentTheme !== 'light') document.documentElement.setAttribute('data-theme', currentTheme);
document.documentElement.style.setProperty('--font-size-base', fontSizeBase + 'px');

document.addEventListener('DOMContentLoaded', async () => {
    initUIControls();

    try {
        const urlParams = new URLSearchParams(window.location.search);
        let lessonParam = urlParams.get('lesson'); 
        let subjectParam = urlParams.get('subject'); 

        const response = await fetch('transcripts.json?v=' + Date.now());
        DB = await response.json();

        buildSyllabusTab(DB);
        setTimeout(buildIndex, 100);

        if (lessonParam) {
            const found = DB.find(t => 
                (t.lessonNum == lessonParam || t.lesson.includes(lessonParam)) &&
                (!subjectParam || t.subject === subjectParam)
            );
            if (found) {
                openLesson(found);
                switchTab('reader');
            } else {
                switchTab('dashboard');
            }
        } else {
            switchTab('dashboard');
        }

    } catch (e) {
        console.error("Error loading reader data:", e);
    }
});

function loadLesson(lessonNum, subject, startSeconds = 0) {
    currentSubject = subject;
    currentLessonNum = lessonNum;
    
    document.getElementById('reader-empty-state').style.display = 'none';
    const activeState = document.getElementById('reader-active-state');
    if(activeState) activeState.style.display = 'block';
    
    document.getElementById('reader-content').style.display = 'block';
    const lesson = DB.find(t => t.lessonNum == lessonNum && t.subject === subject);
    if (lesson) {
        if (startSeconds > 0) {
            pendingSeekTime = startSeconds;
        }
        openLesson(lesson);
    }
}

window.openLessonFromList = function(subject, lessonNum, startSeconds = 0) {
    loadLesson(lessonNum, subject, startSeconds);
    switchTab('reader');
};

function openLesson(lesson) {
    const emptyState = document.getElementById('reader-empty-state');
    const activeState = document.getElementById('reader-active-state');
    if(emptyState) emptyState.style.display = 'none';
    if(activeState) activeState.style.display = 'block';
    
    document.getElementById('reader-content').style.display = 'block';
    currentLessonData = lesson;
    
    // Auto-seek logic
    if (!pendingSeekTime && lesson.thematic_blocks && lesson.thematic_blocks.length > 0) {
        pendingSeekTime = lesson.thematic_blocks[0].start_seconds;
    }
    
    prepareThematicData(lesson);
    renderLessonHeader(lesson);
    renderTabs();
    
    // Automatically set reader nav button visible
    document.getElementById('btn-nav-reader').style.display = 'flex';
    
    if(thematicData.length > 0) {
        switchThemeTab(0, false);
    }
    markLessonOpened(lesson.subject, lesson.lessonNum);
}



// Reading Progress Bar Logic

function updateDashboardProgress() {
    if (!thematicData || thematicData.length === 0) return;
    
    let currentTime = 0;
    let duration = 1;
    if (player && typeof player.getCurrentTime === 'function') {
        currentTime = player.getCurrentTime() || 0;
        duration = player.getDuration() || 1;
    }

    const numThemes = thematicData.length;
    let activeIdx = currentTabIndex;

    // Reverting to artificial evenly-spaced progress bar (N spaces for N themes)
    let totalFill = 0;
    
    if (numThemes <= 1) {
        totalFill = duration > 0 ? (currentTime / duration) * 100 : 0;
    } else {
        let blockIndex = 0;
        for (let i = 0; i < numThemes; i++) {
            if (currentTime >= thematicData[i].startTime && (i === numThemes - 1 || currentTime < thematicData[i+1].startTime)) {
                blockIndex = i;
                break;
            }
        }
        
        let blockStart = thematicData[blockIndex].startTime;
        let blockEnd = (blockIndex === numThemes - 1) ? duration : thematicData[blockIndex+1].startTime;
        let blockDuration = blockEnd - blockStart;
        if (blockDuration <= 0) blockDuration = 1;
        
        let fractionInBlock = (currentTime - blockStart) / blockDuration;
        fractionInBlock = Math.max(0, Math.min(1, fractionInBlock));
        
        let spacePerBlock = 100 / numThemes;
        totalFill = (blockIndex * spacePerBlock) + (fractionInBlock * spacePerBlock);
    }
    totalFill = Math.max(0, Math.min(100, totalFill));

    const titleEl = document.getElementById('current-theme-label');
    let currentTab = thematicData[activeIdx];
    if (titleEl && currentTab) titleEl.textContent = (activeIdx + 1) + ". " + currentTab.title;
    
    const dotsContainer = document.getElementById('progress-tracker-dots');
    if (!dotsContainer) return;
    
    if (dotsContainer.childElementCount <= 2 || dotsContainer.getAttribute('data-lesson') !== `${currentLessonData.subject}_${currentLessonData.lessonNum}`) {
        let dotsHtml = '';
        for(let i = 0; i <= numThemes; i++) {
            const isCompleted = currentLessonData && i < numThemes ? !!syllabusCompletion[`${currentLessonData.subject}_${currentLessonData.lessonNum}_${i}`] : false;
            const isCurrent = (i === activeIdx);
            const isPast = (i < activeIdx) || (i === numThemes && activeIdx === numThemes - 1 && totalFill >= 99);
            
            let bgClass = isPast || isCurrent || isCompleted ? 'var(--primary, var(--accent-color))' : 'var(--surface-2)';
            let borderColor = isPast || isCurrent || isCompleted ? 'var(--primary, var(--accent-color))' : 'var(--border-color)';
            
            const scale = isCurrent ? '1.4' : (isCompleted ? '1.1' : '1');
            const pos = numThemes === 0 ? 0 : (i / numThemes) * 100;
            
            let onclickAttr = i < numThemes ? `onclick="switchThemeTab(${i});"` : '';
            
            dotsHtml += `
            <div class="progress-dot-item" style="position: absolute; right: ${pos}%; top: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; z-index: 2; transition: all 0.3s; cursor:pointer;" ${onclickAttr}>
                <div style="width: 12px; height: 12px; border-radius: 50%; background: ${bgClass}; border: 2px solid var(--surface); box-shadow: 0 0 0 1px ${borderColor}; transform: scale(${scale}); transition: all 0.3s;"></div>
            </div>`;
        }
        dotsHtml += `
        <div class="progress-line-bg" style="position: absolute; top: 50%; left: 0; right: 0; height: 4px; background: var(--surface-2); transform: translateY(-50%); border-radius: 2px; z-index: 0;"></div>
        <div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 3px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: ${totalFill}%; transition: width 0.1s linear; z-index: 1;"></div>
        `;
        dotsContainer.innerHTML = dotsHtml;
        dotsContainer.setAttribute('data-lesson', `${currentLessonData.subject}_${currentLessonData.lessonNum}`);
    } else {
        const fillEl = document.getElementById('progress-tracker-fill');
        const dots = dotsContainer.querySelectorAll('.progress-dot-item');
        dots.forEach((dot, i) => {
            if (i > numThemes) return;
            const isCompleted = currentLessonData && i < numThemes ? !!syllabusCompletion[`${currentLessonData.subject}_${currentLessonData.lessonNum}_${i}`] : false;
            const isCurrent = (i === activeIdx);
            const isPast = (i < activeIdx) || (i === numThemes && activeIdx === numThemes - 1 && totalFill >= 99);
            
            let bgClass = isPast || isCurrent || isCompleted ? 'var(--primary, var(--accent-color))' : 'var(--surface-2)';
            let borderColor = isPast || isCurrent || isCompleted ? 'var(--primary, var(--accent-color))' : 'var(--border-color)';
            
            const scale = isCurrent ? '1.4' : (isCompleted ? '1.1' : '1');
            
            const dotCircle = dot.firstElementChild;
            dotCircle.style.background = bgClass;
            const pos = numThemes === 0 ? 0 : (i / numThemes) * 100;
            dot.style.right = `${pos}%`;
            dotCircle.style.boxShadow = `0 0 0 1px ${borderColor}`;
            dotCircle.style.transform = `scale(${scale})`;
        });
        
        if (fillEl) {
            fillEl.style.width = `${totalFill}%`;
            fillEl.style.background = 'var(--primary, var(--accent-color))';
        }
    }
}

function initUIControls() {
    // Sticky Video Toggle Logic
    const btnSticky = document.getElementById('btn-sticky-toggle');
    const videoWrapper = document.getElementById('video-wrapper');
    const sommaireWrapper = document.getElementById('sommaire-wrapper');
    
    if (btnSticky && videoWrapper && sommaireWrapper) {
        // Toggle pinned state
        btnSticky.addEventListener('click', () => {
            if (videoWrapper.classList.contains('pinned')) {
                // Unpin
                videoWrapper.classList.remove('pinned');
                videoWrapper.style.position = 'relative';
                btnSticky.style.opacity = '0.5';
                btnSticky.title = "Ãƒâ€°pingler la vidÃƒÂ©o";
                sommaireWrapper.style.top = '0px';
            } else {
                // Pin
                videoWrapper.classList.add('pinned');
                videoWrapper.style.position = 'sticky';
                btnSticky.style.opacity = '1';
                btnSticky.title = "DÃƒÂ©sÃƒÂ©pingler la vidÃƒÂ©o";
                sommaireWrapper.style.top = videoWrapper.offsetHeight + 'px';
            }
        });

        // Keep Sommaire right below the video dynamically
        new ResizeObserver(() => {
            if (videoWrapper.classList.contains('pinned')) {
                sommaireWrapper.style.top = videoWrapper.offsetHeight + 'px';
            }
        }).observe(videoWrapper);
    }

    const globalSidebar = document.getElementById('global-sidebar');
    const globalOverlay = document.getElementById('global-overlay');
    if (globalSidebar && globalOverlay) {
        const closeGlobal = () => {
            globalSidebar.classList.remove('open');
            globalOverlay.classList.remove('show');
        };
        document.getElementById('close-global-sidebar').addEventListener('click', closeGlobal);
        globalOverlay.addEventListener('click', closeGlobal);
    }

    // Sommaire Bottom Sheet
    const sommaireBtn = document.getElementById('open-sommaire-btn');
    const sommaireOverlay = document.getElementById('sommaire-overlay');
    const sommaireSheet = document.getElementById('sommaire-sheet');
    const closeSommaireBtn = document.getElementById('close-sommaire-btn');

    const openSommaire = () => {
        sommaireOverlay.classList.add('show');
        sommaireSheet.classList.add('open');
    };
    const closeSommaire = () => {
        sommaireOverlay.classList.remove('show');
        sommaireSheet.classList.remove('open');
    };

    if(sommaireBtn) sommaireBtn.addEventListener('click', openSommaire);
    if(closeSommaireBtn) closeSommaireBtn.addEventListener('click', closeSommaire);
    if(sommaireOverlay) sommaireOverlay.addEventListener('click', closeSommaire);

    // Text & Theme Controls
    // Initialize UI theme toggle button
    const themeBtn = document.getElementById('btn-theme-toggle');
    if(themeBtn) {
        if(currentTheme === 'dark') themeBtn.textContent = 'Ã¢Ëœâ‚¬Ã¯Â¸Â';
        else if(currentTheme === 'sepia') themeBtn.textContent = 'Ã°Å¸â€œÅ“';
        else themeBtn.textContent = 'Ã°Å¸Å’â„¢';

        themeBtn.addEventListener('click', () => {
            if (currentTheme === 'light') currentTheme = 'sepia';
            else if (currentTheme === 'sepia') currentTheme = 'dark';
            else currentTheme = 'light';
            
            document.documentElement.setAttribute('data-theme', currentTheme);
            localStorage.setItem('readerTheme', currentTheme);
            
            if (currentTheme === 'dark') themeBtn.textContent = 'Ã¢Ëœâ‚¬Ã¯Â¸Â';
            else if (currentTheme === 'sepia') themeBtn.textContent = 'Ã°Å¸â€œÅ“';
            else themeBtn.textContent = 'Ã°Å¸Å’â„¢';
        });
    }
    
    // ZEN MODE LOGIC
    const zenBtn = document.getElementById('btn-zen-toggle');
    if (zenBtn) {
        zenBtn.addEventListener('click', () => {
            document.body.classList.toggle('zen-mode');
            if (document.body.classList.contains('zen-mode')) {
                zenBtn.style.color = 'var(--primary, var(--accent-color))';
                // Block auto-scroll completely in zen mode
                lastUserScrollTime = Date.now() + 999999999;
            } else {
                zenBtn.style.color = '';
                // Re-enable auto-scroll with a 5s grace period
                lastUserScrollTime = Date.now();
            }
        });
    }

    document.getElementById('btn-text-plus').addEventListener('click', () => {
        if(fontSizeBase < 30) {
            fontSizeBase += 2;
            document.documentElement.style.setProperty('--font-size-base', fontSizeBase + 'px');
            localStorage.setItem('readerFontSize', fontSizeBase);
        }
    });

    document.getElementById('btn-text-minus').addEventListener('click', () => {
        if(fontSizeBase > 14) {
            fontSizeBase -= 2;
            document.documentElement.style.setProperty('--font-size-base', fontSizeBase + 'px');
            localStorage.setItem('readerFontSize', fontSizeBase);
        }
    });
}

let currentActiveSubjectData = null;
let currentActiveSubjectColor = null;

function buildSyllabusTab(transcripts) {
    currentActiveSubjectData = null;
    currentActiveSubjectColor = null;
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
                    <p style="margin-bottom: 4px; font-weight: 600; color: var(--subject-color, var(--primary));">Ã˜Â§Ã™â€žÃ˜Â¯Ã˜Â±Ã™Ë†Ø³: ${data.lessons.length}</p>
                    <p style="color: var(--text-2); font-size: 13px;">Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â­Ã˜Â§Ã™Ë†Ø± Ã˜Â§Ã™â€žÃ™â€¦Ã™â€ Ø¬Ø²Ø©: ${completedBlocks}/${totalBlocks}</p>
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
            subjHeader.innerHTML = `<h3>${data.label}</h3><span class="chev">Ã¢â€“Â¼</span>`;
            
            const subjContent = document.createElement('div');
            subjContent.className = 'subject-content subject-list';
            
            data.lessons.forEach(l => {
                let html = `<div style="background:var(--bg); border-radius:12px; margin-bottom:10px; overflow:hidden;">
                    <div style="padding:12px; background:var(--surface); border-bottom:1px solid var(--border-color); font-weight:bold; display:flex; justify-content:space-between; align-items:center;" onclick="openLessonFromList('${l.subject}', ${l.lessonNum})">
                        <span>Ã˜Â§Ã™â€žØ¯Ø±Ø³ ${l.lessonNum} - ${l.title || ''}</span>
                    </div>
                    <div style="padding:10px;">`;
                
                if (l.thematic_blocks && l.thematic_blocks.length) {
                    l.thematic_blocks.forEach((b, idx) => {
                        const compKey = `${l.subject}_${l.lessonNum}_${idx}`;
                        const isComp = !!syllabusCompletion[compKey];
                        html += `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px; background:white; margin-bottom:6px; border-radius:8px; border:1px solid ${isComp ? 'var(--primary)' : 'var(--border-color)'};">
                            <button onclick="toggleChapterCompletion(event, '${l.subject}', ${l.lessonNum}, ${idx})" style="width:24px; height:24px; border-radius:50%; border:2px solid ${isComp ? 'var(--primary)' : '#cbd5e1'}; background:${isComp ? 'var(--primary)' : 'none'}; color:white; font-size:12px; cursor:pointer; display:flex; justify-content:center; align-items:center; flex-shrink:0;">${isComp ? 'Ã¢Å“â€œ' : ''}</button>
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
    currentActiveSubjectData = data;
    currentActiveSubjectColor = colorClass;
    const listContainer = document.getElementById('subjects-list');
    listContainer.innerHTML = '';
    
    const header = document.createElement('div');
    header.className = `subject-detail-header ${colorClass}`;
    header.innerHTML = `
        <button class="back-btn" onclick="buildSyllabusTab(DB)">Ã˜Â±Ã˜Â¬Ã™Ë†Ø¹ Ã¢Å¾Â¡Ã¯Â¸Â</button>
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
        }
        let p = total > 0 ? (comp / total) * 100 : 0;
        let deg = (p / 100) * 360;
        const isComplete = comp > 0 && comp === total;
        
        const btn = document.createElement('button');
        btn.className = `smart-lesson-btn ${colorClass} ${p === 100 ? 'completed' : ''}`;
        
        let badgeHtml = '';
        if (total > 0) {
            if (isComplete) {
                badgeHtml = `<div style="font-size: 11px; font-weight: bold; color: var(--success, #10b981); background: rgba(16, 185, 129, 0.1); padding: 2px 6px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; width: 100%; box-sizing: border-box; margin-top: 4px; line-height: 1.2;">Ã¢Å“â€¦ ${comp}/${total} Ã™â€¦Ã˜Â­Ã˜Â§Ã™Ë†Ø±</div>`;
            } else if (comp > 0) {
                badgeHtml = `<div style="font-size: 11px; font-weight: bold; color: var(--subject-color, var(--primary, var(--accent-color))); background: rgba(0, 0, 0, 0.05); padding: 2px 6px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; width: 100%; box-sizing: border-box; margin-top: 4px; line-height: 1.2;">Ã¢â€“Â¶Ã¯Â¸Â ${comp}/${total} Ã™â€¦Ã˜Â­Ã˜Â§Ã™Ë†Ø±</div>`;
            } else {
                badgeHtml = `<div style="font-size: 11px; font-weight: bold; color: var(--text-3); background: rgba(0, 0, 0, 0.05); padding: 2px 6px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; width: 100%; box-sizing: border-box; margin-top: 4px; line-height: 1.2;">${total} Ã™â€¦Ã˜Â­Ã˜Â§Ã™Ë†Ø±</div>`;
            }
        }

        let ringStyle = p === 100 
            ? `background: var(--subject-color, var(--primary, var(--accent-color)));` 
            : `background: conic-gradient(var(--subject-color, var(--primary, var(--accent-color))) ${deg}deg, var(--surface-2) 0deg);`;

        btn.innerHTML = `
            <div class="ring" style="${ringStyle}">
                <div class="inner">${l.lessonNum}</div>
            </div>
            ${badgeHtml}
        `;
        
        btn.onclick = () => {
            openLessonPreview(l);
        };
        grid.appendChild(btn);
    });
    
    listContainer.appendChild(grid);
}



// YouTube Player Setup
function onYouTubeIframeAPIReady() {
    // API ready
}

function initYouTubePlayer(videoId) {
    if (player && typeof player.loadVideoById === 'function') {
        let start = pendingSeekTime || 0;
        player.loadVideoById({'videoId': videoId, 'startSeconds': start});
        player.playVideo();
        pendingSeekTime = null;
    } else {
        player = new YT.Player('youtube-player', {
            height: '100%',
            width: '100%',
            videoId: videoId,
            playerVars: {
                'playsinline': 1,
                'rel': 0,
                'controls': 1,
                'autoplay': 1,
                'modestbranding': 1,
                'showinfo': 0,
                'start': pendingSeekTime || 0
            },
            events: {
                'onReady': (e) => {
                    e.target.playVideo();
                    pendingSeekTime = null;
                }
            }
        });
    }
}
function renderLessonHeader(lesson) {
    function extractYoutubeId(url) { if(!url) return null; let match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^&\n\?#]+)/); return (match && match[1]) || null; }
    const videoId = extractYoutubeId(lesson.video_url || lesson.videoLink || lesson.url);
    const videoWrapper = document.getElementById('video-wrapper');
    if (!videoId) {
        videoWrapper.innerHTML = '<div style="background:#1e293b; color:white; height:100%; display:flex; align-items:center; justify-content:center; flex-direction:column;"><span style="font-size:32px;margin-bottom:8px;">Ã°Å¸Å½Â¥</span><span style="font-size:14px;">Ã˜Â§Ã™â€žÃ™ÂÃ™Å Ã˜Â¯Ã™Å Ã™Ë† Ã˜ÂºÃ™Å Ø± Ã™â€¦Ã˜ÂªÃ™Ë†Ã™ÂØ± Ã™â€žÃ™â€¡Ø°Ø§ Ã˜Â§Ã™â€žØ¯Ø±Ø³</span></div>';
    } else {
        if (!document.getElementById('youtube-player')) {
            videoWrapper.innerHTML = '<div id="youtube-player"></div>';
        }
        if (window.YT && window.YT.Player) {
            initYouTubePlayer(videoId);
        } else {
            // API non prÃƒÂªte
            const interval = setInterval(() => {
                if (window.YT && window.YT.Player) {
                    initYouTubePlayer(videoId);
                    clearInterval(interval);
                }
            }, 500);
        }
    }
}

function prepareThematicData(lesson) {
    thematicData = [];
    if (!lesson.segments || lesson.segments.length === 0) {
        // Fallback if no segments
        thematicData.push({
            title: "LeÃƒÂ§on complÃƒÂ¨te",
            startTime: 0,
            endTime: 99999,
            htmlContent: `<div class="reader-paragraph">${lesson.full_text || lesson.summary}</div>`,
            questions: lesson.quiz || []
        });
        return;
    }

    let blocks = lesson.thematic_blocks || [];
    if(blocks.length === 0) {
        blocks = [{ title: "Partie 1", start_seconds: 0, end_seconds: 99999 }];
    }

    let questions = lesson.quiz ? [...lesson.quiz] : [];

    blocks.forEach((block, idx) => {
        // Determine end time securely
        let nextStart = (idx < blocks.length - 1) ? blocks[idx+1].start_seconds : 99999;
        
        // Find segments for this block
        let blockSegments = lesson.segments.filter(s => s.sec >= block.start_seconds && s.sec < nextStart);
        
        let htmlContent = "";

        // Extract tags [POEME:X] shatr 1 *** shatr 2 [/POEME] or just [POEME] shatr 1 *** shatr 2 [/POEME]
        const poetryRegex = /\[POEME(?::(\d+))?\](.*?)\[\/POEME\]/g;

        let parts = [];
        let lastIndex = 0;
        let match;

        let blockText = blockSegments.map(s => `[[TS:${s.sec}]]${s.text}`).join(' ');
        let lastTs = block.start_seconds || 0;
        
        function injectKaraokeSpans(htmlString) {
            let initialTs = lastTs;
            let res = htmlString.replace(/\[\[TS:(\d+(?:\.\d+)?)\]\]/g, (match, sec) => {
                lastTs = sec;
                return `</span><span class="karaoke-segment" data-start="${sec}">`;
            });
            if (res.startsWith('</span>')) {
                res = res.substring(7);
            } else {
                res = `<span class="karaoke-segment" data-start="${initialTs}">` + res;
            }
            res = res + `</span>`;
            // Clean up empty spans
            res = res.replace(/<span[^>]*>\s*<\/span>/g, '');
            return res;
        }

        while ((match = poetryRegex.exec(blockText)) !== null) {
            const prose = blockText.substring(lastIndex, match.index);
            if (prose) parts.push({ type: 'prose', content: prose });
            
            // Inside the tag, we expect *** to separate the two halves, but it's optional in case they write a 1 line quote.
            let innerText = match[2].trim();
            let s1 = innerText, s2 = '';
            if (innerText.includes('***')) {
                let split = innerText.split('***');
                s1 = split[0].trim();
                s2 = split[1].trim();
            }
            
            parts.push({
                type: 'poetry',
                num: match[1] || null,
                shatr1: s1,
                shatr2: s2
            });
            lastIndex = poetryRegex.lastIndex;
        }

        if (lastIndex < blockText.length) {
            parts.push({ type: 'prose', content: blockText.substring(lastIndex) });
        }
        if (parts.length === 0) {
            parts.push({ type: 'prose', content: blockText });
        }

        parts.forEach(part => {
            if (part.type === 'prose') {
                if (!part.content.trim()) return;
                
                // Group sentences into paragraphs of ~4 sentences for better readability
                let sentences = part.content.match(/[^.!?]+[.!?]*/g) || [part.content];
                let pText = "";
                let pCount = 0;
                
                sentences.forEach(sentence => {
                    pText += sentence.trim() + " ";
                    pCount++;
                    if (pCount >= 4) {
                        htmlContent += `<div class="reader-paragraph">${injectKaraokeSpans(formatProse(pText))}</div>`;
                        pText = "";
                        pCount = 0;
                    }
                });
                if (pText.trim() !== "") {
                    htmlContent += `<div class="reader-paragraph">${injectKaraokeSpans(formatProse(pText))}</div>`;
                }
            } else {
                const s1 = injectKaraokeSpans(formatProse(part.shatr1.trim()));
                const s2 = part.shatr2 ? injectKaraokeSpans(formatProse(part.shatr2.trim())) : '';
                const numBadge = part.num ? `<div style="position: absolute; top: -14px; right: 20px; background: var(--gold, #d4af37); color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 2px solid white;">Ã˜Â¨Ã™Å Øª ${part.num}</div>` : '';
                
                htmlContent += `
                <div class="poetry-verse-container" style="position: relative; margin: 28px auto 18px auto; max-width: 90%; direction: rtl; text-align: center;">
                    ${numBadge}
                    <div class="poetry-verse" style="background: #fffdf5; border: 1.1px solid #f2e7c9; border-radius: 14px; padding: 16px 16px 12px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); font-family: 'Amiri', serif; line-height: 1.8; display: inline-block; width: 100%; box-sizing: border-box; margin-top: ${part.num ? '8px' : '0'};">
                        <div class="shatr" style="font-size: 16.5px; font-weight: 700; color: #854d0e; margin-bottom: ${s2 ? '6px' : '0'}; text-align: center;">${s1}</div>
                        ${s2 ? `<div class="shatr" style="font-size: 16.5px; font-weight: 700; color: #854d0e; text-align: center;">${s2}</div>` : ''}
                    </div>
                </div>`;
            }
        });

        if (block.explanation && block.explanation.trim() !== "") {
            htmlContent += `
            <div class="reader-chapter-explanation">
                <div class="explanation-header">
                    <span class="explanation-icon">Ã°Å¸â€™Â¡</span>
                    <span class="explanation-title">Ã˜ÂªÃ™Ë†Ã˜Â¬Ã™Å Ã™â€¡ Ã™Ë†Ã™ÂØ§Ø¦Ø¯Ø© (Note du Professeur)</span>
                </div>
                <div class="explanation-content">${block.explanation}</div>
            </div>`;
        }

        // Find questions for this block
        let blockQuestions = [];
        for (let i = questions.length - 1; i >= 0; i--) {
            let q = questions[i];
            let qTimeSec = extractSecondsFromExplanation(q.explanation);
            
            // Assign question to this block if its time falls within, or if we couldn't parse time and it's the last block
            if ((qTimeSec >= block.start_seconds && qTimeSec < nextStart) || 
                (idx === blocks.length - 1 && qTimeSec === -1)) {
                blockQuestions.push(q);
                questions.splice(i, 1);
            }
        }

        thematicData.push({
            title: block.title,
            level: block.level || 1,
            startTime: block.start_seconds,
            endTime: nextStart,
            htmlContent: htmlContent,
            questions: blockQuestions.reverse()
        });
    });
}

function renderTabs() {
    renderSommaire();
}

function renderSommaire() {
    const listContainer = document.getElementById('sommaire-list');
    if (!listContainer) return;
    listContainer.innerHTML = '';
    
    const sheetTitle = document.querySelector('#sommaire-sheet .bottom-sheet-header h3');
    if (sheetTitle && currentLessonData) {
        sheetTitle.textContent = `Ã™â€¦Ã˜Â­Ã˜Â§Ã™Ë†Ø± Ã˜Â§Ã™â€žØ¯Ø±Ø³ ${currentLessonData.lessonNum}`;
    }

    thematicData.forEach((data, index) => {
        let item = document.createElement('div');
        item.className = 'theme-item';
        if (data.level === 2) item.classList.add('level-2');
        
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.justifyContent = 'space-between';
        
        const compKey = `${currentLessonData.subject}_${currentLessonData.lessonNum}_${index}`;
        let isComp = !!syllabusCompletion[compKey];
        
        item.innerHTML = `<span style="flex:1; text-align:right;">${index + 1}. ${data.title}</span>`;
        
        let checkBtn = document.createElement('button');
        checkBtn.className = 'sommaire-check-btn ' + (isComp ? 'completed' : '');
        checkBtn.innerHTML = isComp ? 'Ã¢Å“â€œ' : '';
        checkBtn.onclick = (e) => {
            e.stopPropagation();
            isComp = !isComp;
            syllabusCompletion[compKey] = isComp;
            localStorage.setItem('academy_syllabus_completions', JSON.stringify(syllabusCompletion));
            checkBtn.className = 'sommaire-check-btn ' + (isComp ? 'completed' : '');
            checkBtn.innerHTML = isComp ? 'Ã¢Å“â€œ' : '';
            
            updateDashboardProgress();
            
            if (currentTabIndex === index) {
                const vBtn = document.querySelector('.validate-chapter-btn');
                if (vBtn) {
                    vBtn.className = isComp ? 'validate-chapter-btn completed' : 'validate-chapter-btn';
                    vBtn.innerHTML = isComp ? 'Ã¢Å“â€œ Ã˜ÂªÃ™â€¦ Ã˜Â¥Ã™â€ Ø¬Ø§Ø² Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â­Ã™Ë†Ø±' : 'Ã˜ÂªÃ˜Â¹Ã™â€žÃ™Å Ã™â€¦ Ã™Æ’Ã™â€¦Ã™â€šÃ˜Â±Ã™Ë†Ø¡';
                }
            }
        };
        
        item.appendChild(checkBtn);
        
        item.onclick = (e) => {
            if (e.target === checkBtn) return;
            switchThemeTab(index, true);
            document.getElementById('sommaire-overlay').classList.remove('show');
            document.getElementById('sommaire-sheet').classList.remove('open');
        };
        listContainer.appendChild(item);
    });
}

function switchThemeTab(index, shouldSeek = true) {
    if (index < 0 || index >= thematicData.length) return;
    
    currentTabIndex = index;
    const data = thematicData[index];

    // Update bottom sheet label and active state
    const labelEl = document.getElementById('current-theme-label');
    if (labelEl) {
        labelEl.textContent = data.title;
    }

    const items = document.querySelectorAll('.theme-item');
    items.forEach((item, i) => {
        if (i === index) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Render Content
    const contentArea = document.getElementById('reader-content');
    contentArea.innerHTML = ''; // Clear

    let contentDiv = document.createElement('div');
    contentDiv.className = 'tab-content active';
    
    // Course Badge (Lesson X - Subject)
    if (currentSubject && currentLessonNum) {
        let courseBadge = document.createElement('div');
        courseBadge.style.fontSize = '12px';
        courseBadge.style.color = 'var(--text-3)';
        courseBadge.style.marginBottom = '6px';
        const subjLabel = SUBJECT_LABELS[currentSubject] || currentSubject;
        courseBadge.textContent = `${subjLabel} Ã¢â‚¬Â¢ Ã˜Â§Ã™â€žØ¯Ø±Ø³ ${currentLessonNum}`;
        contentDiv.appendChild(courseBadge);
    }

    // Title
    let titleEl = document.createElement('h2');
    if (data.level === 2) {
        titleEl.className = 'sub-theme-title';
    } else {
        titleEl.className = 'thematic-title';
    }
    titleEl.textContent = data.title;
    contentDiv.appendChild(titleEl);

    // Text
    let textWrapper = document.createElement('div');
    textWrapper.innerHTML = data.htmlContent;
    contentDiv.appendChild(textWrapper);

    // Questions
    data.questions.forEach(q => {
        contentDiv.appendChild(createQuizElement(q));
    });

    // Finish Thematic Button
    if (currentSubject && currentLessonNum) {
        let finishBtnWrapper = document.createElement('div');
        finishBtnWrapper.style.marginTop = '24px';
        finishBtnWrapper.style.marginBottom = '12px';
        let finishBtn = document.createElement('button');
        finishBtn.className = 'finish-theme-btn';
        finishBtn.innerHTML = 'Ã¢Å“â€¦ Ã˜Â£Ã™Æ’Ã™â€¦Ã™â€žØª Ã™â€¡Ø°Ø§ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â­Ã™Ë†Ø±';
        finishBtn.onclick = (e) => {
            toggleChapterCompletion(e, currentSubject, currentLessonNum, index);
            if (finishBtn.classList.contains('completed')) {
                finishBtn.classList.remove('completed');
                finishBtn.innerHTML = 'Ã¢Å“â€¦ Ã˜Â£Ã™Æ’Ã™â€¦Ã™â€žØª Ã™â€¡Ø°Ø§ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â­Ã™Ë†Ø±';
                finishBtn.style.background = 'var(--surface)';
                finishBtn.style.color = 'var(--text)';
            } else {
                finishBtn.classList.add('completed');
                finishBtn.innerHTML = 'Ã¢Å“â€Ã¯Â¸Â Ã˜ÂªÃ™â€¦ Ã˜Â¥Ã™â€ Ø¬Ø§Ø² Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â­Ã™Ë†Ø±';
                finishBtn.style.background = 'var(--success, #10b981)';
                finishBtn.style.color = 'white';
            }
        };
        
        // Check if already completed
        const compKey = `${currentSubject}_${currentLessonNum}_${index}`;
        if (syllabusCompletion[compKey]) {
            finishBtn.classList.add('completed');
            finishBtn.innerHTML = 'Ã¢Å“â€Ã¯Â¸Â Ã˜ÂªÃ™â€¦ Ã˜Â¥Ã™â€ Ø¬Ø§Ø² Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â­Ã™Ë†Ø±';
            finishBtn.style.background = 'var(--success, #10b981)';
            finishBtn.style.color = 'white';
        } else {
            finishBtn.style.background = 'var(--surface)';
            finishBtn.style.color = 'var(--text)';
            finishBtn.style.border = '1px solid var(--border-color)';
        }
        
        finishBtn.style.width = '100%';
        finishBtn.style.padding = '14px';
        finishBtn.style.borderRadius = '12px';
        finishBtn.style.fontWeight = 'bold';
        finishBtn.style.cursor = 'pointer';
        finishBtn.style.transition = 'all 0.3s';
        
        finishBtnWrapper.appendChild(finishBtn);
        contentDiv.appendChild(finishBtnWrapper);
    }

    // Next Button
    if (index < thematicData.length - 1) {
        let nextBtnWrapper = document.createElement('div');
        nextBtnWrapper.className = 'next-tab-wrapper';
        
        let nextBtn = document.createElement('button');
        nextBtn.className = 'next-tab-btn';
        nextBtn.innerHTML = `Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â§Ã™â€žÙŠ: ${thematicData[index+1].title} Ã¢Â¬â€¦Ã¯Â¸Â`;
        nextBtn.onclick = () => switchThemeTab(index + 1, true);
        
        nextBtnWrapper.appendChild(nextBtn);
        contentDiv.appendChild(nextBtnWrapper);
    }


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
        markBtn.textContent = 'Ã¢Å“â€œ Ã™â€¦Ã™Æ’Ã˜ÂªÃ™â€¦Ã™â€ž';
        markBtn.disabled = true;
    } else {
        markBtn.style.background = 'var(--primary)';
        markBtn.style.color = 'white';
        markBtn.textContent = 'Ã¢Å“â€¦ Ã˜Â¥Ã™â€ Ã™â€¡Ø§Ø¡ Ã™â€¡Ø°Ø§ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â­Ã™Ë†Ø±';
        markBtn.onclick = () => {
            if (currentLessonData) {
                toggleChapterCompletion(null, currentLessonData.subject, currentLessonData.lessonNum, index);
                markBtn.style.background = '#e2e8f0';
                markBtn.style.color = '#64748b';
                markBtn.textContent = 'Ã¢Å“â€œ Ã™â€¦Ã™Æ’Ã˜ÂªÃ™â€¦Ã™â€ž';
                markBtn.disabled = true;
                
                // Show completion toast or visual effect
                let tst = document.createElement('div');
                tst.textContent = 'Ã˜ÂªÃ™â€¦ Ã˜ÂªÃ˜Â³Ã˜Â¬Ã™Å Ã™â€ž Ã˜Â§Ã™â€žÃ˜ÂªÃ™â€šÃ˜Â¯Ã™â€¦!';
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

    // --- NEW: Add "Practice Lesson" button at the end ---
    if (currentSubject && currentLessonNum) {
        let practiceBtnWrapper = document.createElement('div');
        practiceBtnWrapper.style.marginTop = '12px';
        practiceBtnWrapper.style.marginBottom = '24px';
        let practiceBtn = document.createElement('button');
        practiceBtn.innerHTML = 'Ã°Å¸Å½Â¯ Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â¯Ã˜Â±Ã™Å Ø¨ Ã˜Â¹Ã™â€žÃ™â€° Ã™â€¡Ø°Ø§ Ã˜Â§Ã™â€žØ¯Ø±Ø³';
        practiceBtn.style.background = 'var(--primary)';
        practiceBtn.style.color = 'white';
        practiceBtn.style.border = 'none';
        practiceBtn.style.width = '100%';
        practiceBtn.style.padding = '14px';
        practiceBtn.style.borderRadius = '12px';
        practiceBtn.style.fontWeight = 'bold';
        practiceBtn.style.cursor = 'pointer';
        practiceBtn.style.fontSize = '16px';
        practiceBtn.style.boxShadow = '0 4px 10px rgba(79, 70, 229, 0.2)';
        practiceBtn.onclick = () => {
            switchTab('practice');
        };
        practiceBtnWrapper.appendChild(practiceBtn);
        contentDiv.appendChild(practiceBtnWrapper);
    }

    contentArea.appendChild(contentDiv);

    // Video Seek
    if (shouldSeek && player && player.seekTo) {
        isSeekingTab = true;
        player.seekTo(data.startTime, true);
        player.playVideo();
        setTimeout(() => { isSeekingTab = false; }, 1500);
        // Scroll to video
        window.scrollTo({top: 0, behavior: 'smooth'});
    } else if (shouldSeek) {
        window.scrollTo({top: 0, behavior: 'smooth'});
    }
}

function createQuizElement(questionData) {
    const container = document.createElement('div');
    container.className = 'inline-quiz-container';

    let optionsHtml = '';
    let opts = Array.isArray(questionData.options) ? questionData.options : 
               (typeof questionData.options === 'string' ? questionData.options.split(/[.-]/).map(s=>s.trim()).filter(s=>s) : []);
    
    opts.forEach((opt, optIdx) => {
        optionsHtml += `<button class="quiz-option" data-idx="${optIdx}">${opt}</button>`;
    });

    let tempDiv = document.createElement('div');
    tempDiv.innerHTML = questionData.explanation || '';
    let cleanExplanation = tempDiv.textContent || tempDiv.innerText || '';
    // Parse explanation like Telegram
    let text = cleanExplanation.trim();
    let sourceText = "";
    if (text.includes("Ã°Å¸â€œÂ")) {
        let parts = text.split("Ã°Å¸â€œÂ");
        text = parts[0].trim();
        sourceText = "Ã°Å¸â€œÂ " + parts[1].trim();
    } else if (text.includes("Ã˜Â§Ã™â€žÃ™â€¦ØµØ¯Ø±")) {
        let parts = text.split("Ã˜Â§Ã™â€žÃ™â€¦ØµØ¯Ø±");
        text = parts[0].trim();
        sourceText = "Ã°Å¸â€œÂ Ã˜Â§Ã™â€žÃ™â€¦ØµØ¯Ø± " + parts[1].trim();
    }

    let profNote = "";
    const profPatterns = ["Ã˜ÂªÃ™Ë†Ã˜Â¬Ã™Å Ã™â€¡ Ã™Ë†Ã™ÂØ§Ø¦Ø¯Ø© :", "Ã™â€¦Ã™â€žØ§Ø­Ø¸Ø© Ã˜Â§Ã™â€žØ£Ø³ØªØ§Ø° :", "Ã™ÂØ§Ø¦Ø¯Ø© :"];
    for (let p of profPatterns) {
        if (text.includes(p)) {
            let parts = text.split(p);
            text = parts[0].trim();
            profNote = parts[1].trim();
            break;
        }
    }

    let parsedHtml = '';
    if (text) {
        parsedHtml += `<div class="exp-main" style="margin-bottom:12px; font-size:14px;"><strong>Ã˜Â§Ã™â€žÃ˜ÂªÃ™Ë†Ã˜Â¶Ã™Å Ø­:</strong><br>${text}</div>`;
    }
    if (profNote) {
        parsedHtml += `<div class="exp-prof" style="margin-bottom:12px; background:var(--surface-2); padding:12px; border-radius:8px; border-right:3px solid var(--primary); font-size:13.5px;"><span style="font-size:16px;">Ã°Å¸â€™Â¡</span> <strong>Ã˜ÂªÃ™Ë†Ã˜Â¬Ã™Å Ã™â€¡ Ã™Ë†Ã™ÂØ§Ø¦Ø¯Ø©:</strong><br>${profNote}</div>`;
    }
    if (sourceText) {
        parsedHtml += `<div class="exp-source" style="font-size:12px; color:var(--text-3); margin-top:8px;">${sourceText}</div>`;
    }

    container.innerHTML = `
        <div class="quiz-header">Ã˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž Ã˜ÂªÃ™ÂÃ˜Â§Ã˜Â¹Ã™â€žÙŠ</div>
        <div class="quiz-question">${questionData.question}</div>
        <div class="quiz-options">
            ${optionsHtml}
        </div>
        <div class="quiz-explanation">
            ${parsedHtml}
        </div>
    `;

    const buttons = container.querySelectorAll('.quiz-option');
    const expDiv = container.querySelector('.quiz-explanation');

    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            if (container.classList.contains('answered')) return;
            container.classList.add('answered');

            let correctIdx = questionData.answerIndex; 
            if (correctIdx === undefined && questionData.correct) {
                correctIdx = questionData.correct - 1;
            }

            buttons.forEach(b => {
                const bIdx = parseInt(b.getAttribute('data-idx'));
                if (bIdx === correctIdx) {
                    b.classList.add('correct');
                } else if (bIdx === parseInt(btn.getAttribute('data-idx'))) {
                    b.classList.add('wrong');
                }
            });

            expDiv.classList.add('show');
        });
    });

    return container;
}

function extractVideoID(url) {
    let match = url.match(/[?&]v=([^&]+)/);
    if (match) return match[1];
    match = url.match(/youtu\.be\/([^?]+)/);
    if (match) return match[1];
    return null;
}

function extractSecondsFromExplanation(html) {
    if (!html) return -1;
    let match = html.match(/&t=(\d+)s/);
    if (match) {
        return parseInt(match[1]);
    }
    return -1;
}

// Ã¢â€â‚¬Ã¢â€â‚¬ RICH TEXT PARSERS Ã¢â€â‚¬Ã¢â€â‚¬
function formatProse(text) {
    if (!text) return '';
    let result = text;
    // Quranic verses inside {}
    result = result.replace(/\{([^{}]+)\}/g, (match, verse) => {
        const cleanVerse = verse.trim();
        return `<span class="quran-verse">Ã¯Â´Â¿ ${cleanVerse} Ã¯Â´Â¾</span>`;
    });
    result = highlightGlossary(result);
    return result;
}

function highlightGlossary(text) {
    let result = text;
    
    // Order matters: longer/more specific patterns first to avoid partial matches
    const GLOSSARY_MATCHERS = [
        // Ã¢â€â‚¬Ã¢â€â‚¬ Ã™â€ Ø³Ø§Ø¡ (rose/pink) Ã¢â€â‚¬Ã¢â€â‚¬
        { term: "Ã˜Â®Ã˜Â¯Ã™Å Ø¬Ø© Ã˜Â¨Ã™â€ Øª Ã˜Â®Ã™Ë†Ã™Å Ã™â€žØ¯",         pattern: "Ã˜Â®Ã˜Â¯Ã™Å Ø¬[Ã˜Â©Ã™â€¡] Ã˜Â¨Ã™â€ Øª Ã˜Â®Ã™Ë†Ã™Å Ã™â€žØ¯|Ã˜Â®Ã˜Â¯Ã™Å Ø¬[Ã˜Â©Ã™â€¡] Ã˜Â±Ã˜Â¶Ã™Å  Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¹Ã™â€ Ã™â€¡Ø§|Ã˜Â®Ã˜Â¯Ã™Å Ø¬[Ã˜Â©Ã™â€¡]" },
        { term: "Ø¹Ø§Ø¦Ø´Ø© Ã˜Â¨Ã™â€ Øª Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â¨Ã™Æ’Ø±",        pattern: "Ø¹Ø§Ø¦Ø´[Ã˜Â©Ã™â€¡] Ã˜Â¨Ã™â€ Øª [Ø£Ø§]Ã˜Â¨Ã™Å  Ã˜Â¨Ã™Æ’Ø±|Ø¹Ø§Ø¦Ø´[Ã˜Â©Ã™â€¡] Ã˜Â±Ã˜Â¶Ã™Å  Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¹Ã™â€ Ã™â€¡Ø§|Ø¹Ø§Ø¦Ø´[Ã˜Â©Ã™â€¡]|Ã˜Â§Ã™â€žÃ˜Â³Ã™Å Ø¯Ø© Ø¹Ø§Ø¦Ø´[Ã˜Â©Ã™â€¡]" },
        { term: "Ã™ÂÃ˜Â§Ã˜Â·Ã™â€¦Ø© Ã˜Â§Ã™â€žÃ˜Â²Ã™â€¡Ø±Ø§Ø¡",            pattern: "Ã™ÂÃ˜Â§Ã˜Â·Ã™â€¦[Ã˜Â©Ã™â€¡] Ã˜Â§Ã™â€žÃ˜Â²Ã™â€¡Ø±Ø§Ø¡|Ã™ÂÃ˜Â§Ã˜Â·Ã™â€¦[Ã˜Â©Ã™â€¡] Ã˜Â¨Ã™â€ Øª Ã™â€¦Ã˜Â­Ã™â€¦Ø¯|Ã™ÂÃ˜Â§Ã˜Â·Ã™â€¦[Ã˜Â©Ã™â€¡]" },
        { term: "Ã˜Â²Ã™Å Ã™â€ Ø¨ Ã˜Â¨Ã™â€ Øª Ø¬Ø­Ø´",            pattern: "Ã˜Â²Ã™Å Ã™â€ Ø¨ Ã˜Â¨Ã™â€ Øª Ø¬Ø­Ø´|Ã˜Â§Ã™â€žÃ˜Â³Ã™Å Ø¯Ø© Ã˜Â²Ã™Å Ã™â€ Ø¨" },
        { term: "Ã˜Â²Ã™Å Ã™â€ Ø¨ Ã˜Â¨Ã™â€ Øª Ã™â€¦Ã˜Â­Ã™â€¦Ø¯",            pattern: "Ã˜Â²Ã™Å Ã™â€ Ø¨ Ã˜Â¨Ã™â€ Øª Ã™â€¦Ã˜Â­Ã™â€¦Ø¯|Ã˜Â²Ã™Å Ã™â€ Ø¨ Ã˜Â¨Ã™â€ Øª Ã˜Â§Ã™â€žÃ™â€ Ø¨ÙŠ|Ã˜Â²Ã™Å Ã™â€ Ø¨" },
        { term: "Ã˜Â£Ã™â€¦ Ã˜Â³Ã™â€žÃ™â€¦Ø©",                 pattern: "[Ø£Ø§]Ã™â€¦ Ã˜Â³Ã™â€žÃ™â€¦[Ã˜Â©Ã™â€¡]|Ã™â€¡Ã™â€ Ø¯ Ã˜Â¨Ã™â€ Øª [Ø£Ø§]Ã˜Â¨Ã™Å  [Ø£Ø§]Ã™â€¦Ã™Å [Ã˜Â©Ã™â€¡]" },
        { term: "Ã˜ÂµÃ™ÂÃ™Å Ø© Ã˜Â¨Ã™â€ Øª Ã˜Â­Ã™Å Ã™Å ",            pattern: "Ã˜ÂµÃ™ÂÃ™Å [Ã˜Â©Ã™â€¡] Ã˜Â¨Ã™â€ Øª Ø­ÙŠÙŠ|Ã˜ÂµÃ™ÂÃ™Å [Ã˜Â©Ã™â€¡]" },
        { term: "Ã˜Â­Ã™ÂØµØ© Ã˜Â¨Ã™â€ Øª Ã˜Â¹Ã™â€¦Ø±",            pattern: "Ã˜Â­Ã™ÂØµ[Ã˜Â©Ã™â€¡] Ã˜Â¨Ã™â€ Øª Ã˜Â¹Ã™â€¦Ø±|Ã˜Â­Ã™ÂØµ[Ã˜Â©Ã™â€¡]" },
        { term: "Ã˜Â±Ã™â€šÃ™Å Ø© Ã˜Â¨Ã™â€ Øª Ã™â€¦Ã˜Â­Ã™â€¦Ø¯",            pattern: "Ã˜Â±Ã™â€šÃ™Å [Ã˜Â©Ã™â€¡] Ã˜Â¨Ã™â€ Øª Ã™â€¦Ã˜Â­Ã™â€¦Ø¯|Ã˜Â±Ã™â€šÃ™Å [Ã˜Â©Ã™â€¡]" },
        { term: "Ã˜Â£Ã™â€¦ Ã™Æ’Ã™â€žÃ˜Â«Ã™Ë†Ã™â€¦ Ã˜Â¨Ã™â€ Øª Ã™â€¦Ã˜Â­Ã™â€¦Ø¯",        pattern: "[Ø£Ø§]Ã™â€¦ Ã™Æ’Ã™â€žÃ˜Â«Ã™Ë†Ã™â€¦ Ã˜Â¨Ã™â€ Øª Ã™â€¦Ã˜Â­Ã™â€¦Ø¯|[Ø£Ø§]Ã™â€¦ Ã™Æ’Ã™â€žÃ˜Â«Ã™Ë†Ã™â€¦" },
        { term: "Ã™â€¡Ã™â€ Ø¯ Ã˜Â¨Ã™â€ Øª Ø¹ØªØ¨Ø©",             pattern: "Ã™â€¡Ã™â€ Ø¯ Ã˜Â¨Ã™â€ Øª Ø¹ØªØ¨[Ã˜Â©Ã™â€¡]|Ã™â€¡Ã™â€ Ø¯" },
        { term: "Ã˜Â£Ã˜Â³Ã™â€¦Ø§Ø¡ Ã˜Â¨Ã™â€ Øª Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â¨Ã™Æ’Ø±",        pattern: "[Ø£Ø§]Ã˜Â³Ã™â€¦Ø§Ø¡ Ã˜Â¨Ã™â€ Øª [Ø£Ø§]Ã˜Â¨Ã™Å  Ã˜Â¨Ã™Æ’Ø±|[Ø£Ø§]Ã˜Â³Ã™â€¦Ø§Ø¡|Ø°Ø§Øª Ã˜Â§Ã™â€žÃ™â€ Ã˜Â·Ã˜Â§Ã™â€šÃ™Å Ã™â€ " },
        { term: "Ã™â€¦Ã˜Â§Ã˜Â±Ã™Å Ø§ Ã˜Â§Ã™â€žÃ™â€šÃ˜Â¨Ã˜Â·Ã™Å Ø©",            pattern: "Ã™â€¦Ã˜Â§Ã˜Â±Ã™Å [Ø©Ø§] Ã˜Â§Ã™â€žÃ™â€šÃ˜Â¨Ã˜Â·Ã™Å [Ã˜Â©Ã™â€¡]|Ã™â€¦Ã˜Â§Ã˜Â±Ã™Å [Ø©Ø§]" },
        // Ã¢â€â‚¬Ã¢â€â‚¬ Ã˜Â±Ã˜Â¬Ã˜Â§Ã™â€ž (bleu) Ã¢â€â‚¬Ã¢â€â‚¬
        { term: "Ã˜Â£Ã˜Â¨Ã™Ë† Ã˜Â¨Ã™Æ’Ø± Ã˜Â§Ã™â€žÃ˜ÂµÃ˜Â¯Ã™Å Ã™â€š",           pattern: "[Ø£Ø§]Ã˜Â¨Ã™Ë† Ã˜Â¨Ã™Æ’Ø± Ã˜Â§Ã™â€žÃ˜ÂµÃ˜Â¯Ã™Å Ã™â€š|Ã˜Â§Ã™â€žÃ˜ÂµÃ˜Â¯Ã™Å Ã™â€š|[Ø£Ø§]Ã˜Â¨Ã™Ë† Ã˜Â¨Ã™Æ’Ø±" },
        { term: "Ã˜Â¹Ã™â€¦Ø± Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žØ®Ø·Ø§Ø¨",            pattern: "Ã˜Â¹Ã™â€¦Ø± Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žØ®Ø·Ø§Ø¨|Ã˜Â§Ã™â€žÃ™ÂÃ˜Â§Ã˜Â±Ã™Ë†Ã™â€š Ã˜Â¹Ã™â€¦Ø±|Ã˜Â¹Ã™â€¦Ø± Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žØ®Ø·Ø§Ø¨|Ã˜Â¹Ã™â€¦Ø±" },
        { term: "Ã˜Â¹Ã˜Â«Ã™â€¦Ã˜Â§Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™ÂÃ˜Â§Ã™â€ ",            pattern: "Ã˜Â¹Ã˜Â«Ã™â€¦Ã˜Â§Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™ÂÃ˜Â§Ã™â€ |Ã˜Â°Ã™Ë† Ã˜Â§Ã™â€žÃ™â€ Ã™Ë†Ã˜Â±Ã™Å Ã™â€ |Ã˜Â¹Ã˜Â«Ã™â€¦Ã˜Â§Ã™â€ " },
        { term: "Ã˜Â¹Ã™â€žÃ™Å  Ã˜Â¨Ã™â€  Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â·Ã˜Â§Ã™â€žØ¨",          pattern: "Ã˜Â¹Ã™â€žÃ™Å  Ã˜Â¨Ã™â€  [Ø£Ø§]Ã˜Â¨Ã™Å  Ã˜Â·Ã˜Â§Ã™â€žØ¨|Ã˜Â¹Ã™â€žÃ™Å  Ã˜Â±Ã˜Â¶Ã™Å  Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¹Ã™â€ Ã™â€¡|Ã˜Â¹Ã™â€žÙŠ" },
        { term: "Ã˜Â®Ã˜Â§Ã™â€žØ¯ Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ™Ë†Ã™â€žÃ™Å Ø¯",           pattern: "Ã˜Â®Ã˜Â§Ã™â€žØ¯ Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ™Ë†Ã™â€žÃ™Å Ø¯|Ã˜Â³Ã™Å Ã™Â Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™Ë†Ã™â€ž|Ã˜Â®Ã˜Â§Ã™â€žØ¯" },
        { term: "Ã˜Â¨Ã™â€žÃ˜Â§Ã™â€ž Ã˜Â¨Ã™â€  Ø±Ø¨Ø§Ø­",             pattern: "Ã˜Â¨Ã™â€žÃ˜Â§Ã™â€ž Ã˜Â¨Ã™â€  Ø±Ø¨Ø§Ø­|Ã˜Â¨Ã™â€žÃ˜Â§Ã™â€ž" },
        { term: "Ã˜Â£Ã˜Â¨Ã™Ë† Ã™â€¡Ã˜Â±Ã™Å Ø±Ø©",               pattern: "[Ø£Ø§]Ã˜Â¨Ã™Ë† Ã™â€¡Ã˜Â±Ã™Å Ø±[Ã˜Â©Ã™â€¡]" },
        { term: "Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€  Ã™â€¦Ã˜Â³Ã˜Â¹Ã™Ë†Ø¯",        pattern: "Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€  Ã™â€¦Ã˜Â³Ã˜Â¹Ã™Ë†Ø¯|Ã˜Â§Ã˜Â¨Ã™â€  Ã™â€¦Ã˜Â³Ã˜Â¹Ã™Ë†Ø¯" },
        { term: "Ã˜Â­Ã™â€¦Ø²Ø© Ã˜Â¨Ã™â€  Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â·Ã™â€žØ¨",       pattern: "Ã˜Â­Ã™â€¦Ø²[Ã˜Â©Ã™â€¡] Ã˜Â¨Ã™â€  Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â·Ã™â€žØ¨|Ã˜Â­Ã™â€¦Ø²[Ã˜Â©Ã™â€¡]" },
        { term: "Ã™â€¦ØµØ¹Ø¨ Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€¦Ã™Å Ø±",            pattern: "Ã™â€¦ØµØ¹Ø¨ Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€¦Ã™Å Ø±|Ã™â€¦ØµØ¹Ø¨" },
        { term: "Ã˜Â¹Ã™â€¦Ã˜Â±Ã™Ë† Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žØ¹Ø§Øµ",            pattern: "Ã˜Â¹Ã™â€¦Ã˜Â±Ã™Ë† Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žØ¹Ø§Øµ|Ã˜Â¹Ã™â€¦Ø±Ùˆ" },
        { term: "Ã˜Â·Ã™â€žØ­Ø© Ã˜Â¨Ã™â€  Ã˜Â¹Ã˜Â¨Ã™Å Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡",        pattern: "Ã˜Â·Ã™â€žØ­[Ã˜Â©Ã™â€¡] Ã˜Â¨Ã™â€  Ã˜Â¹Ã˜Â¨Ã™Å Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡|Ã˜Â·Ã™â€žØ­[Ã˜Â©Ã™â€¡]" },
        { term: "Ã˜Â§Ã™â€žÃ˜Â²Ã˜Â¨Ã™Å Ø± Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ˜Â¹Ã™Ë†Ã˜Â§Ã™â€¦",          pattern: "Ã˜Â§Ã™â€žÃ˜Â²Ã˜Â¨Ã™Å Ø± Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ˜Â¹Ã™Ë†Ã˜Â§Ã™â€¦|Ã˜Â§Ã™â€žÃ˜Â²Ã˜Â¨Ã™Å Ø±" },
        { term: "Ã™Æ’Ø¹Ø¨ Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ˜Â£Ã˜Â´Ã˜Â±Ã™Â",           pattern: "Ã™Æ’Ø¹Ø¨ Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ˜Â£Ã˜Â´Ã˜Â±Ã™Â|Ã™Æ’Ø¹Ø¨" },
        { term: "Ø³Ø¹Ø¯ Ã˜Â¨Ã™â€  Ø¹Ø¨Ø§Ø¯Ø©",            pattern: "Ø³Ø¹Ø¯ Ã˜Â¨Ã™â€  Ø¹Ø¨Ø§Ø¯[Ã˜Â©Ã™â€¡]" },
        { term: "Ã˜Â²Ã™Å Ø¯ Ã˜Â¨Ã™â€  Ø­Ø§Ø±Ø«Ø©",            pattern: "Ã˜Â²Ã™Å Ø¯ Ã˜Â¨Ã™â€  Ø­Ø§Ø±Ø«[Ã˜Â©Ã™â€¡]|Ã˜Â²Ã™Å Ø¯" },
        { term: "Ã˜Â³Ã™â€žÃ™â€¦Ã˜Â§Ã™â€  Ã˜Â§Ã™â€žÃ™ÂÃ˜Â§Ã˜Â±Ã˜Â³Ã™Å ",           pattern: "Ã˜Â³Ã™â€žÃ™â€¦Ã˜Â§Ã™â€  Ã˜Â§Ã™â€žÃ™ÂÃ˜Â§Ã˜Â±Ã˜Â³Ã™Å |Ã˜Â³Ã™â€žÃ™â€¦Ã˜Â§Ã™â€ " },
        { term: "Ø³Ø¹Ø¯ Ã˜Â¨Ã™â€  Ã™â€¦Ø¹Ø§Ø°",             pattern: "Ø³Ø¹Ø¯ Ã˜Â¨Ã™â€  Ã™â€¦Ø¹Ø§Ø°|Ø³Ø¹Ø¯" },
        { term: "Ã˜Â­Ã™Å Ã™Å  Ã˜Â¨Ã™â€  Ø£Ø®Ø·Ø¨",             pattern: "Ã˜Â­Ã™Å Ã™Å  Ã˜Â¨Ã™â€  [Ø£Ø§]Ø®Ø·Ø¨|Ø­ÙŠÙŠ" },
        { term: "Ã™â€ Ã˜Â¹Ã™Å Ã™â€¦ Ã˜Â¨Ã™â€  Ã™â€¦Ã˜Â³Ã˜Â¹Ã™Ë†Ø¯",           pattern: "Ã™â€ Ã˜Â¹Ã™Å Ã™â€¦ Ã˜Â¨Ã™â€  Ã™â€¦Ã˜Â³Ã˜Â¹Ã™Ë†Ø¯|Ã™â€ Ã˜Â¹Ã™Å Ã™â€¦" },
        { term: "Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€  Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦",         pattern: "Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€  Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦|Ã˜Â§Ã˜Â¨Ã™â€  Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦" },
        { term: "Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€  Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â¨Ã™â€  Ã˜Â³Ã™â€žÃ™Ë†Ã™â€ž",  pattern: "Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€  [Ø£Ø§]Ã˜Â¨Ã™Å  Ã˜Â¨Ã™â€  Ã˜Â³Ã™â€žÃ™Ë†Ã™â€ž|Ã˜Â§Ã˜Â¨Ã™â€  Ã˜Â³Ã™â€žÃ™Ë†Ã™â€ž|Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€  [Ø£Ø§]Ø¨ÙŠ" },
        { term: "Ã˜ÂµÃ™ÂÃ™Ë†Ã˜Â§Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¹Ã˜Â·Ã™â€ž",          pattern: "Ã˜ÂµÃ™ÂÃ™Ë†Ã˜Â§Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¹Ã˜Â·Ã™â€ž|Ã˜ÂµÃ™ÂÃ™Ë†Ã˜Â§Ã™â€ " },
        { term: "Ã™Ë†Ã˜Â­Ã˜Â´Ã™Å  Ã˜Â¨Ã™â€  Ø­Ø±Ø¨",             pattern: "Ã™Ë†Ã˜Â­Ã˜Â´Ã™Å  Ã˜Â¨Ã™â€  Ø­Ø±Ø¨|ÙˆØ­Ø´ÙŠ" },
        { term: "Ã˜Â£Ã˜Â¨Ã™Ë† Ã˜Â¬Ã™â€¡Ã™â€ž",                 pattern: "[Ø£Ø§]Ã˜Â¨Ã™Ë† Ã˜Â¬Ã™â€¡Ã™â€ž|Ã™ÂÃ˜Â±Ã˜Â¹Ã™Ë†Ã™â€  [Ø£Ø§]Ã™â€¦Ø©" },
        { term: "Ã˜Â£Ã˜Â¨Ã™Ë† Ã™â€žÃ™â€¡Ø¨",                 pattern: "[Ø£Ø§]Ã˜Â¨Ã™Ë† Ã™â€žÃ™â€¡Ø¨" },
        { term: "Ã˜Â£Ã˜Â¨Ã™Ë† Ã˜Â³Ã™ÂÃ™Å Ã˜Â§Ã™â€ ",               pattern: "[Ø£Ø§]Ã˜Â¨Ã™Ë† Ã˜Â³Ã™ÂÃ™Å Ã˜Â§Ã™â€ |[Ø£Ø§]Ã˜Â¨Ã™Å  Ã˜Â³Ã™ÂÃ™Å Ã˜Â§Ã™â€ |[Ø£Ø§]Ø¨Ø§ Ã˜Â³Ã™ÂÃ™Å Ã˜Â§Ã™â€ " },
        { term: "Ã˜Â£Ã™â€¦Ã™Å Ø© Ã˜Â¨Ã™â€  Ã˜Â®Ã™â€žÃ™Â",             pattern: "[Ø£Ø§]Ã™â€¦Ã™Å [Ã˜Â©Ã™â€¡] Ã˜Â¨Ã™â€  Ã˜Â®Ã™â€žÃ™Â" },
        { term: "Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€žÃ™Å ",            pattern: "Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€žÙŠ|Ã˜Â§Ã™â€žØ³Ø¨Ø· Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™â€ |Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™â€ " },
        { term: "Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™Å Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€žÃ™Å ",           pattern: "Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™Å Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€žÙŠ|Ã˜Â§Ã™â€žØ³Ø¨Ø· Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™Å Ã™â€ |Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™Å Ã™â€ " },
        { term: "Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¬Ã˜Â§Ã˜Â´Ã™Å ",                 pattern: "Ã˜Â§Ã™â€žÃ™â€ Ø¬Ø§Ø´ÙŠ|Ã™â€ Ã˜Â¬Ã˜Â§Ã˜Â´Ã™Å  Ã˜Â§Ã™â€žØ­Ø¨Ø´[Ã˜Â©Ã™â€¡]" },
        // Ã¢â€â‚¬Ã¢â€â‚¬ Ã™â€šÃ˜Â¨Ã˜Â§Ã˜Â¦Ã™â€ž Ã™Ë†Ø£Ø­Ø¯Ø§Ø« Ã¢â€â‚¬Ã¢â€â‚¬
        { term: "Ã˜Â¨Ã™â€ Ã™Ë† Ã™â€šÃ˜Â±Ã™Å Ø¸Ø©",               pattern: "Ã˜Â¨Ã™â€ Ã™Ë† Ã™â€šÃ˜Â±Ã™Å Ø¸[Ã˜Â©Ã™â€¡]|Ã˜Â¨Ã™â€ Ã™Å  Ã™â€šÃ˜Â±Ã™Å Ø¸[Ã˜Â©Ã™â€¡]" },
        { term: "Ã˜Â¨Ã™â€ Ã™Ë† Ã™â€šÃ™Å Ã™â€ Ã™â€šØ§Ø¹",              pattern: "Ã˜Â¨Ã™â€ Ã™Ë† Ã™â€šÃ™Å Ã™â€ Ã™â€šØ§Ø¹|Ã˜Â¨Ã™â€ Ã™Å  Ã™â€šÃ™Å Ã™â€ Ã™â€šØ§Ø¹" },
        { term: "Ã˜Â¨Ã™â€ Ã™Ë† Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¶Ã™Å Ø±",              pattern: "Ã˜Â¨Ã™â€ Ã™Ë† Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¶Ã™Å Ø±|Ã˜Â¨Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¶Ã™Å Ø±" },
        { term: "Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â§Ã™â€žØ£Ø­Ø²Ø§Ø¨",            pattern: "Ã˜ÂºÃ˜Â²Ã™Ë†[Ã˜Â©Ã™â€¡] Ã˜Â§Ã™â€žØ£Ø­Ø²Ø§Ø¨|Ã˜Â§Ã™â€žØ£Ø­Ø²Ø§Ø¨" },
        { term: "Ø¨Ø¯Ø± Ã˜Â§Ã™â€žÃ™â€¦Ã™Ë†Ø¹Ø¯",              pattern: "Ø¨Ø¯Ø± Ã˜Â§Ã™â€žÃ™â€¦Ã™Ë†Ø¹Ø¯" },
        { term: "Ø°Ø§Øª Ã˜Â§Ã™â€žÃ˜Â±Ã™â€šØ§Ø¹",              pattern: "Ø°Ø§Øª Ã˜Â§Ã™â€žÃ˜Â±Ã™â€šØ§Ø¹" },
        { term: "Ã˜Â¯Ã™Ë†Ã™â€¦Ø© Ã˜Â§Ã™â€žÃ˜Â¬Ã™â€ Ã˜Â¯Ã™â€ž",             pattern: "Ã˜Â¯Ã™Ë†Ã™â€¦[Ã˜Â©Ã™â€¡] Ã˜Â§Ã™â€žÃ˜Â¬Ã™â€ Ã˜Â¯Ã™â€ž" },
        { term: "Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â¨Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ™â€¦Ã˜ÂµÃ˜Â·Ã™â€žÃ™â€š",        pattern: "Ã˜ÂºÃ˜Â²Ã™Ë†[Ã˜Â©Ã™â€¡] Ã˜Â¨Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ™â€¦Ã˜ÂµÃ˜Â·Ã™â€žÃ™â€š|Ã˜Â¨Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ™â€¦Ã˜ÂµÃ˜Â·Ã™â€žÃ™â€š|Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â±Ã™Å Ã˜Â³Ã™Å Ø¹" }
    ];
    
    GLOSSARY_MATCHERS.forEach((item, idx) => {
        let isFemale = idx < 13;
        let cssClass = isFemale ? 'glossary-female' : 'glossary-male';
        // Removed lookbehind for iOS/Safari compatibility. Captured the preceding char in $1, the pattern in $2.
        try {
            const regex = new RegExp(`(^|[^Ø£-ÙŠ])(${item.pattern})(?=$|[^Ø£-ÙŠ])(?![^<>]*>)`, 'g');
            result = result.replace(regex, `$1<span class="glossary-badge ${cssClass}" onclick="showGlossaryPopup(event, '${item.term}')">$2</span>`);
        } catch (e) {
            console.error("Regex error on term", item.term, e);
        }
    });
    return result;
}

// Ã¢â€â‚¬Ã¢â€â‚¬ GLOSSARY & MINDMAP POPUPS Ã¢â€â‚¬Ã¢â€â‚¬
const GLOSSARY = {
    // Ã˜Â±Ã˜Â¬Ã˜Â§Ã™â€ž Ã˜Â§Ã™â€žØµØ­Ø§Ø¨Ø© Ã™Ë†Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¹Ã˜Â§Ã˜ÂµÃ˜Â±Ã™Ë†Ã™â€ 
    "Ã˜Â²Ã™Å Ø¯ Ã˜Â¨Ã™â€  Ø­Ø§Ø±Ø«Ø©": { def: "Ã˜ÂµÃ˜Â­Ã˜Â§Ã˜Â¨Ã™Å  Ã˜Â¬Ã™â€žÃ™Å Ã™â€žÃ˜Å’ Ã™Æ’Ã˜Â§Ã™â€  Ã™Å Ã˜Â¯Ã˜Â¹Ã™â€° Ã˜Â²Ã™Å Ø¯ Ã˜Â¨Ã™â€  Ã™â€¦Ã˜Â­Ã™â€¦Ø¯ Ã˜Â¨Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â¨Ã™â€ Ã™Å  Ã™â€šÃ˜Â¨Ã™â€ž Ã˜ÂªÃ˜Â­Ã˜Â±Ã™Å Ã™â€¦Ã™â€¡Ã˜Å’ Ã™Ë†Ã™â€¡Ã™Ë† Ã˜Â§Ã™â€žÃ˜ÂµÃ˜Â­Ã˜Â§Ã˜Â¨Ã™Å  Ã˜Â§Ã™â€žÃ™Ë†Ã˜Â­Ã™Å Ø¯ Ã˜Â§Ã™â€žÃ˜Â°Ã™Å  Ã˜Â°Ã™ÂÃ™Æ’Ø± Ã˜Â§Ã˜Â³Ã™â€¦Ã™â€¡ ØµØ±Ø§Ø­Ø© Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ™â€šÃ˜Â±Ã˜Â¢Ã™â€  Ã˜Â§Ã™â€žÃ™Æ’Ã˜Â±Ã™Å Ã™â€¦.", type: "person", gender: "male" },
    "Ã˜Â£Ã˜Â¨Ã™Ë† Ã˜Â³Ã™ÂÃ™Å Ã˜Â§Ã™â€ ": { def: "Ã˜Â²Ã˜Â¹Ã™Å Ã™â€¦ Ã™â€¦Ã˜Â´Ã˜Â±Ã™Æ’Ã™Å  Ã™â€šÃ˜Â±Ã™Å Ø´ Ã™Ë†Ã™â€šØ§Ø¦Ø¯ Ã™â€šÃ™Ë†Ã˜Â§Ã™ÂÃ™â€žÃ™â€¡Ã™â€¦ Ã™Ë†Ã˜Â¬Ã™Å Ã™Ë†Ã˜Â´Ã™â€¡Ã™â€¦ Ã™ÂÃ™Å  Ã˜ÂºÃ˜Â²Ã™Ë† Ø£Ø­Ø¯ Ã™Ë†Ã˜Â§Ã™â€žØ£Ø­Ø²Ø§Ø¨ Ã™â€šÃ˜Â¨Ã™â€ž Ã˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦Ã™â€¡ Ã™Å Ã™Ë†Ã™â€¦ Ã™ÂØªØ­ Ã™â€¦Ã™Æ’Ø©.", type: "person", gender: "male" },
    "Ã˜Â³Ã™â€žÃ™â€¦Ã˜Â§Ã™â€  Ã˜Â§Ã™â€žÃ™ÂÃ˜Â§Ã˜Â±Ã˜Â³Ã™Å ": { def: "Ã˜ÂµÃ˜Â­Ã˜Â§Ã˜Â¨Ã™Å  Ã˜Â¬Ã™â€žÃ™Å Ã™â€ž Ã™â€¦Ã™â€  Ã˜Â¨Ã™â€žØ§Ø¯ Ã™ÂÃ˜Â§Ã˜Â±Ã˜Â³Ã˜Å’ Ã™Ë†Ã™â€¡Ã™Ë† ØµØ§Ø­Ø¨ Ã™ÂÃ™Æ’Ø±Ø© Ã˜Â­Ã™ÂØ± Ã˜Â§Ã™â€žÃ˜Â®Ã™â€ Ã˜Â¯Ã™â€š Ã™â€žÃ˜Â­Ã™â€¦Ã˜Â§Ã™Å Ø© Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ø© Ã™ÂÃ™Å  Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â§Ã™â€žØ£Ø­Ø²Ø§Ø¨.", type: "person", gender: "male" },
    "Ø³Ø¹Ø¯ Ã˜Â¨Ã™â€  Ã™â€¦Ø¹Ø§Ø°": { def: "Ã˜Â³Ã™Å Ø¯ Ã˜Â§Ã™â€žÃ˜Â£Ã™Ë†Ø³ Ã™Ë†Ã˜ÂµÃ˜Â­Ã˜Â§Ã˜Â¨Ã™Å  Ã˜Â¬Ã™â€žÃ™Å Ã™â€ž Ã˜Â§Ã™â€¡ØªØ² Ã™â€žÃ™Ë†Ã™ÂÃ˜Â§Ã˜ÂªÃ™â€¡ Ø¹Ø±Ø´ Ã˜Â§Ã™â€žÃ˜Â±Ã˜Â­Ã™â€¦Ã™â€ Ã˜Å’ Ã™Ë†Ã™â€¡Ã™Ë† Ã˜Â§Ã™â€žÃ˜Â°Ã™Å  Ã˜Â­Ã™Æ’Ã™â€¦ Ã™ÂÃ™Å  Ã˜Â¨Ã™â€ Ã™Å  Ã™â€šÃ˜Â±Ã™Å Ø¸Ø© Ã˜Â¨Ã˜Â­Ã™Æ’Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã™Ë†Ã˜Â±Ã˜Â³Ã™Ë†Ã™â€žÃ™â€¡.", type: "person", gender: "male" },
    "Ã˜Â­Ã™Å Ã™Å  Ã˜Â¨Ã™â€  Ø£Ø®Ø·Ø¨": { def: "Ã˜Â²Ã˜Â¹Ã™Å Ã™â€¦ Ã˜Â¨Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¶Ã™Å Ø± Ã™Ë†Ø£Ø­Ø¯ Ã˜Â£Ã™â€žØ¯ Ø£Ø¹Ø¯Ø§Ø¡ Ã˜Â§Ã™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦Ã˜Å’ Ã˜Â­Ã˜Â±Ã™â€˜Ø¶ Ã˜Â§Ã™â€žØ£Ø­Ø²Ø§Ø¨ Ø¶Ø¯ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ø© Ã™Ë†ØºØ¯Ø± Ã˜Â¨Ã˜Â§Ã™â€žÃ˜Â¹Ã™â€¡Ø¯ Ã˜Â«Ã™â€¦ Ã™â€šÃ™ÂÃ˜ÂªÃ™â€ž Ã™â€¦Ø¹ Ã˜Â¨Ã™â€ Ã™Å  Ã™â€šÃ˜Â±Ã™Å Ø¸Ø©.", type: "person", gender: "male" },
    "Ã™â€ Ã˜Â¹Ã™Å Ã™â€¦ Ã˜Â¨Ã™â€  Ã™â€¦Ã˜Â³Ã˜Â¹Ã™Ë†Ø¯": { def: "Ã˜ÂµÃ˜Â­Ã˜Â§Ã˜Â¨Ã™Å  Ã˜Â¬Ã™â€žÃ™Å Ã™â€ž Ã˜Â£Ã˜Â³Ã™â€žÃ™â€¦ Ã˜Â³Ã˜Â±Ã™â€˜Ã˜Â§Ã™â€¹ Ã™Å Ã™Ë†Ã™â€¦ Ã˜Â§Ã™â€žØ£Ø­Ø²Ø§Ø¨ Ã™Ë†Ã™â€ Ø¬Ø­ Ã˜Â¨Ã˜Â¯Ã™â€¡Ã˜Â§Ã˜Â¦Ã™â€¡ Ã™ÂÃ™Å  Ã˜Â®Ã˜Â°Ã™â€ž Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã˜Â±Ã™Æ’Ã™Å Ã™â€  Ã™Ë†Ã˜Â¥Ã™Å Ã™â€šØ§Ø¹ Ã˜Â§Ã™â€žÃ˜Â®Ã™â€žÃ˜Â§Ã™Â Ã˜Â¨Ã™Å Ã™â€  Ã™â€šÃ˜Â±Ã™Å Ø´ Ã™Ë†Ã˜Â¨Ã™â€ Ã™Å  Ã™â€šÃ˜Â±Ã™Å Ø¸Ø©.", type: "person", gender: "male" },
    "Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€  Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â¨Ã™â€  Ã˜Â³Ã™â€žÃ™Ë†Ã™â€ž": { def: "Ø±Ø£Ø³ Ã˜Â§Ã™â€žÃ™â€ Ã™ÂÃ˜Â§Ã™â€š Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ã˜Â©Ã˜Å’ Ã˜Â§Ã˜Â³Ã˜ÂªÃ˜ÂºÃ™â€ž Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â¨Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ™â€¦Ã˜ÂµÃ˜Â·Ã™â€žÃ™â€š Ã™â€žØ¥Ø«Ø§Ø±Ø© Ã˜Â§Ã™â€žÃ™ÂÃ˜ÂªÃ™â€  Ã™Ë†Ã˜ÂªÃ™Ë†Ã™â€žÃ™â€° Ã™Æ’Ã™ÂØ¨Ø± Ø­Ø§Ø¯Ø«Ø© Ã˜Â§Ã™â€žÃ˜Â¥Ã™ÂÃ™Æ’ Ã˜Â·Ã˜Â¹Ã™â€ Ã˜Â§Ã™â€¹ Ã™ÂÃ™Å  Ã˜Â£Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¤Ã™â€¦Ã™â€ Ã™Å Ã™â€  Ø¹Ø§Ø¦Ø´Ø©.", type: "person", gender: "male" },
    "Ã˜ÂµÃ™ÂÃ™Ë†Ã˜Â§Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¹Ã˜Â·Ã™â€ž": { def: "Ã˜ÂµÃ˜Â­Ã˜Â§Ã˜Â¨Ã™Å  Ã˜Â¬Ã™â€žÃ™Å Ã™â€ž Ã™â€¦Ã™â€  Ã˜Â®Ã™Å Ø±Ø© Ã˜Â§Ã™â€žÃ˜ÂµÃ˜Â­Ã˜Â§Ã˜Â¨Ã˜Â©Ã˜Å’ Ã˜Â§Ã˜ÂªÃ™â€¡Ã™â€¦Ã™â€¡ Ã˜Â§Ã™â€žÃ™â€¦Ã™â€ Ã˜Â§Ã™ÂÃ™â€šÃ™Ë†Ã™â€  Ã˜Â¸Ã™â€žÃ™â€¦Ã˜Â§Ã™â€¹ Ã™Ë†Ã˜Â²Ã™Ë†Ã˜Â±Ã˜Â§Ã™â€¹ Ã™ÂÃ™Å  Ø­Ø§Ø¯Ø«Ø© Ã˜Â§Ã™â€žÃ˜Â¥Ã™ÂÃ™Æ’ Ã™Ë†Ã˜Â¨Ã˜Â±Ã˜Â£Ã™â€¡ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ø¹Ø² Ã™Ë†Ã˜Â¬Ã™â€ž Ã˜Â¨Ã˜Â¢Ã™Å Ø§Øª Ã˜Â³Ã™Ë†Ø±Ø© Ã˜Â§Ã™â€žÃ™â€ Ã™Ë†Ø±.", type: "person", gender: "male" },
    "Ã˜Â£Ã™â€¦Ã™Å Ø© Ã˜Â¨Ã™â€  Ã˜Â®Ã™â€žÃ™Â": { def: "Ø£Ø­Ø¯ Ã˜Â£Ã˜Â¦Ã™â€¦Ø© Ã˜Â§Ã™â€žÃ™Æ’Ã™ÂØ± Ã˜Â¨Ã™â€¦Ã™Æ’Ã˜Â©Ã˜Å’ Ã™Æ’Ã˜Â§Ã™â€  Ã™Å Ø¹Ø°Ø¨ Ã˜Â¨Ã™â€žÃ˜Â§Ã™â€ž Ã˜Â¨Ã™â€  Ã˜Â±Ã˜Â¨Ã˜Â§Ã˜Â­Ã˜Å’ Ã™Ë†Ã™â€šÃ™ÂÃ˜ÂªÃ™â€ž Ã™ÂÃ™Å  Ã™â€¦Ã˜Â¹Ã˜Â±Ã™Æ’Ø© Ø¨Ø¯Ø± Ã˜Â§Ã™â€žÃ™Æ’Ã˜Â¨Ã˜Â±Ã™â€° Ã˜Â¹Ã™â€žÃ™â€° Ã™Å Ø¯ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™â€¦Ã™Å Ã™â€ .", type: "person", gender: "male" },
    "Ã˜Â­Ã™â€¦Ø²Ø© Ã˜Â¨Ã™â€  Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â·Ã™â€žØ¨": { def: "Ø£Ø³Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã™Ë†Ã˜Â±Ã˜Â³Ã™Ë†Ã™â€žÃ™â€¡ Ã™Ë†Ã˜Â¹Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·ÂºÃ˜Å’ Ã˜Â§Ã˜Â³Ã˜ÂªÃ˜Â´Ã™â€¡Ø¯ Ã™ÂÃ™Å  Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ø£Ø­Ø¯ Ã˜Â¹Ã™â€žÃ™â€° Ã™Å Ø¯ Ã™Ë†Ã˜Â­Ã˜Â´Ã™Å  Ã™Ë†Ã™â€¦Ã˜Â«Ã™â€ž Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã˜Â±Ã™Æ’Ã™Ë†Ã™â€  Ã˜Â¨Ã˜Â¬Ã˜Â³Ã˜Â¯Ã™â€¡ Ã˜Â§Ã™â€žÃ˜Â´Ã˜Â±Ã™Å Ã™Â.", type: "person", gender: "male" },
    "Ã™â€¦ØµØ¹Ø¨ Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€¦Ã™Å Ø±": { def: "Ã˜Â£Ã™Ë†Ã™â€ž Ã˜Â³Ã™ÂÃ™Å Ø± Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦Ã˜Å’ Ã˜Â­Ã™â€¦Ã™â€ž Ã˜Â±Ã˜Â§Ã™Å Ø© Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™â€¦Ã™Å Ã™â€  Ã™ÂÃ™Å  Ã˜ÂºÃ˜Â²Ã™Ë† Ã˜Â£Ã™ÂØ­Ø¯ Ã™Ë†Ã˜Â§Ã˜Â³Ã˜ÂªÃ˜Â´Ã™â€¡Ø¯ Ã™â€¦Ã™â€šÃ˜Â¨Ã™â€žÃ˜Â§Ã™â€¹ Ã˜ÂºÃ™Å Ø± Ã™â€¦Ø¯Ø¨Ø± Ã˜Â±Ã˜Â¶Ã™Å  Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¹Ã™â€ Ã™â€¡.", type: "person", gender: "male" },
    "Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€  Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦": { def: "Ø­Ø¨Ø± Ã™â€¦Ã™â€  Ø£Ø­Ø¨Ø§Ø± Ã™Å Ã™â€¡Ã™Ë†Ø¯ Ã˜Â¨Ã™â€ Ã™Å  Ã™â€šÃ™Å Ã™â€ Ã™â€šØ§Ø¹ Ã˜Â¨Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ã˜Â©Ã˜Å’ Ã˜Â£Ã˜Â³Ã™â€žÃ™â€¦ Ã™â€¦Ø¹ Ã˜Â¨Ã˜Â¯Ã˜Â§Ã™Å Ø© Ã™â€¡Ø¬Ø±Ø© Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Ë†Ã˜Â´Ã™â€¡Ø¯ Ã˜Â¨Ã˜ÂµÃ˜Â¯Ã™â€š Ã™â€ Ã˜Â¨Ã™Ë†Ã˜ÂªÃ™â€¡ Ã™Ë†Ã™â€¡Ã™Ë† Ã™â€¦Ã™â€  Ã™Æ’Ø¨Ø§Ø± Ã˜Â§Ã™â€žØµØ­Ø§Ø¨Ø©.", type: "person", gender: "male" },
    "Ã˜Â£Ã˜Â¨Ã™Ë† Ã˜Â¨Ã™Æ’Ø± Ã˜Â§Ã™â€žÃ˜ÂµÃ˜Â¯Ã™Å Ã™â€š": { def: "Ã˜Â£Ã™Ë†Ã™â€ž Ã˜Â§Ã™â€žÃ˜Â®Ã™â€žÃ™ÂØ§Ø¡ Ã˜Â§Ã™â€žÃ˜Â±Ã˜Â§Ã˜Â´Ã˜Â¯Ã™Å Ã™â€  Ã™Ë†Ã˜Â£Ã™â€šØ±Ø¨ Ã˜Â§Ã™â€žØµØ­Ø§Ø¨Ø© Ã˜Â¥Ã™â€žÃ™â€° Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·ÂºÃ˜Å’ Ã˜Â±Ã™ÂÃ™Å Ã™â€šÃ™â€¡ Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ™â€¡Ø¬Ø±Ø© Ã™Ë†ØµØ§Ø­Ø¨ Ã˜Â§Ã™â€žÃ˜ÂºÃ˜Â§Ã˜Â±Ã˜Å’ Ã™Ë†Ã˜Â£Ã™Ë†Ã™â€ž Ã™â€¦Ã™â€  Ã˜ÂµÃ˜Â¯Ã™â€˜Ã™â€š Ã˜Â¨Ã˜Â§Ã™â€žØ¥Ø³Ø±Ø§Ø¡ Ã™Ë†Ã˜Â§Ã™â€žÃ™â€¦Ø¹Ø±Ø§Ø¬.", type: "person", gender: "male" },
    "Ã˜Â¹Ã™â€¦Ø± Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žØ®Ø·Ø§Ø¨": { def: "Ã˜Â«Ã˜Â§Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ˜Â®Ã™â€žÃ™ÂØ§Ø¡ Ã˜Â§Ã™â€žÃ˜Â±Ã˜Â§Ã˜Â´Ã˜Â¯Ã™Å Ã™â€ Ã˜Å’ Ã˜Â§Ã™â€žÃ™ÂÃ˜Â§Ã˜Â±Ã™Ë†Ã™â€š Ã˜Â§Ã™â€žÃ˜Â°Ã™Å  Ø£Ø¹Ø² Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€¡ Ã˜Â§Ã™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦Ã˜Å’ Ã˜Â¹Ã™ÂÃ˜Â±Ã™Â Ã˜Â¨Ã˜Â´Ã˜Â¯Ã˜ÂªÃ™â€¡ Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â­Ã™â€š Ã™Ë†Ã˜Â¹Ã˜Â¯Ã™â€žÃ™â€¡ Ã˜Â§Ã™â€žÃ˜Â°Ã™Å  Ø¶Ø±Ø¨ Ã˜Â¨Ã™â€¡ Ã˜Â§Ã™â€žÃ˜Â£Ã™â€¦Ã˜Â«Ã˜Â§Ã™â€ž Ã™ÂÃ™Å  Ã™Æ’Ã™â€ž Ã™â€¦Ã™Æ’Ã˜Â§Ã™â€ .", type: "person", gender: "male" },
    "Ã˜Â¹Ã˜Â«Ã™â€¦Ã˜Â§Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™ÂÃ˜Â§Ã™â€ ": { def: "Ã˜Â«Ã˜Â§Ã™â€žØ« Ã˜Â§Ã™â€žÃ˜Â®Ã™â€žÃ™ÂØ§Ø¡ Ã˜Â§Ã™â€žÃ˜Â±Ã˜Â§Ã˜Â´Ã˜Â¯Ã™Å Ã™â€  Ã™Ë†Ã˜Â°Ã™Ë† Ã˜Â§Ã™â€žÃ™â€ Ã™Ë†Ã˜Â±Ã™Å Ã™â€ Ã˜Å’ Ã˜Â²Ã™Ë†Ø¬ Ã˜Â±Ã™â€šÃ™Å Ø© Ã˜Â«Ã™â€¦ Ã˜Â£Ã™â€¦ Ã™Æ’Ã™â€žÃ˜Â«Ã™Ë†Ã™â€¦ Ã˜Â¨Ã™â€ Ã˜ÂªÃ™Å½Ã™Å  Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·ÂºÃ˜Å’ Ã˜Â¬Ã™â€¡Ã™â€˜Ø² Ã˜Â¬Ã™Å Ø´ Ã˜Â§Ã™â€žØ¹Ø³Ø±Ø© Ã™â€¦Ã™â€  Ã™â€¦Ã˜Â§Ã™â€žÃ™â€¡ Ã™Ë†Ã˜Â¬Ã™â€¦Ø¹ Ã˜Â§Ã™â€žÃ™â€šÃ˜Â±Ã˜Â¢Ã™â€ .", type: "person", gender: "male" },
    "Ã˜Â¹Ã™â€žÃ™Å  Ã˜Â¨Ã™â€  Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â·Ã˜Â§Ã™â€žØ¨": { def: "Ø±Ø§Ø¨Ø¹ Ã˜Â§Ã™â€žÃ˜Â®Ã™â€žÃ™ÂØ§Ø¡ Ã˜Â§Ã™â€žÃ˜Â±Ã˜Â§Ã˜Â´Ã˜Â¯Ã™Å Ã™â€  Ã™Ë†Ã˜Â§Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Ë†Ã˜Â²Ã™Ë†Ø¬ Ã™ÂÃ˜Â§Ã˜Â·Ã™â€¦Ø© Ã˜Â§Ã™â€žÃ˜Â²Ã™â€¡Ã˜Â±Ã˜Â§Ã˜Â¡Ã˜Å’ Ã˜Â£Ã˜Â³Ã™â€žÃ™â€¦ Ã™Ë†Ã™â€¡Ã™Ë† Ã˜ÂµÃ˜ÂºÃ™Å Ø± Ã™Ë†Ã™Æ’Ã˜Â§Ã™â€  Ã™â€¦Ã™â€  Ø£Ø´Ø¬Ø¹ Ã™ÂÃ˜Â±Ã˜Â³Ã˜Â§Ã™â€  Ã˜Â§Ã™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦.", type: "person", gender: "male" },
    "Ã˜Â®Ã˜Â§Ã™â€žØ¯ Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ™Ë†Ã™â€žÃ™Å Ø¯": { def: "Ã˜Â³Ã™Å Ã™Â Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™Ë†Ã™â€žÃ˜Å’ Ã˜Â£Ã˜Â³Ã™â€žÃ™â€¦ Ã™â€šÃ™ÂÃ˜Â¨Ã™Å Ã™â€ž Ã™ÂØªØ­ Ã™â€¦Ã™Æ’Ø© Ã™Ë†Ã™â€šØ§Ø¯ Ã™â€¦Ã˜Â¹Ã˜Â§Ã˜Â±Ã™Æ’ Ã˜Â­Ã˜Â§Ã˜Â³Ã™â€¦Ø© Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ™Å Ã™â€¦Ã˜Â§Ã™â€¦Ø© Ã™Ë†Ã˜Â§Ã™â€žÃ˜Â´Ã˜Â§Ã™â€¦ Ã™Ë†Ã˜Â§Ã™â€žÃ˜Â¹Ã˜Â±Ã˜Â§Ã™â€š Ã™Ë†Ã™â€žÃ™â€¦ Ã™Å Ã™ÂÃ™â€¡Ã˜Â²Ã™â€¦ Ã™ÂÃ™Å  Ø­Ø±Ø¨ Ã™â€šØ·.", type: "person", gender: "male" },
    "Ã˜Â¨Ã™â€žÃ˜Â§Ã™â€ž Ã˜Â¨Ã™â€  Ø±Ø¨Ø§Ø­": { def: "Ã˜Â£Ã™Ë†Ã™â€ž Ã™â€¦Ã˜Â¤Ã˜Â°Ã™â€  Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦Ã˜Å’ Ø¹Ø¨Ø¯ Ã˜Â­Ã˜Â¨Ã˜Â´Ã™Å  Ã™Æ’Ã˜Â§Ã™â€  Ã™Å Ã˜Â¹Ã˜Â°Ã˜Â¨Ã™â€¡ Ã˜Â£Ã™â€¦Ã™Å Ø© Ã˜Â¨Ã™â€  Ã˜Â®Ã™â€žÃ™Â Ã˜Â¨Ã˜Â§Ã™â€žÃ˜Â±Ã™â€¦Ø¶Ø§Ø¡ Ã™â€žÃ™Å Ã˜ÂªÃ˜Â±Ã™Æ’ Ã˜Â¯Ã™Å Ã™â€ Ã™â€¡Ã˜Å’ Ã˜Â­Ã˜ÂªÃ™â€° Ã˜Â§Ã˜Â´Ã˜ÂªÃ˜Â±Ã˜Â§Ã™â€¡ Ã˜Â£Ã˜Â¨Ã™Ë† Ã˜Â¨Ã™Æ’Ø± Ã™Ë†Ã˜Â£Ã˜Â¹Ã˜ÂªÃ™â€šÃ™â€¡.", type: "person", gender: "male" },
    "Ã˜Â£Ã˜Â¨Ã™Ë† Ã™â€¡Ã˜Â±Ã™Å Ø±Ø©": { def: "Ã˜Â£Ã™Æ’Ø«Ø± Ã˜Â§Ã™â€žØµØ­Ø§Ø¨Ø© Ã˜Â±Ã™Ë†Ã˜Â§Ã™Å Ø© Ã™â€žÃ™â€žÃ˜Â­Ã˜Â¯Ã™Å Ø« Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Ë†Ã™Å Ã˜Å’ Ã˜Â£Ã˜Â³Ã™â€žÃ™â€¦ Ã˜Â¹Ã˜Â§Ã™â€¦ Ã˜Â®Ã™Å Ø¨Ø± Ã™Ë†Ã˜Â¸Ã™â€ž Ã™â€¦Ã™â€žÃ˜Â§Ã˜Â²Ã™â€¦Ã˜Â§Ã™â€¹ Ã™â€žÃ™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã˜Â­Ã˜ÂªÃ™â€° Ã™Ë†Ã™ÂÃ˜Â§Ã˜ÂªÃ™â€¡ Ã™Ë†Ã˜Â±Ã™Ë†Ã™â€° Ã˜Â£Ã™Æ’Ø«Ø± Ã™â€¦Ã™â€  Ã˜Â®Ã™â€¦Ø³Ø© Ã˜Â¢Ã™â€žÃ˜Â§Ã™Â Ã˜Â­Ã˜Â¯Ã™Å Ø«.", type: "person", gender: "male" },
    "Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã™â€  Ã™â€¦Ã˜Â³Ã˜Â¹Ã™Ë†Ø¯": { def: "Ã˜ÂµÃ˜Â­Ã˜Â§Ã˜Â¨Ã™Å  Ã™â€¦Ã™â€  Ã˜Â£Ã™Ë†Ã˜Â§Ã˜Â¦Ã™â€ž Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™â€¦Ã™Å Ã™â€ Ã˜Å’ Ã˜Â®Ã˜Â§Ã˜Â¯Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Ë†Ã˜Â£Ã˜Â¹Ã™â€žÃ™â€¦ Ã˜Â§Ã™â€žØµØ­Ø§Ø¨Ø© Ã˜Â¨Ã˜Â§Ã™â€žÃ™â€šÃ˜Â±Ã˜Â¢Ã™â€  Ã˜Â§Ã™â€žÃ™Æ’Ã˜Â±Ã™Å Ã™â€¦ Ã™Ë†Ã˜Â§Ã™â€žÃ˜ÂªÃ™ÂÃ˜Â³Ã™Å Ã˜Â±Ã˜Å’ Ã™â€šÃ˜Â§Ã™â€ž Ã˜Â¹Ã™â€ Ã™â€¡ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº: Ã™â€¦Ã™â€  Ã˜Â³Ã˜Â±Ã™â€¡ Ã˜Â£Ã™â€  Ã™Å Ã™â€šØ±Ø£ Ã˜Â§Ã™â€žÃ™â€šÃ˜Â±Ã˜Â¢Ã™â€  Ã˜ÂºÃ˜Â¶Ã˜Â§Ã™â€¹ Ã™ÂÃ™â€žÃ™Å Ã™â€šØ±Ø£ Ã˜Â¹Ã™â€žÃ™â€° Ã™â€šØ±Ø§Ø¡Ø© Ã˜Â§Ã˜Â¨Ã™â€  Ã˜Â£Ã™â€¦ Ø¹Ø¨Ø¯.", type: "person", gender: "male" },
    "Ã™Ë†Ã˜Â­Ã˜Â´Ã™Å  Ã˜Â¨Ã™â€  Ø­Ø±Ø¨": { def: "Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â¨Ã˜Â´Ã™Å  Ã˜Â§Ã™â€žÃ˜Â°Ã™Å  Ã™â€šÃ˜ÂªÃ™â€ž Ã˜Â­Ã™â€¦Ø²Ø© Ã˜Â¨Ã™â€  Ø¹Ø¨Ø¯ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â·Ã™â€žØ¨ Ã˜Â¨Ã˜Â£Ã™â€¦Ø± Ã™â€¡Ã™â€ Ø¯ Ã™Å Ã™Ë†Ã™â€¦ Ã˜Â£Ã˜Â­Ã˜Â¯Ã˜Å’ Ã˜Â«Ã™â€¦ Ã˜Â£Ã˜Â³Ã™â€žÃ™â€¦ Ø¨Ø¹Ø¯ Ã™ÂØªØ­ Ã™â€¦Ã™Æ’Ø© Ã™Ë†Ã™â€šÃ˜ÂªÃ™â€ž Ã™â€¦Ã˜Â³Ã™Å Ã™â€žÃ™â€¦Ø© Ã˜Â§Ã™â€žÃ™Æ’Ø°Ø§Ø¨ Ã™ÂÃ™Å  Ã˜Â­Ã˜Â±Ã™Ë†Ø¨ Ã˜Â§Ã™â€žØ±Ø¯Ø©.", type: "person", gender: "male" },
    "Ã˜Â¹Ã™â€¦Ã˜Â±Ã™Ë† Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žØ¹Ø§Øµ": { def: "Ã˜ÂµÃ˜Â­Ã˜Â§Ã˜Â¨Ã™Å  Ã™Ë†Ã™â€šØ§Ø¦Ø¯ Ã˜Â¹Ã˜Â³Ã™Æ’Ã˜Â±Ã™Å  Ã˜Â¨Ã˜Â§Ã˜Â±Ã˜Â¹Ã˜Å’ Ã˜Â£Ã˜Â³Ã™â€žÃ™â€¦ Ã™â€šÃ™ÂÃ˜Â¨Ã™Å Ã™â€ž Ã™ÂØªØ­ Ã™â€¦Ã™Æ’Ø© Ã™Ë†Ã™ÂØªØ­ Ã™â€¦ØµØ± Ã™ÂÃ™Å  Ã˜Â¹Ã™â€¡Ø¯ Ã˜Â¹Ã™â€¦Ø± Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žØ®Ø·Ø§Ø¨ Ã˜Â±Ã˜Â¶Ã™Å  Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¹Ã™â€ Ã™â€¡.", type: "person", gender: "male" },
    "Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€žÙŠ": { def: "Ø³Ø¨Ø· Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Ë†Ã˜Â±Ã™Å Ã˜Â­Ã˜Â§Ã™â€ Ã˜ÂªÃ™â€¡Ã˜Å’ Ã˜Â§Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€žÃ™Å  Ã™Ë†Ã™ÂÃ˜Â§Ã˜Â·Ã™â€¦Ã˜Â©Ã˜Å’ Ã™â€šÃ˜Â§Ã™â€ž Ã™ÂÃ™Å Ã™â€¡ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å : Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™â€  Ã™Ë†Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™Å Ã™â€  Ã˜Â³Ã™Å Ø¯Ø§ Ø´Ø¨Ø§Ø¨ Ã˜Â£Ã™â€¡Ã™â€ž Ã˜Â§Ã™â€žÃ˜Â¬Ã™â€ Ø©.", type: "person", gender: "male" },
    "Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™Å Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€žÙŠ": { def: "Ø³Ø¨Ø· Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Ë†Ã˜Â±Ã™Å Ã˜Â­Ã˜Â§Ã™â€ Ã˜ÂªÃ™â€¡Ã˜Å’ Ã˜Â£Ã™ÂÃ™Ë†Ã™â€žØ¯ Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â³Ã™â€ Ø© Ã˜Â§Ã™â€žØ±Ø§Ø¨Ø¹Ø© Ã™â€žÃ™â€žÃ™â€¡Ã˜Â¬Ã˜Â±Ã˜Â©Ã˜Å’ Ã™Ë†Ã™â€šÃ˜Â§Ã™â€ž Ã™ÂÃ™Å Ã™â€¡ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å : Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™Å Ã™â€  Ã™â€¦Ã™â€ Ã™Å  Ã™Ë†Ã˜Â£Ã™â€ Ø§ Ã™â€¦Ã™â€  Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â³Ã™Å Ã™â€ .", type: "person", gender: "male" },
    "Ã˜Â§Ã™â€žÃ™â€ Ø¬Ø§Ø´ÙŠ": { def: "Ã™â€¦Ã™â€žÃ™Æ’ Ã˜Â§Ã™â€žØ­Ø¨Ø´Ø© Ã˜Â§Ã™â€žÃ˜Â°Ã™Å  Ø£Ø¬Ø§Ø± Ã˜Â§Ã™â€žÃ™â€¦Ã™â€¡Ã˜Â§Ã˜Â¬Ã˜Â±Ã™Å Ã™â€  Ã˜Â§Ã™â€žÃ˜Â£Ã™Ë†Ã™â€žÃ™Å Ã™â€  Ã™Ë†Ã˜Â£Ã™â€ Ã˜ÂµÃ™ÂÃ™â€¡Ã™â€¦Ã˜Å’ Ã˜Â£Ã˜Â³Ã™â€žÃ™â€¦ Ã™ÂÃ™Å  Ã™â€šÃ™â€žÃ˜Â¨Ã™â€¡ Ã™Ë†Ã˜ÂµÃ™â€žÃ™â€° Ã˜Â¹Ã™â€žÃ™Å Ã™â€¡ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã˜ÂµÃ™â€žØ§Ø© Ã˜Â§Ã™â€žØºØ§Ø¦Ø¨ Ã™â€žÃ™â€¦Ø§ Ã™â€¦Ø§Øª.", type: "person", gender: "male" },
    "Ã˜Â£Ã˜Â¨Ã™Ë† Ã˜Â¬Ã™â€¡Ã™â€ž": { def: "Ã™ÂÃ˜Â±Ã˜Â¹Ã™Ë†Ã™â€  Ã™â€¡Ã˜Â°Ã™â€¡ Ã˜Â§Ã™â€žÃ˜Â£Ã™â€¦Ø© Ã™Ë†Ã˜Â§Ã˜Â³Ã™â€¦Ã™â€¡ Ã˜Â¹Ã™â€¦Ã˜Â±Ã™Ë† Ã˜Â¨Ã™â€  Ã™â€¡Ã˜Â´Ã˜Â§Ã™â€¦Ã˜Å’ Ã™â€¦Ã™â€  Ø£Ø´Ø¯ Ø£Ø¹Ø¯Ø§Ø¡ Ã˜Â§Ã™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦ Ã™Ë†Ã˜Â£Ã™Æ’Ã˜Â«Ã˜Â±Ã™â€¡Ã™â€¦ Ã˜Â¥Ã™Å Ã˜Â°Ã˜Â§Ã˜Â¡Ã™â€¹ Ã™â€žÃ™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™â€¦Ã™Å Ã™â€ Ã˜Å’ Ã™â€šÃ™ÂÃ˜ÂªÃ™â€ž Ã™ÂÃ™Å  Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ø¨Ø¯Ø± Ã˜Â§Ã™â€žÃ™Æ’Ã˜Â¨Ã˜Â±Ã™â€°.", type: "person", gender: "male" },
    "Ã˜Â£Ã˜Â¨Ã™Ë† Ã™â€žÃ™â€¡Ø¨": { def: "Ã˜Â¹Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Ë†Ã˜Â¹Ã˜Â¯Ã™Ë†Ã™â€¡ Ã˜Â§Ã™â€žÃ™â€žÃ˜Â¯Ã™Ë†Ã˜Â¯Ã˜Å’ Ã™â€ Ã˜Â²Ã™â€žØª Ã™ÂÃ™Å Ã™â€¡ Ã™Ë†Ã˜Â²Ã™Ë†Ã˜Â¬Ã˜ÂªÃ™â€¡ Ã˜Â³Ã™Ë†Ø±Ø© Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã˜Â¯Ã˜Å’ Ã™â€žÃ˜Â¹Ã™â€ Ã™â€¡ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã™â€žØ´Ø¯Ø© Ã˜Â¹Ã˜Â¯Ã˜Â§Ã˜Â¦Ã™â€¡ Ã™â€žÃ™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦ Ã™Ë†Ã˜Â±Ã˜Â³Ã™Ë†Ã™â€žÃ™â€¡.", type: "person", gender: "male" },
    "Ø³Ø¹Ø¯ Ã˜Â¨Ã™â€  Ø¹Ø¨Ø§Ø¯Ø©": { def: "Ã˜Â³Ã™Å Ø¯ Ã˜Â§Ã™â€žØ®Ø²Ø±Ø¬ Ã™Ë†Ã˜Â²Ã˜Â¹Ã™Å Ã™â€¦ Ã˜Â§Ã™â€žÃ˜Â£Ã™â€ Ã˜ÂµÃ˜Â§Ã˜Â±Ã˜Å’ Ã™Æ’Ã˜Â§Ã™â€  Ã™Å Ã™â€ Ã˜Â§Ã™ÂØ³ Ø³Ø¹Ø¯ Ã˜Â¨Ã™â€  Ã™â€¦Ø¹Ø§Ø° Ã˜Â¹Ã™â€žÃ™â€° Ã˜Â¥Ã™â€¦Ø§Ø±Ø© Ã˜Â§Ã™â€žÃ˜Â£Ã™â€ ØµØ§Ø± Ã™Ë†Ã˜Â´Ã™â€¡Ø¯ Ã˜ÂºÃ˜Â²Ã™Ë†Ø§Øª Ã™Æ’Ã˜Â«Ã™Å Ø±Ø© Ã™â€¦Ø¹ Ã˜Â§Ã™â€žÃ™â€ Ø¨ÙŠ ï·º.", type: "person", gender: "male" },
    "Ã˜Â·Ã™â€žØ­Ø© Ã˜Â¨Ã™â€  Ã˜Â¹Ã˜Â¨Ã™Å Ø¯ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡": { def: "Ø£Ø­Ø¯ Ã˜Â§Ã™â€žØ¹Ø´Ø±Ø© Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¨Ã˜Â´Ã˜Â±Ã™Å Ã™â€  Ã˜Â¨Ã˜Â§Ã™â€žÃ˜Â¬Ã™â€ Ã˜Â©Ã˜Å’ Ã™Ë†Ã™â€šÃ™Â Ã™Å Ã™Ë†Ã™â€¦ Ã˜Â£Ã™ÂØ­Ø¯ Ã˜Â¯Ã˜Â±Ã˜Â¹Ã˜Â§Ã™â€¹ Ã™â€žÃ™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Ë†Ã˜Â£Ã˜ÂµÃ™Å Ø¨Øª Ã™Å Ã˜Â¯Ã™â€¡ Ã˜Â­Ã™Å Ã™â€  Ã˜Â£Ã™â€ Ã™â€šÃ˜Â°Ã™â€¡Ã˜Å’ Ã™ÂÃ™â€šÃ˜Â§Ã™â€ž Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å : Ã˜Â£Ã™Ë†Ø¬Ø¨ Ã˜Â·Ã™â€žØ­Ø©.", type: "person", gender: "male" },
    "Ã˜Â§Ã™â€žÃ˜Â²Ã˜Â¨Ã™Å Ø± Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ˜Â¹Ã™Ë†Ã˜Â§Ã™â€¦": { def: "Ø£Ø­Ø¯ Ã˜Â§Ã™â€žØ¹Ø´Ø±Ø© Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¨Ã˜Â´Ã˜Â±Ã™Å Ã™â€  Ã˜Â¨Ã˜Â§Ã™â€žÃ˜Â¬Ã™â€ Ø© Ã™Ë†Ã˜Â­Ã™Ë†Ã˜Â§Ã˜Â±Ã™Å  Ã˜Â±Ã˜Â³Ã™Ë†Ã™â€ž Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã¯Â·Âº Ã™Ë†Ã˜Â§Ã˜Â¨Ã™â€  Ã˜Â¹Ã™â€¦Ã˜ÂªÃ™â€¡ Ã˜ÂµÃ™ÂÃ™Å Ã˜Â©Ã˜Å’ Ã™Æ’Ã˜Â§Ã™â€  Ã™ÂÃ˜Â§Ã˜Â±Ã˜Â³Ã˜Â§Ã™â€¹ Ã˜Â´Ã˜Â¬Ã˜Â§Ã˜Â¹Ã˜Â§Ã™â€¹ Ã™â€žØ§ Ã™Å Ã™ÂÃ˜Â¨Ã˜Â§Ã˜Â±Ã™â€° Ã™ÂÃ™Å  Ã™â€¦Ã™Å Ã˜Â§Ã˜Â¯Ã™Å Ã™â€  Ã˜Â§Ã™â€žÃ™â€šÃ˜ÂªÃ˜Â§Ã™â€ž.", type: "person", gender: "male" },
    "Ã™Æ’Ø¹Ø¨ Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ˜Â£Ã˜Â´Ã˜Â±Ã™Â": { def: "Ã˜Â²Ã˜Â¹Ã™Å Ã™â€¦ Ã™Å Ã™â€¡Ã™Ë†Ã˜Â¯Ã™Å  Ã™â€¦Ã™â€  Ã˜Â¨Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¶Ã™Å Ã˜Â±Ã˜Å’ Ã˜Â­Ã˜Â±Ã™â€˜Ø¶ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã˜Â±Ã™Æ’Ã™Å Ã™â€  Ø¶Ø¯ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™â€¦Ã™Å Ã™â€  Ã™Ë†Ã™â€¡Ø¬Ø§ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã˜Â¨Ã˜Â´Ã˜Â¹Ã˜Â±Ã™â€¡Ã˜Å’ Ã™ÂÃ˜Â£Ã˜Â°Ã™â€  Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã˜Â¨Ã™â€šÃ˜ÂªÃ™â€žÃ™â€¡ Ã™ÂÃ™â€ Ã™ÂØ° Ã˜Â§Ã™â€žÃ˜Â£Ã™â€¦Ø± Ã™â€¦Ã˜Â­Ã™â€¦Ø¯ Ã˜Â¨Ã™â€  Ã™â€¦Ã˜Â³Ã™â€žÃ™â€¦Ø©.", type: "person", gender: "male" },
    // Ã™â€ Ø³Ø§Ø¡ Ã˜Â§Ã™â€žØµØ­Ø§Ø¨Ø© Ã™Ë†Ã˜Â£Ã™â€¦Ã™â€¡Ø§Øª Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¤Ã™â€¦Ã™â€ Ã™Å Ã™â€ 
    "Ã˜Â²Ã™Å Ã™â€ Ø¨ Ã˜Â¨Ã™â€ Øª Ø¬Ø­Ø´": { def: "Ã˜Â£Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¤Ã™â€¦Ã™â€ Ã™Å Ã™â€ Ã˜Å’ Ã˜Â²Ã™Ë†Ø¬Ø© Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·ÂºÃ˜Å’ Ã˜ÂªÃ˜Â²Ã™Ë†Ã˜Â¬Ã™â€¡Ø§ Ã˜Â¨Ã˜Â£Ã™â€¦Ø± Ã™â€¦Ã™â€  Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã™â€žÃ˜Â¥Ã˜Â¨Ã˜Â·Ã˜Â§Ã™â€ž Ã˜Â­Ã™Æ’Ã™â€¦ Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â¨Ã™â€ Ã™Å  Ã˜Â¹Ã™â€¦Ã™â€žÃ™Å Ã˜Â§Ã™â€¹Ã˜Å’ Ã™Ë†Ã™Æ’Ã˜Â§Ã™â€ Øª Ã˜ÂªÃ™ÂØ®Ø± Ã˜Â¨Ã˜Â£Ã™â€  Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â²Ã™Ë†Ã™â€˜Ã˜Â¬Ã™â€¡Ø§ Ã™â€¦Ã™â€  Ã™ÂÃ™Ë†Ã™â€š Ø³Ø¨Ø¹ Ã˜Â³Ã™â€¦Ã˜Â§Ã™Ë†Ø§Øª.", type: "person", gender: "female" },
    "Ø¹Ø§Ø¦Ø´Ø© Ã˜Â¨Ã™â€ Øª Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â¨Ã™Æ’Ø±": { def: "Ã˜Â£Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¤Ã™â€¦Ã™â€ Ã™Å Ã™â€  Ã™Ë†Ã˜Â­Ã˜Â¨Ã™Å Ø¨Ø© Ã˜Â±Ã˜Â³Ã™Ë†Ã™â€ž Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã¯Â·ÂºÃ˜Å’ Ã˜Â£Ã™Æ’Ø«Ø± Ã˜Â§Ã™â€žØµØ­Ø§Ø¨Ø© Ã˜Â±Ã™Ë†Ã˜Â§Ã™Å Ø© Ã™â€žÃ™â€žÃ˜Â­Ã˜Â¯Ã™Å Ø« Ø¨Ø¹Ø¯ Ã˜Â£Ã˜Â¨Ã™Å  Ã™â€¡Ã˜Â±Ã™Å Ã˜Â±Ã˜Â©Ã˜Å’ Ã˜Â¨Ã˜Â±Ã˜Â£Ã™â€¡Ø§ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ™â€šÃ˜Â±Ã˜Â¢Ã™â€  Ã™â€¦Ã™â€  Ø­Ø§Ø¯Ø«Ø© Ã˜Â§Ã™â€žÃ˜Â¥Ã™ÂÃ™Æ’.", type: "person", gender: "female" },
    "Ã˜Â®Ã˜Â¯Ã™Å Ø¬Ø© Ã˜Â¨Ã™â€ Øª Ã˜Â®Ã™Ë†Ã™Å Ã™â€žØ¯": { def: "Ã˜Â£Ã™Ë†Ã™â€ž Ã˜Â£Ã™â€¦Ã™â€¡Ø§Øª Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¤Ã™â€¦Ã™â€ Ã™Å Ã™â€  Ã™Ë†Ã˜Â£Ã™Ë†Ã™â€ž Ã™â€¦Ã™â€  Ã˜Â¢Ã™â€¦Ã™â€  Ã˜Â¨Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·ÂºÃ˜Å’ Ã™Ë†Ã™â€¡Ø¨Øª Ã™â€¦Ã˜Â§Ã™â€žÃ™â€¡Ø§ Ã™Ë†Ã™â€ Ã™ÂÃ˜Â³Ã™â€¡Ø§ Ã™â€žÃ™â€žÃ˜Â¯Ã˜Â¹Ã™Ë†Ã˜Â©Ã˜Å’ Ã™Ë†Ã˜Â¨Ã˜Â´Ã™â€˜Ã˜Â±Ã™â€¡Ø§ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã˜Â¨Ã˜Â¨Ã™Å Øª Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â¬Ã™â€ Ø© Ã™â€¦Ã™â€  Ã™â€šØµØ¨ Ã™â€žØ§ ØµØ®Ø¨ Ã™ÂÃ™Å Ã™â€¡ Ã™Ë†Ã™â€žØ§ Ã™â€ ØµØ¨.", type: "person", gender: "female" },
    "Ã™ÂÃ˜Â§Ã˜Â·Ã™â€¦Ø© Ã˜Â§Ã™â€žÃ˜Â²Ã™â€¡Ø±Ø§Ø¡": { def: "Ã˜Â³Ã™Å Ø¯Ø© Ã™â€ Ø³Ø§Ø¡ Ã˜Â§Ã™â€žÃ˜Â¹Ã˜Â§Ã™â€žÃ™â€¦Ã™Å Ã™â€  Ã™Ë†Ã˜Â§Ã˜Â¨Ã™â€ Ø© Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Ë†Ã˜Â²Ã™Ë†Ø¬Ø© Ã˜Â¹Ã™â€žÃ™Å  Ã˜Â¨Ã™â€  Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â·Ã˜Â§Ã™â€žÃ˜Â¨Ã˜Å’ Ã™â€šÃ˜Â§Ã™â€ž Ã˜Â¹Ã™â€ Ã™â€¡Ø§ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å : Ã™ÂÃ˜Â§Ã˜Â·Ã™â€¦Ø© Ø¨Ø¶Ø¹Ø© Ã™â€¦Ã™â€ Ã™Å  Ã™ÂÃ™â€¦Ã™â€  Ã˜Â¢Ã˜Â°Ã˜Â§Ã™â€¡Ø§ Ã™ÂÃ™â€šØ¯ Ã˜Â¢Ã˜Â°Ã˜Â§Ã™â€ ÙŠ.", type: "person", gender: "female" },
    "Ã˜Â£Ã™â€¦ Ã˜Â³Ã™â€žÃ™â€¦Ø©": { def: "Ã˜Â£Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¤Ã™â€¦Ã™â€ Ã™Å Ã™â€  Ã™â€¡Ã™â€ Ø¯ Ã˜Â¨Ã™â€ Øª Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â£Ã™â€¦Ã™Å Ã˜Â©Ã˜Å’ Ã™â€¡Ø§Ø¬Ø±Øª Ã˜Â¥Ã™â€žÃ™â€° Ã˜Â§Ã™â€žØ­Ø¨Ø´Ø© Ã˜Â«Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ã˜Â©Ã˜Å’ Ã˜Â§Ã˜Â´Ã˜ÂªÃ™ÂÃ™â€¡Ø±Øª Ã˜Â¨Ã˜Â­Ã™Æ’Ã™â€¦Ã˜ÂªÃ™â€¡Ø§ Ã™Ë†Ã™â€ Ã˜ÂµÃ˜Â­Ã™â€¡Ø§ Ã™â€žÃ™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Å Ã™Ë†Ã™â€¦ Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â¯Ã™Å Ã˜Â¨Ã™Å Ø©.", type: "person", gender: "female" },
    "Ã˜ÂµÃ™ÂÃ™Å Ø© Ã˜Â¨Ã™â€ Øª Ø­ÙŠÙŠ": { def: "Ã˜Â£Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¤Ã™â€¦Ã™â€ Ã™Å Ã™â€ Ã˜Å’ Ã˜Â¨Ã™â€ Øª Ã˜Â²Ã˜Â¹Ã™Å Ã™â€¦ Ã˜Â¨Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¶Ã™Å Ø± Ã˜Â­Ã™Å Ã™Å  Ã˜Â¨Ã™â€  Ã˜Â£Ã˜Â®Ã˜Â·Ã˜Â¨Ã˜Å’ Ã˜ÂªÃ˜Â²Ã™Ë†Ã˜Â¬Ã™â€¡Ø§ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ø¨Ø¹Ø¯ Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â®Ã™Å Ã˜Â¨Ã˜Â±Ã˜Å’ Ã™Ë†Ã™Æ’Ã˜Â§Ã™â€ Øª Ã˜ÂªÃ˜Â¯Ã˜Â§Ã™ÂØ¹ Ã˜Â¹Ã™â€  Ã˜Â´Ã˜Â±Ã™Â Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã˜Â¨Ã™â€žÃ˜Â³Ã˜Â§Ã™â€ Ã™â€¡Ø§.", type: "person", gender: "female" },
    "Ã˜Â­Ã™ÂØµØ© Ã˜Â¨Ã™â€ Øª Ã˜Â¹Ã™â€¦Ø±": { def: "Ã˜Â£Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¤Ã™â€¦Ã™â€ Ã™Å Ã™â€  Ã™Ë†Ã˜Â§Ã˜Â¨Ã™â€ Ø© Ã˜Â¹Ã™â€¦Ø± Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ˜Â®Ã˜Â·Ã˜Â§Ã˜Â¨Ã˜Å’ Ã˜Â§Ã˜Â´Ã˜ÂªÃ™â€¡Ø±Øª Ã˜Â¨Ã˜Â§Ã™â€žÃ˜ÂµÃ™Å Ã˜Â§Ã™â€¦ Ã™Ë†Ã˜Â§Ã™â€žÃ™â€šÃ™Å Ã˜Â§Ã™â€¦Ã˜Å’ Ã™Ë†Ã˜Â¹Ã™â€ Ã˜Â¯Ã™â€¡Ø§ Ã˜Â­Ã™ÂÃ™ÂØ¸Øª Ã˜Â§Ã™â€žÃ™â€¦Ã˜ÂµÃ˜Â­Ã™Â Ã˜Â§Ã™â€žÃ˜Â£Ã™Ë†Ã™â€ž Ã˜Â§Ã™â€žÃ˜Â°Ã™Å  Ã˜Â¬Ã™â€¦Ã˜Â¹Ã™â€¡ Ã˜Â£Ã˜Â¨Ã™Ë† Ã˜Â¨Ã™Æ’Ø± Ã˜Â±Ã˜Â¶Ã™Å  Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¹Ã™â€ Ã™â€¡.", type: "person", gender: "female" },
    "Ã˜Â±Ã™â€šÃ™Å Ø© Ã˜Â¨Ã™â€ Øª Ã™â€¦Ã˜Â­Ã™â€¦Ø¯": { def: "Ã˜Â¨Ã™â€ Øª Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Ë†Ã˜Â²Ã™Ë†Ø¬Ø© Ã˜Â¹Ã˜Â«Ã™â€¦Ã˜Â§Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™ÂÃ˜Â§Ã™â€ Ã˜Å’ Ã™â€¡Ø§Ø¬Ø±Øª Ã™â€¦Ã˜Â¹Ã™â€¡ Ã˜Â¥Ã™â€žÃ™â€° Ã˜Â§Ã™â€žØ­Ø¨Ø´Ø© Ã˜Â«Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ã˜Â©Ã˜Å’ Ã™Ë†Ã˜ÂªÃ™Ë†Ã™ÂÃ™Å Øª Ã™Å Ã™Ë†Ã™â€¦ Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ø¨Ø¯Ø± Ã™Ë†Ã™â€¡Ã™Ë† Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¹Ã˜Â±Ã™Æ’Ø©.", type: "person", gender: "female" },
    "Ã˜Â£Ã™â€¦ Ã™Æ’Ã™â€žÃ˜Â«Ã™Ë†Ã™â€¦ Ã˜Â¨Ã™â€ Øª Ã™â€¦Ã˜Â­Ã™â€¦Ø¯": { def: "Ã˜Â¨Ã™â€ Øª Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™Ë†Ã˜Â²Ã™Ë†Ø¬Ø© Ã˜Â¹Ã˜Â«Ã™â€¦Ã˜Â§Ã™â€  Ã˜Â¨Ã™â€  Ã˜Â¹Ã™ÂÃ˜Â§Ã™â€  Ø¨Ø¹Ø¯ Ã™Ë†Ã™ÂØ§Ø© Ã˜Â£Ã˜Â®Ã˜ÂªÃ™â€¡Ø§ Ã˜Â±Ã™â€šÃ™Å Ã˜Â©Ã˜Å’ Ã™Ë†Ã™â€žÃ™â€¡Ø°Ø§ Ã˜Â³Ã™ÂÃ™â€¦Ã™Å  Ã˜Â¹Ã˜Â«Ã™â€¦Ã˜Â§Ã™â€  Ã˜Â¨Ã˜Â°Ã™Å  Ã˜Â§Ã™â€žÃ™â€ Ã™Ë†Ã˜Â±Ã™Å Ã™â€ .", type: "person", gender: "female" },
    "Ã˜Â²Ã™Å Ã™â€ Ø¨ Ã˜Â¨Ã™â€ Øª Ã™â€¦Ã˜Â­Ã™â€¦Ø¯": { def: "Ã˜Â£Ã™Æ’Ø¨Ø± Ã˜Â¨Ã™â€ Ø§Øª Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·ÂºÃ˜Å’ Ã˜ÂªÃ˜Â²Ã™Ë†Ø¬Øª Ø£Ø¨Ø§ Ã˜Â§Ã™â€žØ¹Ø§Øµ Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ˜Â±Ã˜Â¨Ã™Å Ø¹ Ã™â€šÃ˜Â¨Ã™â€ž Ã˜Â§Ã™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦Ã˜Å’ Ã™Ë†Ã™â€¡Ø§Ø¬Ø±Øª Ã˜Â¥Ã™â€žÃ™â€° Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ø© Ø¨Ø¹Ø¯ Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ø¨Ø¯Ø± Ã™Ë†Ã˜ÂªÃ™Ë†Ã™ÂÃ™Å Øª Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â³Ã™â€ Ø© Ã˜Â§Ã™â€žÃ˜Â«Ã˜Â§Ã™â€¦Ã™â€ Ø©.", type: "person", gender: "female" },
    "Ã™â€¡Ã™â€ Ø¯ Ã˜Â¨Ã™â€ Øª Ø¹ØªØ¨Ø©": { def: "Ã˜Â²Ã™Ë†Ø¬Ø© Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â³Ã™ÂÃ™Å Ã˜Â§Ã™â€  Ã™Ë†Ã˜Â£Ã™â€¦ Ã™â€¦Ã˜Â¹Ã˜Â§Ã™Ë†Ã™Å Ã˜Â©Ã˜Å’ Ã˜Â£Ã™â€¦Ø±Øª Ã˜Â¨Ã™â€šÃ˜ÂªÃ™â€ž Ã˜Â­Ã™â€¦Ø²Ø© Ã™Å Ã™Ë†Ã™â€¦ Ã˜Â£Ã™ÂØ­Ø¯ Ã™Ë†Ã˜Â´Ã™â€šØª Ã˜ÂµÃ˜Â¯Ã˜Â±Ã™â€¡Ã˜Å’ Ã˜Â£Ã˜Â³Ã™â€žÃ™â€¦Øª Ã™Å Ã™Ë†Ã™â€¦ Ã™ÂØªØ­ Ã™â€¦Ã™Æ’Ø© Ã™Ë†Ã˜Â­Ã˜Â³Ã™â€  Ã˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦Ã™â€¡Ø§.", type: "person", gender: "female" },
    "Ã˜Â£Ã˜Â³Ã™â€¦Ø§Ø¡ Ã˜Â¨Ã™â€ Øª Ã˜Â£Ã˜Â¨Ã™Å  Ã˜Â¨Ã™Æ’Ø±": { def: "Ø°Ø§Øª Ã˜Â§Ã™â€žÃ™â€ Ã˜Â·Ã˜Â§Ã™â€šÃ™Å Ã™â€  Ã™Ë†Ø£Ø®Øª Ã˜Â¹Ã˜Â§Ã˜Â¦Ã˜Â´Ã˜Â©Ã˜Å’ Ã˜Â£Ã˜Â¹Ã˜Â§Ã™â€ Øª Ã˜Â£Ã˜Â¨Ã˜Â§Ã™â€¡Ø§ Ã™Ë†Ã˜Â²Ã™Ë†Ø¬ Ã˜Â£Ã˜Â®Ã˜ÂªÃ™â€¡Ø§ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ™â€¡Ø¬Ø±Ø© Ã˜Â¨Ã˜Â­Ã™â€¦Ã™â€ž Ã˜Â§Ã™â€žÃ˜Â²Ã˜Â§Ã˜Â¯Ã˜Å’ Ã™Ë†Ã˜Â£Ã™â€ Ø¬Ø¨Øª Ã˜Â£Ã™Ë†Ã™â€ž Ã™â€¦Ã™Ë†Ã™â€žÃ™Ë†Ø¯ Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦ Ã˜Â¨Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ø©.", type: "person", gender: "female" },
    "Ã™â€¦Ã˜Â§Ã˜Â±Ã™Å Ø§ Ã˜Â§Ã™â€žÃ™â€šÃ˜Â¨Ã˜Â·Ã™Å Ø©": { def: "Ã˜Â£Ã™â€¦ Ã˜Â¥Ã˜Â¨Ã˜Â±Ã˜Â§Ã™â€¡Ã™Å Ã™â€¦ Ã˜Â§Ã˜Â¨Ã™â€  Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·ÂºÃ˜Å’ Ã˜Â£Ã™â€¡Ã˜Â¯Ã˜Â§Ã™â€¡Ø§ Ã˜Â§Ã™â€žÃ™â€¦Ã™â€šÃ™Ë†Ã™â€šØ³ Ã™â€¦Ã™â€žÃ™Æ’ Ã™â€¦ØµØ± Ã˜Â¥Ã™â€žÃ™â€° Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·ÂºÃ˜Å’ Ã™Ë†Ã˜ÂªÃ™Ë†Ã™ÂÃ™Å  Ã˜Â§Ã˜Â¨Ã™â€ Ã™â€¡Ø§ Ã˜Â¥Ã˜Â¨Ã˜Â±Ã˜Â§Ã™â€¡Ã™Å Ã™â€¦ Ã˜ÂµÃ˜ÂºÃ™Å Ã˜Â±Ã˜Â§Ã™â€¹ Ã™ÂÃ˜Â¨Ã™Æ’Ã™â€° Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã™Ë†Ã™â€šÃ˜Â§Ã™â€ž: Ã˜Â¥Ã™â€  Ã˜Â§Ã™â€žÃ˜Â¹Ã™Å Ã™â€  Ã˜ÂªÃ˜Â¯Ã™â€¦Ø¹ Ã™Ë†Ã˜Â§Ã™â€žÃ™â€šÃ™â€žØ¨ Ã™Å Ã˜Â­Ã˜Â²Ã™â€ .", type: "person", gender: "female" },
    // Ã˜Â§Ã™â€žØ£Ø­Ø¯Ø§Ø« Ã™Ë†Ã˜Â§Ã™â€žÃ˜ÂºÃ˜Â²Ã™Ë†Ø§Øª
    "Ã˜Â¨Ã™â€ Ã™Ë† Ã™â€šÃ™Å Ã™â€ Ã™â€šØ§Ø¹": { def: "Ã˜Â£Ã™Ë†Ã™â€ž Ã™â€šÃ˜Â¨Ã˜Â§Ã˜Â¦Ã™â€ž Ã˜Â§Ã™â€žÃ™Å Ã™â€¡Ã™Ë†Ø¯ Ã˜Â¨Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ø© Ã™â€ Ã™â€šÃ˜Â¶Ã˜Â§Ã™â€¹ Ã™â€žÃ™â€žÃ˜Â¹Ã™â€¡Ø¯ Ã™â€¦Ø¹ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ø¨Ø¹Ø¯ Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â¨Ã˜Â¯Ã˜Â±Ã˜Å’ Ã™ÂÃ˜ÂªÃ™â€¦ Ã˜Â­Ã˜ÂµÃ˜Â§Ã˜Â±Ã™â€¡Ã™â€¦ Ã™Ë†Ã˜Â¥Ã˜Â¬Ã™â€žÃ˜Â§Ã˜Â¤Ã™â€¡Ã™â€¦ Ã˜Â¹Ã™â€  Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ø©.", type: "tribe" },
    "Ã˜Â¨Ã™â€ Ã™Ë† Ã™â€šÃ˜Â±Ã™Å Ø¸Ø©": { def: "Ã˜Â¥Ã˜Â­Ã˜Â¯Ã™â€° Ã™â€šÃ˜Â¨Ã˜Â§Ã˜Â¦Ã™â€ž Ã˜Â§Ã™â€žÃ™Å Ã™â€¡Ã™Ë†Ø¯ Ã˜Â¨Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ø© Ã˜Â§Ã™â€žÃ˜Â°Ã™Å Ã™â€  Ã˜ÂªÃ˜Â­Ã˜Â§Ã™â€žÃ™ÂÃ™Ë†Ø§ Ã™â€¦Ø¹ Ã˜Â§Ã™â€žØ£Ø­Ø²Ø§Ø¨ Ã™Ë†Ã™â€ Ã™â€šÃ˜Â¶Ã™Ë†Ø§ Ã˜Â¹Ã™â€¡Ã˜Â¯Ã™â€¡Ã™â€¦ Ã™â€¦Ø¹ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™â€¦Ã™Å Ã™â€ Ã˜Å’ Ã™ÂÃ˜Â­Ã™ÂÃ™Ë†Ã˜ÂµÃ˜Â±Ã™Ë†Ø§ Ã™Ë†Ã˜Â­Ã™Æ’Ã™â€¦ Ã™ÂÃ™Å Ã™â€¡Ã™â€¦ Ø³Ø¹Ø¯ Ã˜Â¨Ã™â€  Ã™â€¦Ø¹Ø§Ø°.", type: "tribe" },
    "Ã˜Â¨Ã™â€ Ã™Ë† Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¶Ã™Å Ø±": { def: "Ã™â€šÃ˜Â¨Ã™Å Ã™â€žØ© Ã™Å Ã™â€¡Ã™Ë†Ã˜Â¯Ã™Å Ø© Ã˜Â¨Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ø© Ã˜ÂªÃ˜Â¢Ã™â€¦Ø±Øª Ã˜Â¹Ã™â€žÃ™â€° Ã™â€šÃ˜ÂªÃ™â€ž Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã˜Â¨Ã™â€žÃ™â€šØ§Ø¡ Ã˜ÂµÃ˜Â®Ã˜Â±Ã˜Â©Ã˜Å’ Ã™ÂÃ˜Â­Ã˜Â§Ã˜ÂµÃ˜Â±Ã™â€¡Ã™â€¦ Ã™Ë†Ã˜Â£Ã˜Â¬Ã™â€žÃ˜Â§Ã™â€¡Ã™â€¦ Ã˜Â¥Ã™â€žÃ™â€° Ã˜Â®Ã™Å Ø¨Ø± Ã™Ë†Ã˜Â§Ã™â€žÃ˜Â´Ã˜Â§Ã™â€¦.", type: "tribe" },
    "Ø¨Ø¯Ø± Ã˜Â§Ã™â€žÃ™â€¦Ã™Ë†Ø¹Ø¯": { def: "Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ø¨Ø¯Ø± Ã˜Â§Ã™â€žÃ˜ÂµÃ˜ÂºÃ˜Â±Ã™â€° Ã˜Â£Ã™Ë† Ã˜Â§Ã™â€žÃ˜Â«Ã˜Â§Ã™â€ Ã™Å Ã˜Â©Ã˜Å’ Ø®Ø±Ø¬ Ã™ÂÃ™Å Ã™â€¡Ø§ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™â€¦Ã™Ë†Ã™â€  Ã™â€žÃ™â€žÃ™â€šØ§Ø¡ Ã™â€šÃ˜Â±Ã™Å Ø´ Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â³Ã™â€ Ø© Ã˜Â§Ã™â€žØ±Ø§Ø¨Ø¹Ø© Ã™â€žÃ™â€žÃ™â€¡Ø¬Ø±Ø© Ã™Ë†ØªØ±Ø§Ø¬Ø¹ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã˜Â±Ã™Æ’Ã™Ë†Ã™â€  Ã˜Â±Ã˜Â¹Ã˜Â¨Ã˜Â§Ã™â€¹.", type: "event" },
    "Ã˜Â²Ã™Æ’Ø§Ø© Ã˜Â§Ã™â€žÃ™ÂØ·Ø±": { def: "Ã˜ÂµÃ˜Â¯Ã™â€šØ© ØªØ¬Ø¨ Ã˜Â¹Ã™â€žÃ™â€° Ã™Æ’Ã™â€ž Ã™â€¦Ã˜Â³Ã™â€žÃ™â€¦ Ã™â€šÃ˜Â¨Ã™â€ž Ã˜ÂµÃ™â€žØ§Ø© Ã˜Â¹Ã™Å Ø¯ Ã˜Â§Ã™â€žÃ™ÂØ·Ø± Ã˜Â·Ã™â€¡Ø±Ø© Ã™â€žÃ™â€žÃ˜ÂµÃ˜Â§Ã˜Â¦Ã™â€¦ Ã™Ë†Ã˜Â·Ã˜Â¹Ã™â€¦Ø© Ã™â€žÃ™â€žÃ™â€¦Ã˜Â³Ã˜Â§Ã™Æ’Ã™Å Ã™â€ Ã˜Å’ Ã™ÂØ±Ø¶Øª Ã™ÂÃ™Å  Ã˜Â´Ã˜Â¹Ã˜Â¨Ã˜Â§Ã™â€  Ã™â€¦Ã™â€  Ã˜Â§Ã™â€žÃ˜Â³Ã™â€ Ø© Ã˜Â§Ã™â€žÃ˜Â«Ã˜Â§Ã™â€ Ã™Å Ø© Ã™â€žÃ™â€žÃ™â€¡Ø¬Ø±Ø©.", type: "concept" },
    "Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â¨Ã™â€ ÙŠ": { def: "Ø§Ø¯Ø¹Ø§Ø¡ Ã˜Â¨Ã™â€ Ã™Ë†Ø© Ã˜Â·Ã™ÂÃ™â€ž Ã™â€žÃ˜ÂºÃ™Å Ø± Ã˜Â£Ã˜Â¨Ã™Å Ã™â€¡ Ã˜Â§Ã™â€žÃ˜Â­Ã™â€šÃ™Å Ã™â€šÃ™Å Ã˜Å’ Ã™Ë†Ã™â€šØ¯ Ã˜Â£Ã˜Â¨Ã˜Â·Ã™â€žÃ™â€¡ Ã˜Â§Ã™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦ Ã˜Â¹Ã™â€¦Ã™â€žÃ™Å Ã˜Â§Ã™â€¹ Ã™Ë†Ã™â€ Ã˜Â¸Ã˜Â±Ã™Å Ã˜Â§Ã™â€¹ Ã™â€žÃ˜ÂµÃ™Å Ã˜Â§Ã™â€ Ø© Ã˜Â§Ã™â€žÃ˜Â£Ã™â€ Ø³Ø§Ø¨ Ã™â€¦Ã™â€  Ã˜Â§Ã™â€žÃ˜Â¶Ã™Å Ø§Ø¹.", type: "concept" },
    "Ø°Ø§Øª Ã˜Â§Ã™â€žÃ˜Â±Ã™â€šØ§Ø¹": { def: "Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â³Ã™ÂÃ™â€¦Ã™Å Øª Ã˜Â¨Ã˜Â°Ã™â€žÃ™Æ’ Ã™â€žÃ˜Â£Ã™â€  Ã˜Â§Ã™â€žØµØ­Ø§Ø¨Ø© Ã˜Â±Ã˜Â¶Ã™Å  Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¹Ã™â€ Ã™â€¡Ã™â€¦ Ã™â€žÃ™ÂÃ™Ë†Ø§ Ã˜Â§Ã™â€žÃ˜Â®Ã˜Â±Ã™â€š Ã˜Â¹Ã™â€žÃ™â€° Ã˜Â£Ã™â€šÃ˜Â¯Ã˜Â§Ã™â€¦Ã™â€¡Ã™â€¦ Ã™â€¦Ã™â€  Ø´Ø¯Ø© Ã˜Â§Ã™â€žØ­Ø± Ã™Ë†Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã™Å Ã˜Å’ Ã™Ë†Ã™â€ Ã˜Â²Ã™â€žØª Ã™ÂÃ™Å Ã™â€¡Ø§ Ø±Ø®Øµ Ã™Æ’Ã˜ÂµÃ™â€žØ§Ø© Ã˜Â§Ã™â€žÃ˜Â®Ã™Ë†Ã™Â Ã™Ë†Ã˜Â§Ã™â€žÃ˜ÂªÃ™Å Ã™â€¦Ã™â€¦.", type: "event" },
    "Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â§Ã™â€žØ£Ø­Ø²Ø§Ø¨": { def: "Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â§Ã™â€žÃ˜Â®Ã™â€ Ã˜Â¯Ã™â€š (Ã˜Â§Ã™â€žÃ˜Â³Ã™â€ Ø© Ã˜Â§Ã™â€žÃ˜Â®Ã˜Â§Ã™â€¦Ø³Ø© Ã™â€žÃ™â€žÃ™â€¡Ø¬Ø±Ø©) Ã˜Â­Ã™Å Ø« Ã˜ÂªÃ˜Â¬Ã™â€¦Ø¹Øª Ã™â€šÃ˜Â¨Ã˜Â§Ã˜Â¦Ã™â€ž Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã˜Â±Ã™Æ’Ã™Å Ã™â€  Ã™Ë†Ã˜Â§Ã™â€žÃ™Å Ã™â€¡Ã™Ë†Ø¯ Ã™â€žÃ™â€¦Ø­Ø§ØµØ±Ø© Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™â€¦Ã™Å Ã™â€ Ã˜Å’ Ã™ÂÃ™â€¡Ã˜Â²Ã™â€¦Ã™â€¡Ã™â€¦ Ã˜Â§Ã™â€žÃ™â€žÃ™â€¡ Ã˜Â¨Ã˜Â§Ã™â€žÃ˜Â±Ã™Å Ø­ Ã™Ë†Ã˜Â§Ã™â€žÃ˜Â¬Ã™â€ Ã™Ë†Ø¯.", type: "event" },
    "Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â¨Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ™â€¦Ã˜ÂµÃ˜Â·Ã™â€žÃ™â€š": { def: "Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â±Ã™Å Ã˜Â³Ã™Å Ø¹ (Ã˜Â§Ã™â€žÃ˜Â³Ã™â€ Ø© Ã˜Â§Ã™â€žØ³Ø§Ø¯Ø³Ø© Ã™â€žÃ™â€žÃ™â€¡Ø¬Ø±Ø©) Ã™â€¡Ã˜Â²Ã™â€¦ Ã™ÂÃ™Å Ã™â€¡Ø§ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã™â€žÃ™â€¦Ã™Ë†Ã™â€  Ã˜Â¨Ã™â€ Ã™Å  Ã˜Â§Ã™â€žÃ™â€¦Ã˜ÂµÃ˜Â·Ã™â€žÃ™â€š Ã™Ë†Ø­Ø¯Ø«Øª Ã™ÂÃ™Å Ã™â€¡Ø§ Ø­Ø§Ø¯Ø«Ø© Ã˜Â§Ã™â€žÃ˜Â¥Ã™ÂÃ™Æ’ Ã˜Â§Ã™â€žÃ™â€¦Ã™ÂÃ˜ÂªÃ˜Â±Ã™Å Ø©.", type: "event" },
    "Ã˜Â¯Ã™Ë†Ã™â€¦Ø© Ã˜Â§Ã™â€žÃ˜Â¬Ã™â€ Ã˜Â¯Ã™â€ž": { def: "Ã˜ÂºÃ˜Â²Ã™Ë†Ø© Ã™â€šÃ˜Â§Ã˜Â¯Ã™â€¡Ø§ Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Å  Ã¯Â·Âº Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â³Ã™â€ Ø© Ã˜Â§Ã™â€žÃ˜Â®Ã˜Â§Ã™â€¦Ø³Ø© Ã™â€žÃ™â€žÃ™â€¡Ø¬Ø±Ø© Ã™â€žÃ˜ÂªÃ˜Â£Ã™â€¦Ã™Å Ã™â€  Ã˜Â§Ã™â€žÃ˜Â­Ã˜Â¯Ã™Ë†Ø¯ Ã˜Â§Ã™â€žÃ˜Â´Ã™â€¦Ã˜Â§Ã™â€žÃ™Å Ø© Ã™Ë†Ã˜ÂªÃ™ÂÃ˜Â±Ã™Å Ã™â€š Ã™â€šÃ˜Â¨Ã˜Â§Ã˜Â¦Ã™â€ž Ã™â€¡Ã™â€ Ã˜Â§Ã™Æ’ Ã™Æ’Ã˜Â§Ã™â€ Øª Ã˜ÂªÃ˜ÂªÃ™â€¡Ã™Å Ø£ Ã™â€žÃ˜ÂºÃ˜Â²Ã™Ë† Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¯Ã™Å Ã™â€ Ø©.", type: "event" }
};

function showGlossaryPopup(event, term) {
    if (event) event.stopPropagation();
    const item = GLOSSARY[term];
    if (!item) return;
    
    let icon = 'Ã°Å¸â€œÅ’';
    let color = '#4f46e5';
    let termColor = 'var(--primary)';
    
    if (item.type === 'person') {
        if (item.gender === 'female') {
            icon = 'Ã¢â„¢â‚¬Ã¯Â¸Â'; color = '#ec4899'; termColor = '#be185d';
        } else {
            icon = 'Ã¢â„¢â€šÃ¯Â¸Â'; color = '#3b82f6'; termColor = '#1d4ed8';
        }
    } else if (item.type === 'event') {
        icon = 'Ã¢Å¡â€Ã¯Â¸Â'; color = '#10b981'; termColor = '#047857';
    } else if (item.type === 'tribe') {
        icon = 'Ã°Å¸ÂÂ¹'; color = '#7c3aed'; termColor = '#6d28d9';
    } else if (item.type === 'concept') {
        icon = 'Ã°Å¸â€™Â¡'; color = '#f59e0b'; termColor = '#b45309';
    }
    
    const termEl = document.getElementById('glossary-popup-term');
    if(termEl) termEl.innerHTML = `<span style="margin-left: 6px; font-size: 15px;">${icon}</span><span style="color:${termColor}; font-weight:800;">${term}</span>`;
    
    const defEl = document.getElementById('glossary-popup-def');
    if(defEl) defEl.textContent = item.def;
    
    const popup = document.getElementById('glossary-popup');
    if(popup) {
        popup.style.borderRightColor = color;
        popup.style.display = 'block';
    }
}

function closeGlossaryPopup() {
    const popup = document.getElementById('glossary-popup');
    if (popup) popup.style.display = 'none';
}

document.addEventListener('click', () => { closeGlossaryPopup(); });

// Ã¢â€â‚¬Ã¢â€â‚¬ MIND MAP POPUP Ã¢â€â‚¬Ã¢â€â‚¬
function openMindMap() {
    const mindmapOverlay = document.getElementById('mindmap-overlay');
    const mindmapImg = document.getElementById('mindmap-image');
    if (!mindmapOverlay || !mindmapImg) return;
    
    // Lazy loading
    if (!mindmapImg.src || mindmapImg.src.endsWith('placeholder.png')) {
        // e.g. /assets/mindmaps/sira_14.png (We just use a demo or derived from URL)
        mindmapImg.src = `assets/mindmaps/sira_${urlLesson}.png`; // Adapt according to real paths
    }
    mindmapOverlay.style.display = 'flex';
}

function closeMindMap() {
    const mindmapOverlay = document.getElementById('mindmap-overlay');
    if (mindmapOverlay) mindmapOverlay.style.display = 'none';
}

// Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ AI SUPPORT ENGINE Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
const supportEngine = {
    analyzeAndSubmit: function() {
        const queryInput = document.getElementById('support-user-query');
        const isPrivateInput = document.getElementById('support-is-private');
        const submitBtn = document.getElementById('support-submit-btn');
        const responseBox = document.getElementById('support-ai-response');
        const badgeEl = document.getElementById('support-detected-badge');
        const suggestionsEl = document.getElementById('support-rag-suggestions');
        const ticketConfEl = document.getElementById('support-ticket-confirmation');

        const text = queryInput.value.trim();
        if (!text) {
            alert('Ã˜Â§Ã™â€žØ±Ø¬Ø§Ø¡ Ã™Æ’ØªØ§Ø¨Ø© Ã˜Â§Ã™â€žÃ˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž Ã˜Â£Ã™Ë† Ã˜Â§Ã™â€žÃ˜Â§Ã˜Â³Ã˜ÂªÃ™ÂØ³Ø§Ø± Ã˜Â£Ã™Ë†Ã™â€žÃ˜Â§Ã™â€¹');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Ã˜Â¬Ã˜Â§Ã˜Â±Ã™Å  Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â­Ã™â€žÃ™Å Ã™â€ž Ã˜Â¨Ã˜Â§Ã™â€žÃ˜Â°Ã™Æ’Ø§Ø¡ Ã˜Â§Ã™â€žÃ˜Â§Ã˜ÂµÃ˜Â·Ã™â€ Ã˜Â§Ã˜Â¹Ã™Å ... Ã¢ÂÂ³</span>';
        responseBox.style.display = 'block';
        badgeEl.textContent = 'Ã°Å¸â€Â Ã˜Â¬Ã˜Â§Ã˜Â±Ã™Å  Ã˜ÂªÃ˜Â­Ã™â€žÃ™Å Ã™â€ž Ã™Ë†Ã˜ÂªÃ˜ÂµÃ™â€ Ã™Å Ã™Â Ã˜Â§Ã™â€žÃ˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž...';
        suggestionsEl.innerHTML = '';
        ticketConfEl.style.display = 'none';

        // 1. Detect Category automatically
        let category = 'Ã˜Â¹Ã˜Â§Ã™â€¦';
        if (text.match(/Ã™ÂÃ™Å Ã˜Â¯Ã™Å Ã™Ë†|Ã˜ÂªÃ˜Â·Ã˜Â¨Ã™Å Ã™â€š|Ã˜Â¨Ã˜Â·Ã™Å Ø¡|Ø®Ø·Ø£|Ã™â€žØ§ Ã™Å Ã˜Â¹Ã™â€¦Ã™â€ž|Ã™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ©|Ø´Ø§Ø´Ø©/i)) {
            category = 'Ã°Å¸â€ºÂ Ã¯Â¸Â Ã™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã˜ÂªÃ™â€šÃ™â€ Ã™Å Ø©';
        } else if (text.match(/Ã˜ÂµÃ™â€žØ§Ø©|Ã™Ë†Ã˜Â¶Ã™Ë†Ø¡|Ã™ÂÃ™â€šÃ™â€¡|Ã˜ÂµÃ™Å Ã˜Â§Ã™â€¦|Ã˜Â·Ã™â€¡Ø§Ø±Ø©|Ã˜Â¥Ã™â€¦Ã˜Â§Ã™â€¦|Ã˜Â²Ã™Æ’Ø§Ø©/i)) {
            category = 'Ã¢Å¡â€“Ã¯Â¸Â Ã˜Â§Ã™â€žÃ™ÂÃ™â€šÃ™â€¡ Ã˜Â§Ã™â€žÃ˜Â¥Ã˜Â³Ã™â€žÃ˜Â§Ã™â€¦ÙŠ';
        } else if (text.match(/Ã˜ÂªÃ˜Â¬Ã™Ë†Ã™Å Ø¯|Ã˜Â£Ã˜Â­Ã™Æ’Ã˜Â§Ã™â€¦|Ã™â€ Ã™Ë†Ã™â€ |Ã˜Â¥Ã˜Â¸Ã™â€¡Ø§Ø±|Ã˜Â¥Ã˜Â¯Ã˜ÂºÃ˜Â§Ã™â€¦|Ã™â€¦Ø®Ø±Ø¬/i)) {
            category = 'Ã°Å¸â€œâ€“ Ã˜Â£Ã˜Â­Ã™Æ’Ã˜Â§Ã™â€¦ Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â¬Ã™Ë†Ã™Å Ø¯';
        } else if (text.match(/Ã˜Â³Ã™Å Ø±Ø©|Ã˜ÂºÃ˜Â²Ã™Ë†Ø©|Ã˜Â±Ã˜Â³Ã™Ë†Ã™â€ž|Ã™â€ Ø¨ÙŠ|ØµØ­Ø§Ø¨ÙŠ/i)) {
            category = 'Ã°Å¸â€œÅ“ Ã˜Â§Ã™â€žÃ˜Â³Ã™Å Ø±Ø© Ã˜Â§Ã™â€žÃ™â€ Ã˜Â¨Ã™Ë†Ã™Å Ø©';
        }

        setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Ã˜ÂªÃ˜Â­Ã™â€žÃ™Å Ã™â€ž Ã˜Â§Ã™â€žÃ˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž Ã˜Â¨Ã™Ë†Ø§Ø³Ø·Ø© Ã˜Â§Ã™â€žÃ˜Â°Ã™Æ’Ø§Ø¡ Ã˜Â§Ã™â€žÃ˜Â§Ã˜ÂµÃ˜Â·Ã™â€ Ø§Ø¹ÙŠ âœ¨</span>';

            if (isPrivateInput.checked) {
                badgeEl.textContent = `Ã°Å¸â€â€™ Ã˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž Ø®Ø§Øµ / Ø´Ø®ØµÙŠ - ${category}`;
                suggestionsEl.innerHTML = `
                    <p style="color:var(--text-2); font-size:14px;">Ã˜ÂªÃ™â€¦ Ã˜Â§Ã™â€žÃ™â€šÃ™ÂÃ™â€ž Ã˜Â¹Ã™â€žÃ™â€° Ã˜Â³Ã˜Â¤Ã˜Â§Ã™â€žÃ™Æ’ Ã™Æ’Ã˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž Ø´Ø®ØµÙŠ/Ø®Ø§Øµ. Ã˜ÂªÃ™â€¦Øª Ã˜Â¥Ã˜Â­Ã˜Â§Ã™â€žØ© Ã˜Â§Ã™â€žÃ˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž Ã™â€¦Ø¨Ø§Ø´Ø±Ø© Ã˜Â¥Ã™â€žÃ™â€° Ø¥Ø¯Ø§Ø±Ø© Ã˜Â§Ã™â€žÃ˜Â£Ã™Æ’Ã˜Â§Ã˜Â¯Ã™Å Ã™â€¦Ã™Å Ø© Ã™â€žÃ™â€žÃ˜Â­Ã™ÂØ§Ø¸ Ã˜Â¹Ã™â€žÃ™â€° Ø®ØµÙˆØµÙŠØªÙƒ.</p>
                `;
                ticketConfEl.style.display = 'block';
            } else {
                badgeEl.textContent = `Ã°Å¸Å½Â¯ Ã˜Â§Ã™â€žÃ˜ÂªÃ˜ÂµÃ™â€ Ã™Å Ã™Â Ã˜Â§Ã™â€žÃ˜ÂªÃ™â€žÃ™â€šØ§Ø¦ÙŠ: ${category}`;
                suggestionsEl.innerHTML = `
                    <h4 style="margin: 0 0 10px 0; color:var(--text); font-size:15px;">Ã°Å¸â€™Â¡ Ø¥Ø¬Ø§Ø¨Ø© Ã™â€¦Ã™â€šØªØ±Ø­Ø© Ã™â€¦Ã™â€  Ã˜Â§Ã™â€žÃ˜Â£Ã˜Â±Ã˜Â´Ã™Å Ã™Â / Ã˜Â§Ã™â€žÃ˜ÂªÃ™â€žÃ˜Â®Ã™Å Øµ:</h4>
                    <div style="background:var(--bg); border-right:4px solid var(--primary); padding:12px; border-radius:8px; font-size:14px; color:var(--text-2); line-height:1.6; margin-bottom:12px;">
                        Ã˜Â¨Ã™â€ Ã˜Â§Ã˜Â¡Ã™â€¹ Ã˜Â¹Ã™â€žÃ™â€° Ã˜ÂªÃ™ÂÃ˜Â±Ã™Å Øº Ã˜Â§Ã™â€žÃ˜Â¯Ã˜Â±Ã™Ë†Ø³ Ã˜Â§Ã™â€žÃ™â€¦Ã˜ÂªÃ˜Â¹Ã™â€žÃ™â€šØ© Ã˜Â¨Ã™â‚¬ <strong>${category}</strong>: Ã™Å Ã˜ÂªÃ™â€¦ Ã™â€¦Ø±Ø§Ø¬Ø¹Ø© Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â³Ã˜Â£Ã™â€žØ© Ø¨Ø­Ø³Ø¨ Ã˜Â§Ã™â€žÃ˜Â´Ã˜Â±Ã™Ë†Ø· Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â°Ã™Æ’Ã™Ë†Ø±Ø© Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â´Ã˜Â±Ã˜Â­Ã˜Å’ Ã™Ë†Ø¥Ø°Ø§ Ã™Æ’Ã˜Â§Ã™â€  Ã˜Â§Ã™â€žÃ˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž Ã˜Â¯Ã™â€šÃ™Å Ã™â€šÃ˜Â§Ã™â€¹ Ã™Å Ã™â€¦Ã™Æ’Ã™â€ Ã™Æ’ Ã˜ÂªÃ˜Â£Ã™Æ’Ã™Å Ø¯ Ã˜Â¥Ã˜Â±Ã˜Â³Ã˜Â§Ã™â€žÃ™â€¡ Ã™â€žÃ™â€žØ¥Ø¯Ø§Ø±Ø©.
                    </div>
                    <div style="display:flex; gap:10px;">
                        <button onclick="alert('Ã˜Â§Ã™â€žÃ˜Â­Ã™â€¦Ø¯ Ã™â€žÃ™â€žÃ™â€¡! Ø³Ø¹Ø¯Ø§Ø¡ Ã˜Â¨Ã˜Â®Ã˜Â¯Ã™â€¦ØªÙƒ.')" style="flex:1; padding:10px; background:#dcfce7; color:#166534; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Ø¥Ø¬Ø§Ø¨Ø© Ã™Ë†Ø§Ø¶Ø­Ø© Ã°Å¸â€˜Â</button>
                        <button onclick="document.getElementById('support-ticket-confirmation').style.display='block'" style="flex:1; padding:10px; background:var(--primary-light); color:var(--primary); border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Ã˜Â¥Ã˜Â±Ã˜Â³Ã˜Â§Ã™â€ž Ã™â€žÃ™â€žØ¥Ø¯Ø§Ø±Ø© Ã°Å¸â€œÂ©</button>
                    </div>
                `;
            }
        }, 800);
    }
};

// Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ SPA TAB LOGIC Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
function switchTab(name, btn) {

    
    document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
    document.querySelectorAll('.bottom-nav .nav-btn').forEach(b=>b.classList.remove('active'));
    
    const panel = document.getElementById('tab-'+name);
    if(panel) panel.classList.add('active');
    
    if (btn) {
        btn.classList.add('active');
    } else {
        const targetBtn = document.querySelector(`.nav-btn[onclick*="switchTab('${name}'"]`);
        if(targetBtn) targetBtn.classList.add('active');
    }
    
    if(name === 'journey') { if(typeof renderJourneyTimeline === 'function') renderJourneyTimeline(); }
    if(name === 'home') {
        renderHomeProgress();
    }
    
    if(name === 'search') {
        setTimeout(() => document.getElementById('search-input').focus(), 100);
    }
    
    if (name === 'practice') {
        // Always hide empty state when entering practice, let quizEngine handle questions loading
        const emptyState = document.getElementById('practice-empty-state');
        if (emptyState) emptyState.style.display = 'none';
        
        if (!quizEngine.questions || quizEngine.questions.length === 0) {
            document.getElementById('practice-loading').style.display = 'block';
        }
    }
}

// Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ PROGRESS LOGIC Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
function markLessonOpened(subject, lessonNum) {
    try {
        let opened = JSON.parse(localStorage.getItem('openedLessons') || '{}');
        const key = `${subject}_${lessonNum}`;
        opened[key] = true;
        localStorage.setItem('openedLessons', JSON.stringify(opened));
        
        // Also track recent
        let recent = JSON.parse(localStorage.getItem('recentLessons') || '[]');
        recent = recent.filter(r => r.key !== key);
        recent.unshift({ key, subject, lessonNum, time: Date.now() });
        if(recent.length > 5) recent.pop();
        localStorage.setItem('recentLessons', JSON.stringify(recent));
    } catch(e){}
}

function renderHomeProgress() {
    let opened = {};
    let recent = [];
    try {
        opened = JSON.parse(localStorage.getItem('openedLessons') || '{}');
        recent = JSON.parse(localStorage.getItem('recentLessons') || '[]');
    } catch(e){}

    const totalLessons = DB.length;
    const openedCount = Object.keys(opened).length;
    let percentage = 0;
    if (totalLessons > 0) {
        percentage = Math.round((openedCount / totalLessons) * 100);
    }

    const circle = document.getElementById('progress-circle');
    const text = document.getElementById('progress-text');
    const subtitle = document.getElementById('progress-subtitle');
    
    if (circle) circle.style.strokeDasharray = `${percentage}, 100`;
    if (text) text.textContent = `${percentage}%`;
    if (subtitle) subtitle.textContent = `${openedCount} / ${totalLessons} Ø¯Ø±Ø³`;

    const recentContainer = document.getElementById('recent-lessons-container');
    if (recentContainer) {
        if (recent.length === 0) {
            recentContainer.innerHTML = '<p style="color:var(--text-3); font-size:14px;">Ã™â€žÃ™â€¦ Ã˜ÂªÃ™ÂØªØ­ Ã˜Â£Ã™Å  Ø¯Ø±Ø³ Ø¨Ø¹Ø¯.</p>';
        } else {
            recentContainer.innerHTML = '';
            recent.forEach(r => {
                const lessonObj = DB.find(l => l.subject === r.subject && l.lessonNum == r.lessonNum);
                if (lessonObj) {
                    const btn = document.createElement('div');
                    btn.style.padding = '12px';
                    btn.style.background = 'var(--surface)';
                    btn.style.border = '1px solid var(--border-color)';
                    btn.style.borderRadius = '12px';
                    btn.style.marginBottom = '8px';
                    btn.style.cursor = 'pointer';
                    btn.style.display = 'flex';
                    btn.style.alignItems = 'center';
                    btn.style.gap = '12px';
                    btn.innerHTML = `<span style="font-size:20px;">Ã°Å¸â€œËœ</span> <div><h4 style="margin:0; font-size:15px;">${lessonObj.title}</h4><span style="font-size:12px; color:var(--text-2);">${lessonObj.subjectLabel}</span></div>`;
                    btn.onclick = () => {
                        openLesson(lessonObj);
                        switchTab('reader');
                    };
                    recentContainer.appendChild(btn);
                }
            });
        }
    }
}

// Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ SEARCH LOGIC Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
function buildIndex() {
    const stop = new Set(["Ã™ÂÃ™Å ","Ã™â€¦Ã™â€ ","Ã˜Â¹Ã™â€žÃ™â€°","Ã˜Â¥Ã™â€žÃ™â€°","Ã˜Â¹Ã™â€ ","Ã™â€¡Ø°Ø§","Ã™â€¡Ã˜Â°Ã™â€¡","Ã˜Â§Ã™â€žÃ˜ÂªÃ™Å ","Ã˜Â§Ã™â€žÃ˜Â°Ã™Å ","Ã˜Â£Ã™â€ ","Ã˜Â¥Ã™â€ ","Ã™â€žØ§","Ã™â€¦Ø§","Ã™â€¦Ø¹","Ã™Æ’Ã˜Â§Ã™â€ ","Ã™Æ’Ã˜Â§Ã™â€ Øª","Ã˜Â«Ã™â€¦","Ã˜Â£Ã™Ë†","Ã˜Â£Ã™â€¦","Ã™Æ’Ã™â€ž","Ã™Å Ã™Ë†Ã™â€¦","Ø¨Ø¹Ø¯","Ã™â€šÃ˜Â¨Ã™â€ž","Ã˜Â¹Ã™â€ Ø¯","Ã™â€¡Ã™Ë†","Ã™â€¡Ã™Å ","Ã™Ë†Ã™â€šØ¯","Ã™â€šØ¯","Ã™ÂÃ™â€šØ¯","Ã™Ë†Ã™â€¡Ã™Ë†","Ã™Ë†Ã™â€¡Ã™Å ","Ã™Ë†Ã™Æ’Ã˜Â§Ã™â€ "]);
    const seen = new Set();
    DB.forEach(item => {
        ((item.full_text||'')+' '+(item.blocks_search_text||'')).split(/[\sÃ˜Å’.Ã˜Å¸!():Ã˜â€º]+/).forEach(w=>{
            const c=w.trim();
            if(c.length>=3&&c.length<=10&&!stop.has(c)&&!seen.has(c)){
                seen.add(c);
                wordIndex.push({text:c,subjectLabel:item.subjectLabel,cls:'badge-'+item.subject});
            }
        });
    });
}

function strip(html){return new DOMParser().parseFromString(html,'text/html').body.textContent||'';}
function esc(str){return str.replace(/[.*+?^${}()|[\]\\]/g,'\$&');}
function hl(t,q){const reg=new RegExp(`(${esc(q)})`,'gi');return t.replace(reg,'<mark>$1</mark>');}

function getQ(q){
    const words = q.split(/\s+/).filter(w => w.length > 0);
    return words;
}

const si = document.getElementById('search-input');
const cb = document.getElementById('clear-btn');
const ac = document.getElementById('autocomplete');

if (si) {
    si.addEventListener('input', () => {
        const q=si.value.trim();
        cb.style.display=q?'block':'none';
        if(q.length>=2){showAc(q);doSearch(q);} else{ac.style.display='none';resetSearch();}
    });
    
    si.addEventListener('keydown',(e)=>{
        if (e.key === 'Enter') {
            const q=si.value.trim();
            if(q.length>=2){
                ac.style.display='none';
                doSearch(q);
                si.blur();
            }
        }
    });
    
    cb.addEventListener('click',()=>{
        si.value='';
        cb.style.display='none';
        ac.style.display='none';
        resetSearch();
        si.focus();
    });
    
    document.addEventListener('click',e=>{
        if(ac && !e.target.closest('.search-wrap')) ac.style.display='none';
    });
}

function showAc(q) {
    const ql=q.toLowerCase();
    const matches=wordIndex.filter(w=>w.text.toLowerCase().includes(ql)).slice(0,5);
    if(!matches.length){ac.style.display='none';return;}
    ac.innerHTML=matches.map(m=>`<div class="autocomplete-item" onclick="document.getElementById('search-input').value='${m.text}';document.getElementById('autocomplete').style.display='none';document.getElementById('clear-btn').style.display='block';doSearch('${m.text}')"><span>${hl(m.text,q)}</span><span class="badge ${m.cls}">${m.subjectLabel}</span></div>`).join('');
    ac.style.display='block';
}

function doSearch(queryText) {
    if(ac) ac.style.display = 'none';
    const queries = getQ(queryText);
    const results = [];
    const resContainer = document.getElementById('search-results');
    
    DB.forEach(item => {
        if (item.thematic_blocks && item.thematic_blocks.length) {
            item.thematic_blocks.forEach(b => {
                let sc = 0;
                let matchTitle = false;
                queries.forEach(q2 => {
                    const titleLower = b.title.toLowerCase();
                    const textLower = (b.search_text || '').toLowerCase();
                    if (titleLower.includes(q2)) { sc += 2000; matchTitle = true; }
                    sc += (textLower.match(new RegExp(esc(q2),'g'))||[]).length * 10;
                });
                if(sc > 0) results.push({item, block:b, score:sc, matchTitle});
            });
        }
    });
    
    results.sort((a,b) => b.score - a.score);
    const top = results.slice(0,30);
    
    if(!top.length) {
        resContainer.innerHTML = `<div class="empty-state"><p style="color:var(--text-3);">Ã™â€žØ§ Ã˜ÂªÃ™Ë†Ø¬Ø¯ Ã™â€ ØªØ§Ø¦Ø¬</p></div>`;
        return;
    }
    
    let html = '';
    top.forEach(r => {
        const item = r.item;
        const b = r.block;
        html += `<div class="result-card" onclick="openSearchResult('${item.subject}', ${item.lessonNum}, ${b.start_seconds})">
            <div style="padding:14px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px; align-items:flex-start;">
                    <h4 style="margin:0; font-size:14.5px; color:var(--text); line-height:1.4;">${hl(b.title, queries[0])}</h4>
                    <span class="badge badge-${item.subject}" style="flex-shrink:0; margin-right:10px;">${item.subjectLabel} ${item.lessonNum}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:12px; color:var(--primary); font-weight:600; background:var(--primary-light, rgba(79, 70, 229, 0.1)); padding:4px 8px; border-radius:6px;">
                        Ã¢ÂÂ± ${formatSeconds(b.start_seconds)}
                    </div>
                </div>
            </div>
        </div>`;
    });
    resContainer.innerHTML = html;
}

function resetSearch() {
    const res = document.getElementById('search-results');
    if(res) res.innerHTML = `<div class="empty-state"><p style="color:var(--text-3);">Ã˜Â§Ã™Æ’ØªØ¨ Ã™Æ’Ã™â€žÃ™â€¦Ø© Ã™â€žÃ™â€žØ¨Ø­Ø«</p></div>`;
}

function openSearchResult(subject, lessonNum, startTime) {
    if (startTime !== null && startTime !== undefined) startTime = parseInt(startTime);
    const lesson = DB.find(l => l.subject.toLowerCase() === subject.toLowerCase() && parseInt(l.lessonNum) === parseInt(lessonNum));
    if(lesson) {
        if (startTime !== null && !isNaN(startTime)) pendingSeekTime = startTime;
        openLesson(lesson);
        switchTab('reader');
        
        const idx = thematicData.findIndex(t => t.startTime <= startTime && t.endTime > startTime);
        if(idx !== -1) {
            switchThemeTab(idx, false);
        }
    }
}
function formatSeconds(s) { const m = Math.floor(s/60); const ss = Math.floor(s%60); return m + ":" + (ss<10?"0":"")+ss; }

function setSyllabusMode(mode) {
    syllabusMode = mode;
    const gridBtn = document.getElementById('toggle-grid-btn');
    const listBtn = document.getElementById('toggle-list-btn');
    const subjectsList = document.getElementById('subjects-list');
    
    if (mode === 'grid') {
        gridBtn.style.background = 'var(--primary)';
        gridBtn.style.color = 'white';
        listBtn.style.background = 'transparent';
        listBtn.style.color = 'var(--text-2)';
        if (subjectsList) subjectsList.classList.add('grid-view-mobile');
    } else {
        listBtn.style.background = 'var(--primary)';
        listBtn.style.color = 'white';
        gridBtn.style.background = 'transparent';
        gridBtn.style.color = 'var(--text-2)';
        if (subjectsList) subjectsList.classList.remove('grid-view-mobile');
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
        if (currentActiveSubjectData) {
            openSubjectDetail(currentActiveSubjectData, currentActiveSubjectColor);
        } else {
            buildSyllabusTab(DB);
        }
    }
    
    if (syllabusCompletion[key]) {
        playCompletionSound();
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


// --- KARAOKE ENGINE ---
let lastUserScrollTime = 0;
let isProgrammaticScroll = false;

let isTouching = false;
window.addEventListener('scroll', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });
window.addEventListener('touchstart', () => { 
    if (!isProgrammaticScroll) {
        isTouching = true;
        lastUserScrollTime = Date.now(); 
    }
}, { passive: true, capture: true });
window.addEventListener('touchend', () => { 
    isTouching = false;
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });
window.addEventListener('wheel', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });

setInterval(() => {
    if (!player || !player.getPlayerState || player.getPlayerState() !== YT.PlayerState.PLAYING) return;
    if (isSeekingTab) return;
    
    let currentTime = player.getCurrentTime();
    updateDashboardProgress();
    
    // --- SMART AUTO TAB SWITCHING ---
    if (thematicData && thematicData[currentTabIndex]) {
        let tabStart = thematicData[currentTabIndex].startTime;
        let tabEnd = thematicData[currentTabIndex].endTime;
        
        if (currentTime >= tabEnd && currentTabIndex < thematicData.length - 1) {
            // Video moved past current tab, find correct tab
            let correctIndex = thematicData.findIndex(t => currentTime >= t.startTime && currentTime < t.endTime);
            if (correctIndex !== -1 && correctIndex !== currentTabIndex) {
                switchThemeTab(correctIndex, false);
                return; // Let next tick handle highlighting
            }
        } else if (currentTime < tabStart && currentTabIndex > 0) {
            // Video scrubbed backwards
            let correctIndex = thematicData.findIndex(t => currentTime >= t.startTime && currentTime < t.endTime);
            if (correctIndex !== -1 && correctIndex !== currentTabIndex) {
                switchThemeTab(correctIndex, false);
                return;
            }
        }
    }
    
    const segments = document.querySelectorAll('.karaoke-segment');
    if (segments.length === 0) return;
    
    let activeStart = -1;
    let nextStart = 999999;
    
    for (let i = 0; i < segments.length; i++) {
        let start = parseFloat(segments[i].getAttribute('data-start'));
        if (isNaN(start)) continue;
        
        if (start <= currentTime) {
            activeStart = start;
        } else {
            nextStart = start;
            break;
        }
    }
    
    let firstActiveSeg = null;
    
    segments.forEach(seg => {
        let start = parseFloat(seg.getAttribute('data-start'));
        if (start === activeStart && currentTime < nextStart) {
            if (!seg.classList.contains('active-karaoke')) {
                seg.classList.add('active-karaoke');
            }
            if (!firstActiveSeg) firstActiveSeg = seg;
        } else {
            seg.classList.remove('active-karaoke');
        }
    });
    
    if (firstActiveSeg) {
        // Don't auto-scroll if: (1) user just scrolled manually within 8s, (2) Zen Mode is active,
        // or (3) user is near the bottom of page (near the validation button)
        const scrolledNearBottom = (window.scrollY + window.innerHeight) >= (document.documentElement.scrollHeight - 150);
        const isZenMode = document.body.classList.contains('zen-mode');
        if (Date.now() - lastUserScrollTime > 8000 && !isTouching && !isZenMode && !scrolledNearBottom) {
            const rect = firstActiveSeg.getBoundingClientRect();
            
            // Calculate sticky headers total height
            const stickyContainer = document.getElementById('sticky-header-container');
            let offsetHeight = 0;
            
            if (stickyContainer) {
                const style = window.getComputedStyle(stickyContainer);
                if (style.position === 'sticky' || style.position === 'fixed') {
                    offsetHeight += stickyContainer.offsetHeight;
                }
            }
            
            // Add a padding of 40px so the text is not squeezed against the menu
            const targetOffset = offsetHeight + 40;
            
            let needsScroll = false;
            
            if (readerSettings.scrollMode === 'teleprompter') {
                // Teleprompter: Must always be EXACTLY at targetOffset
                // Increase tolerance to 15px to avoid jitter with large fonts
                if (Math.abs(rect.top - targetOffset) > 15) {
                    needsScroll = true;
                }
            } else {
                // Zone: Only scroll if too high (hidden under header) or too low
                if (rect.top < targetOffset || rect.top > window.innerHeight * 0.70) {
                    needsScroll = true;
                }
            }
            
            if (needsScroll) {
                isProgrammaticScroll = true;
                
                // Calculate absolute scroll position
                const absoluteTop = window.scrollY + rect.top;
                
                window.scrollTo({
                    top: absoluteTop - targetOffset,
                    behavior: 'smooth'
                });
                
                setTimeout(() => { isProgrammaticScroll = false; }, 1200);
            }
        }
    }
}, 300);
// --- END KARAOKE ENGINE ---

// --- SETTINGS STATE ---
let readerSettings = {
    scrollMode: 'zone',
    focusMode: false,
    spacingAere: false,
    fontFamily: "'Tajawal', sans-serif"
};

function loadSettings() {
    try {
        let saved = localStorage.getItem('academie_reader_settings');
        if (saved) {
            let parsed = JSON.parse(saved);
            readerSettings = { ...readerSettings, ...parsed };
            if (parsed.spacingAere !== undefined) readerSettings.spacingAere = parsed.spacingAere;
            if (parsed.fontFamily !== undefined) readerSettings.fontFamily = parsed.fontFamily;
        }
    } catch (e) { console.error(e); }
    
    // Apply UI
    const radios = document.getElementsByName('scrollMode');
    radios.forEach(r => {
        if (r.value === readerSettings.scrollMode) r.checked = true;
        r.addEventListener('change', (e) => {
            readerSettings.scrollMode = e.target.value;
            saveSettings();
        });
    });

    const focusToggle = document.getElementById('focus-mode-toggle');
    if (focusToggle) {
        focusToggle.checked = readerSettings.focusMode;
        focusToggle.addEventListener('change', (e) => {
            readerSettings.focusMode = e.target.checked;
            saveSettings();
            applyFocusMode();
        });
    }

    const spacingToggle = document.getElementById('spacing-toggle');
    if (spacingToggle) {
        spacingToggle.checked = readerSettings.spacingAere;
        spacingToggle.addEventListener('change', (e) => {
            readerSettings.spacingAere = e.target.checked;
            saveSettings();
            applySpacing();
        });
    }

    applyFocusMode();
    applySpacing();
    applyFontFamily();
    initFontButtons();
}

function saveSettings() {
    localStorage.setItem('academie_reader_settings', JSON.stringify(readerSettings));
}

function applyFocusMode() {
    const content = document.getElementById('reader-content');
    if (content) {
        if (readerSettings.focusMode) {
            content.classList.add('focus-mode-active');
        } else {
            content.classList.remove('focus-mode-active');
        }
    }
}

// --- SETTINGS MODAL LOGIC ---
document.addEventListener('DOMContentLoaded', () => {
    const btnSettings = document.getElementById('btn-settings-toggle');
    const settingsSheet = document.getElementById('settings-sheet');
    const settingsOverlay = document.getElementById('settings-overlay');
    const closeSettingsBtn = document.getElementById('close-settings-btn');
    
    function openSettings() {
        settingsSheet.classList.add('open');
        settingsOverlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
    
    function closeSettings() {
        settingsSheet.classList.remove('open');
        settingsOverlay.classList.remove('show');
        document.body.style.overflow = '';
    }
    
    if (btnSettings) btnSettings.addEventListener('click', openSettings);
    if (closeSettingsBtn) closeSettingsBtn.addEventListener('click', closeSettings);
    if (settingsOverlay) settingsOverlay.addEventListener('click', closeSettings);
    
    loadSettings();
});

document.addEventListener('DOMContentLoaded', () => {
    const prevBtn = document.getElementById('prev-theme-btn');
    const nextBtn = document.getElementById('next-theme-btn');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentTabIndex > 0) switchThemeTab(currentTabIndex - 1, true);
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (thematicData && currentTabIndex < thematicData.length - 1) {
                switchThemeTab(currentTabIndex + 1, true);
            }
        });
    }
});




document.addEventListener('DOMContentLoaded', () => {
    const stickyToggleBtn = document.getElementById('btn-sticky-toggle');
    const stickyContainer = document.getElementById('sticky-header-container');
    const videoWrapper = document.getElementById('video-wrapper');
    
    if (stickyToggleBtn && stickyContainer && videoWrapper) {
        stickyToggleBtn.addEventListener('click', () => {
            if (videoWrapper.style.display === 'none') {
                videoWrapper.style.display = 'flex';
                stickyToggleBtn.style.background = 'var(--surface)';
                stickyToggleBtn.style.color = 'var(--text)';
                stickyToggleBtn.setAttribute('title', 'DÃƒÂ©sÃƒÂ©pingler la vidÃƒÂ©o');
            } else {
                videoWrapper.style.display = 'none';
                stickyToggleBtn.style.background = 'var(--primary)';
                stickyToggleBtn.style.color = 'white';
                stickyToggleBtn.setAttribute('title', 'Ãƒâ€°pingler la vidÃƒÂ©o');
            }
        });
    }
});

function applySpacing() {
    const rc = document.getElementById('reader-content');
    if (rc) {
        if (readerSettings.spacingAere) {
            rc.classList.add('spacing-aere');
        } else {
            rc.classList.remove('spacing-aere');
        }
    }
}

function applyFontFamily() {
    document.documentElement.style.setProperty('--main-font', readerSettings.fontFamily);
    
    // Update active button state
    document.querySelectorAll('.font-select-btn').forEach(btn => {
        if (btn.getAttribute('data-font') === readerSettings.fontFamily) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function initFontButtons() {
    document.querySelectorAll('.font-select-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            readerSettings.fontFamily = e.target.getAttribute('data-font');
            saveSettings();
            applyFontFamily();
        });
    });
}

let currentPlaybackRate = 1;
function updateSpeedUI() {
    const quickSpeedBtn = document.getElementById('btn-speed-toggle');
    if (quickSpeedBtn) {
        quickSpeedBtn.textContent = currentPlaybackRate + 'x';
    }
    document.querySelectorAll('.speed-select-btn').forEach(b => {
        if (parseFloat(b.getAttribute('data-speed')) === currentPlaybackRate) {
            b.classList.add('active');
        } else {
            b.classList.remove('active');
        }
    });
}

function setPlaybackSpeed(rate) {
    currentPlaybackRate = rate;
    updateSpeedUI();
    if (player && typeof player.setPlaybackRate === 'function') {
        player.setPlaybackRate(currentPlaybackRate);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const speedBtns = document.querySelectorAll('.speed-select-btn');
    speedBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            setPlaybackSpeed(parseFloat(e.target.getAttribute('data-speed')));
        });
    });
    
    const quickSpeedBtn = document.getElementById('btn-speed-toggle');
    if (quickSpeedBtn) {
        quickSpeedBtn.addEventListener('click', () => {
            let newRate = 1;
            if (currentPlaybackRate === 1) newRate = 1.25;
            else if (currentPlaybackRate === 1.25) newRate = 1.5;
            else if (currentPlaybackRate === 1.5) newRate = 2;
            else if (currentPlaybackRate === 2) newRate = 0.75;
            else newRate = 1;
            setPlaybackSpeed(newRate);
        });
    }
    
    updateSpeedUI();
});

function startLessonFromChapter(subject, lessonNum, startSec) {
    const found = DB.find(t => t.lessonNum == lessonNum && t.subject === subject);
    if (!found) return;
    closeLessonPreview();
    switchTab('reader');
    loadLesson(lessonNum, subject, startSec);
}

function openLessonPreview(l) {
    const sheet = document.getElementById('lesson-preview-sheet');
    const overlay = document.getElementById('lesson-preview-overlay');
    const title = document.getElementById('lesson-preview-title');
    const list = document.getElementById('lesson-preview-list');
    const startBtn = document.getElementById('start-reading-btn');

    title.textContent = 'Ã˜Â§Ã™â€žØ¯Ø±Ø³ ' + l.lessonNum + ' - ' + (l.title || l.subjectLabel || l.subject);

    let html = '';
    let firstUnreadIdx = 0;
    let totalCompleted = 0;
    
    if (l.thematic_blocks && l.thematic_blocks.length > 0) {
        firstUnreadIdx = l.thematic_blocks.findIndex((b, idx) => {
            return !syllabusCompletion[l.subject + '_' + l.lessonNum + '_' + idx];
        });
        if (firstUnreadIdx === -1) firstUnreadIdx = 0;
        
        l.thematic_blocks.forEach((b, idx) => {
            const key = l.subject + '_' + l.lessonNum + '_' + idx;
            const isComp = !!syllabusCompletion[key];
            if (isComp) totalCompleted++;
            
            html += `<div class="preview-chapter-item">
                <div class="preview-checkbox ${isComp ? 'checked' : ''}" onclick="togglePreviewChapter(event, '${l.subject}', ${l.lessonNum}, ${idx}, this.parentElement)">${isComp ? 'Ã¢Å“â€œ' : ''}</div>
                <div class="preview-chapter-info" style="margin-right: 12px; text-align: right; cursor: pointer; flex: 1;" onclick="startLessonFromChapter('${l.subject}', ${l.lessonNum}, ${b.start_seconds})">
                    <div class="preview-chapter-title" style="transition: color 0.2s;">${idx + 1}. ${b.title}</div>
                </div>
            </div>`;
        });
    } else {
        html = '<div style="text-align:center; color:var(--text-2); padding: 20px;">Ã™â€žØ§ Ã˜ÂªÃ™Ë†Ø¬Ø¯ Ã™â€¦Ã˜Â­Ã˜Â§Ã™Ë†Ø± Ã™â€¦ØªØ§Ø­Ø©</div>';
    }
    list.innerHTML = html;

    if (l.thematic_blocks && l.thematic_blocks.length > 0) {
        if (totalCompleted === 0) {
            startBtn.innerHTML = `Ã°Å¸â€œâ€“ Ø§Ø¨Ø¯Ø£ Ã˜Â§Ã™â€žÃ™â€šØ±Ø§Ø¡Ø©`;
        } else if (totalCompleted === l.thematic_blocks.length) {
            startBtn.innerHTML = `Ã°Å¸â€â€ž Ø£Ø¹Ø¯ Ã™â€šØ±Ø§Ø¡Ø© Ã˜Â§Ã™â€žØ¯Ø±Ø³`;
        } else {
            startBtn.innerHTML = `Ã¢â€“Â¶Ã¯Â¸Â Ã˜Â§Ã˜Â³Ã˜ÂªÃ˜Â¦Ã™â€ Ã˜Â§Ã™Â (Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â­Ã™Ë†Ø± ${firstUnreadIdx + 1})`;
        }
    } else {
        startBtn.innerHTML = `Ã°Å¸â€œâ€“ Ø§Ø¨Ø¯Ø£ Ã˜Â§Ã™â€žÃ™â€šØ±Ø§Ø¡Ø©`;
    }

    startBtn.onclick = () => {
        closeLessonPreview();
        switchTab('reader');
        let startSec = 0;
        if (l.thematic_blocks && l.thematic_blocks.length > 0) {
            startSec = l.thematic_blocks[firstUnreadIdx].start_seconds;
        }
        loadLesson(l.lessonNum, l.subject, startSec);
    };

    sheet.classList.add('open');
    overlay.classList.add('show');
}

function closeLessonPreview() {
    document.getElementById('lesson-preview-sheet').classList.remove('open');
    document.getElementById('lesson-preview-overlay').classList.remove('show');
}

function togglePreviewChapter(e, subject, lessonNum, chapterIdx, el) {
    if (e) e.stopPropagation();
    const key = subject + '_' + lessonNum + '_' + chapterIdx;
    const isComp = !syllabusCompletion[key];
    syllabusCompletion[key] = isComp;
    localStorage.setItem('academy_syllabus_completions', JSON.stringify(syllabusCompletion));

    updateGlobalProgress();
    if (currentActiveSubjectData) {
        openSubjectDetail(currentActiveSubjectData, currentActiveSubjectColor);
    } else {
        buildSyllabusTab(DB);
    }

    const cb = el.querySelector('.preview-checkbox');
    if (isComp) {
        cb.classList.add('checked');
        cb.textContent = 'Ã¢Å“â€œ';
        playCompletionSound();
    } else {
        cb.classList.remove('checked');
        cb.textContent = '';
    }
}

document.getElementById('close-preview-btn').onclick = closeLessonPreview;
document.getElementById('lesson-preview-overlay').onclick = closeLessonPreview;


// Segmented Control Logic for Reading/Video Mode
document.addEventListener('DOMContentLoaded', () => {
    const btnSegVideo = document.getElementById('btn-seg-video');
    const btnSegReading = document.getElementById('btn-seg-reading');
    
    window.updateSegmentUI = function() {
        if (typeof isReadingMode === 'undefined') return;
        
        if (btnSegReading && btnSegVideo) {
            if (isReadingMode) {
                btnSegReading.style.background = 'var(--primary)';
                btnSegReading.style.color = 'white';
                btnSegVideo.style.background = 'transparent';
                btnSegVideo.style.color = 'var(--text-secondary)';
            } else {
                btnSegVideo.style.background = 'var(--primary)';
                btnSegVideo.style.color = 'white';
                btnSegReading.style.background = 'transparent';
                btnSegReading.style.color = 'var(--text-secondary)';
            }
        }
        
        // Hide/Show Sticky Pin and Video Speed
        const btnSticky = document.getElementById('btn-sticky-toggle');
        const btnSpeed = document.getElementById('btn-speed-toggle');
        const progTracker = document.getElementById('progress-tracker-dots');
        
        if (btnSticky) btnSticky.style.display = isReadingMode ? 'none' : 'inline-block';
        if (btnSpeed) btnSpeed.style.display = isReadingMode ? 'none' : 'inline-block';
        if (progTracker) progTracker.style.visibility = isReadingMode ? 'hidden' : 'visible'; // Keep space but hide dots
    }
    
    if (btnSegVideo && btnSegReading) {
        btnSegVideo.addEventListener('click', () => {
            if (!isReadingMode) return;
            isReadingMode = false;
            updateSegmentUI();
            if (typeof currentLessonData !== 'undefined' && currentLessonData) {
                prepareThematicData(currentLessonData);
                renderTabs();
                switchThemeTab(typeof currentTabIndex !== 'undefined' ? currentTabIndex : 0, !isReadingMode);
            }
        });
        
        btnSegReading.addEventListener('click', () => {
            if (isReadingMode) return;
            isReadingMode = true;
            updateSegmentUI();
            if (typeof currentLessonData !== 'undefined' && currentLessonData) {
                prepareThematicData(currentLessonData);
                renderTabs();
                switchThemeTab(typeof currentTabIndex !== 'undefined' ? currentTabIndex : 0, !isReadingMode);
            }
        });
        
        // Initialize
        updateSegmentUI();
    }
});

// Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ QUIZ ENGINE (PRACTICE TAB) Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
// ==========================================
// SUPPORT CHAT FUNNEL LOGIC
// ==========================================


/* quizEngine removed (moved to quiz.js) */
const supportFlow = {
    category: '',
    subcategory: '',
    message: '',

    selectCategory: function(cat) {
        this.category = cat;
        this.addMessage(cat, 'user');
        document.getElementById('support-step-1-options').style.display = 'none';
        
        setTimeout(() => {
            let subText = '';
            let subBtns = '';
            if(cat === 'Ã˜ÂªÃ™â€šÃ™â€ Ã™Å Ø©') {
                subText = 'Ã™â€¡Ã™â€ž Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã™â€¦Ã˜ÂªÃ˜Â¹Ã™â€žÃ™â€šØ© Ã˜Â¨Ã™â‚¬:';
                subBtns = `
                    <button onclick="supportFlow.selectSubcategory('Ã˜Â§Ã™â€žÃ™ÂÃ™Å Ã˜Â¯Ã™Å Ã™Ë† Ã™â€žØ§ Ã™Å Ã˜Â¹Ã™â€¦Ã™â€ž')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ã˜Â§Ã™â€žÃ™ÂÃ™Å Ã˜Â¯Ã™Å Ã™Ë† Ã™â€žØ§ Ã™Å Ã˜Â¹Ã™â€¦Ã™â€ž</button>
                    <button onclick="supportFlow.selectSubcategory('Ã™â€žØ§ Ã™Å Ã™Ë†Ø¬Ø¯ Ã˜ÂµÃ™Ë†Øª')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ã™â€žØ§ Ã™Å Ã™Ë†Ø¬Ø¯ Ã˜ÂµÃ™Ë†Øª</button>
                    <button onclick="supportFlow.selectSubcategory('Ã™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â·Ã˜Â¨Ã™Å Ã™â€š')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ã™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â·Ã˜Â¨Ã™Å Ã™â€š</button>
                `;
            } else if(cat === 'Ã˜Â¥Ã˜Â¯Ã˜Â§Ã˜Â±Ã™Å Ø©') {
                subText = 'Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â±Ã˜Â¬Ã™Ë† Ã˜ÂªÃ˜Â­Ã˜Â¯Ã™Å Ø¯ Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ©:';
                subBtns = `
                    <button onclick="supportFlow.selectSubcategory('Ã˜ÂªÃ˜Â¬Ã˜Â¯Ã™Å Ø¯ Ã˜Â§Ã™â€žØ§Ø´ØªØ±Ø§Ùƒ')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ã˜ÂªÃ˜Â¬Ã˜Â¯Ã™Å Ø¯ Ã˜Â§Ã™â€žØ§Ø´ØªØ±Ø§Ùƒ</button>
                    <button onclick="supportFlow.selectSubcategory('Ã™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â¯Ã™ÂØ¹')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ã™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â¯Ã™ÂØ¹</button>
                `;
            } else {
                subText = 'Ã™â€¡Ã™â€ž Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã™ÂÃ™Å :';
                subBtns = `
                    <button onclick="supportFlow.selectSubcategory('Ã™ÂÃ™â€¡Ã™â€¦ Ã˜Â§Ã™â€žØ¯Ø±Ø³')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ã™ÂÃ™â€¡Ã™â€¦ Ã˜Â§Ã™â€žØ¯Ø±Ø³</button>
                    <button onclick="supportFlow.selectSubcategory('Ã˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž Ã˜Â­Ã™Ë†Ã™â€ž Ã˜Â§Ã™â€žØ§Ø®ØªØ¨Ø§Ø±')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ã˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž Ã˜Â­Ã™Ë†Ã™â€ž Ã˜Â§Ã™â€žØ§Ø®ØªØ¨Ø§Ø±</button>
                `;
            }
            
            this.addMessage(subText, 'bot');
            const optsId = 'subopts-' + Date.now();
            const optsHtml = `<div id="${optsId}" style="display: flex; flex-wrap: wrap; gap: 8px; align-self: flex-start; max-width: 85%;">${subBtns}</div>`;
            document.getElementById('support-chat-history').insertAdjacentHTML('beforeend', optsHtml);
            this.currentOptsId = optsId;
            this.scrollToBottom();
        }, 500);
    },

    selectSubcategory: function(sub) {
        this.subcategory = sub;
        this.addMessage(sub, 'user');
        if(this.currentOptsId) {
            document.getElementById(this.currentOptsId).style.display = 'none';
        }
        
        setTimeout(() => {
            let tip = '';
            if (sub === 'Ã˜Â§Ã™â€žÃ™ÂÃ™Å Ã˜Â¯Ã™Å Ã™Ë† Ã™â€žØ§ Ã™Å Ã˜Â¹Ã™â€¦Ã™â€ž' || sub === 'Ã™â€žØ§ Ã™Å Ã™Ë†Ø¬Ø¯ Ã˜ÂµÃ™Ë†Øª') {
                tip = 'Ã°Å¸â€™Â¡ Ã™â€ Ã˜ÂµÃ™Å Ø­Ø© Ã˜Â³Ã˜Â±Ã™Å Ø¹Ø©: 90% Ã™â€¦Ã™â€  Ã™â€¦Ã˜Â´Ã˜Â§Ã™Æ’Ã™â€ž Ã˜Â§Ã™â€žÃ™ÂÃ™Å Ã˜Â¯Ã™Å Ã™Ë† Ã˜ÂªÃ™ÂÃ˜Â­Ã™â€ž Ã˜Â¨Ã™â€¦Ø¬Ø±Ø¯ Ã˜ÂªÃ˜Â­Ã˜Â¯Ã™Å Ø« Ã˜Â§Ã™â€žÃ˜ÂµÃ™ÂØ­Ø© Ã˜Â£Ã™Ë† Ã™â€¦Ø³Ø­ Ã˜Â°Ã˜Â§Ã™Æ’Ø±Ø© Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â®Ã˜Â²Ã™Å Ã™â€  Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â¤Ã™â€šØª (Cache). Ã™â€¡Ã™â€ž Ã˜ÂªÃ˜Â±Ã™Å Ø¯ ØªØ¬Ø±Ø¨Ø© Ã˜Â°Ã™â€žÙƒØŸ<br><br>';
            } else if (sub === 'Ã™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜Â¯Ã™ÂØ¹' || sub === 'Ã˜ÂªÃ˜Â¬Ã˜Â¯Ã™Å Ø¯ Ã˜Â§Ã™â€žØ§Ø´ØªØ±Ø§Ùƒ') {
                tip = 'Ã°Å¸â€™Â¡ Ã™â€¦Ã™â€žØ§Ø­Ø¸Ø©: Ã˜ÂªÃ™ÂÃ˜Â¹Ã™Å Ã™â€ž Ã˜Â§Ã™â€žÃ˜Â§Ã˜Â´Ã˜ÂªÃ˜Â±Ã˜Â§Ã™Æ’Ø§Øª Ã™â€šØ¯ Ã™Å Ø£Ø®Ø° Ã™â€¦Ø§ Ã˜Â¨Ã™Å Ã™â€  5 Ã˜Â¥Ã™â€žÃ™â€° 15 Ã˜Â¯Ã™â€šÃ™Å Ã™â€šØ© Ã™â€žÃ™â€žÃ˜Â¸Ã™â€¡Ã™Ë†Ø± Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â·Ã˜Â¨Ã™Å Ã™â€š Ø¨Ø¹Ø¯ Ã˜Â§Ã™â€žÃ˜Â¯Ã™ÂØ¹.<br><br>';
            } else if (sub === 'Ã™ÂÃ™â€¡Ã™â€¦ Ã˜Â§Ã™â€žØ¯Ø±Ø³') {
                tip = 'Ã°Å¸â€™Â¡ Ã™â€¡Ã™â€ž Ã˜ÂªÃ˜Â¹Ã™â€žÃ™â€¦Ã˜Å¸ Ã™Å Ã™â€¦Ã™Æ’Ã™â€ Ã™Æ’ Ã˜Â§Ã˜Â³Ã˜ÂªÃ˜Â®Ã˜Â¯Ã˜Â§Ã™â€¦ "Ã˜Â§Ã™â€žÃ˜Â®Ã˜Â±Ã™Å Ø·Ø© Ã˜Â§Ã™â€žÃ˜Â°Ã™â€¡Ã™â€ Ã™Å Ø©" Ã˜Â£Ã™Ë† "Ã™â€¦Ã™â€žØ®Øµ Ã˜Â§Ã™â€žØ¯Ø±Ø³" Ã˜Â§Ã™â€žÃ™â€¦Ã˜ÂªÃ™Ë†Ã™ÂØ±Ø© Ã™ÂÃ™Å  Ã™â€šÃ˜Â§Ã˜Â¦Ã™â€¦Ø© Ã˜Â§Ã™â€žØ¯Ø±Ø³ Ã™â€žÃ™â€žÃ˜Â­Ã˜ÂµÃ™Ë†Ã™â€ž Ã˜Â¹Ã™â€žÃ™â€° Ã™ÂÃ™Æ’Ø±Ø© Ã˜Â£Ã™Ë†Ø¶Ø­ Ã™â€šÃ˜Â¨Ã™â€ž Ø·Ø±Ø­ Ã˜Â§Ã™â€žÃ˜Â³Ã˜Â¤Ã˜Â§Ã™â€ž.<br><br>';
            }
            
            this.addMessage(tip + 'Ø¥Ø°Ø§ Ã™Æ’Ã˜Â§Ã™â€ Øª Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã™â€¦Ã˜Â³Ã˜ÂªÃ™â€¦Ã˜Â±Ã˜Â©Ã˜Å’ Ã™Å Ã˜Â±Ã˜Â¬Ã™â€° Ã™Æ’ØªØ§Ø¨Ø© Ã˜Â§Ã™â€žÃ˜ÂªÃ™ÂÃ˜Â§Ã˜ÂµÃ™Å Ã™â€ž Ã˜Â£Ã˜Â¯Ã™â€ Ã˜Â§Ã™â€¡:', 'bot');
            document.getElementById('support-chat-input-area').style.display = 'flex';
            document.getElementById('support-chat-input').focus();
            this.scrollToBottom();
        }, 500);
    },

    sendMessage: function() {
        const inp = document.getElementById('support-chat-input');
        const text = inp.value.trim();
        if(!text) return;
        
        this.message = text;
        inp.value = '';
        document.getElementById('support-chat-input-area').style.display = 'none';
        
        this.addMessage(text, 'user');
        
        // Typing indicator
        setTimeout(() => {
            const typingId = 'typing-' + Date.now();
            const typingHtml = `
                <div id="${typingId}" style="align-self: flex-start; background: white; padding: 12px 16px; border-radius: 16px 16px 0 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); display: flex; gap: 4px; align-items: center;">
                    <span style="width: 8px; height: 8px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both;"></span>
                    <span style="width: 8px; height: 8px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.2s;"></span>
                    <span style="width: 8px; height: 8px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.4s;"></span>
                    <span style="font-size: 12px; color: #6b7280; margin-right: 8px;">Ã˜Â¬Ã˜Â§Ã˜Â±Ã™Å  Ã˜Â§Ã™â€žØ¨Ø­Ø« Ã™ÂÃ™Å  Ã™â€šØ§Ø¹Ø¯Ø© Ã˜Â§Ã™â€žÃ˜Â¨Ã™Å Ã˜Â§Ã™â€ Ø§Øª...</span>
                </div>
                <style>@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }</style>
            `;
            document.getElementById('support-chat-history').insertAdjacentHTML('beforeend', typingHtml);
            this.scrollToBottom();
            
            // Fake delay for search
            setTimeout(() => {
                document.getElementById(typingId).remove();
                this.showFaqAndEscalate();
            }, 2500);
        }, 400);
    },

    showFaqAndEscalate: function() {
        const msg = `Ã™â€žÃ™â€žÃ˜Â£Ã˜Â³Ã™Â Ã™â€žÃ™â€¦ Ø£Ø¬Ø¯ Ø¥Ø¬Ø§Ø¨Ø© Ã™â€¦Ø¨Ø§Ø´Ø±Ø© Ã™â€žÃ™â€¦Ã˜Â´Ã™Æ’Ã™â€žÃ˜ÂªÃ™Æ’. Ã™Å Ã™â€¦Ã™Æ’Ã™â€ Ã™Æ’ Ã˜ÂªÃ˜ÂµÃ™ÂØ­ Ã˜Â§Ã™â€žÃ˜Â£Ã˜Â³Ã˜Â¦Ã™â€žØ© Ã˜Â§Ã™â€žØ´Ø§Ø¦Ø¹Ø© Ã˜Â£Ã˜Â¯Ã™â€ Ã˜Â§Ã™â€¡. Ø¥Ø°Ø§ Ã™â€žÃ™â€¦ ØªØ¬Ø¯ Ã˜Â­Ã™â€žÃ˜Â§Ã™â€¹Ã˜Å’ Ã™Å Ã™â€¦Ã™Æ’Ã™â€ Ã™Æ’ Ã˜ÂªÃ˜Â­Ã™Ë†Ã™Å Ã™â€ž Ã˜Â·Ã™â€žÃ˜Â¨Ã™Æ’ Ã™â€žÃ™â€žØ¥Ø¯Ø§Ø±Ø©.`;
        this.addMessage(msg, 'bot');
        
        const faqs = `
            <div style="background: white; border-radius: 12px; padding: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); align-self: flex-start; width: 100%; max-width: 90%; margin-top: 5px;">
                <details style="padding: 8px; border-bottom: 1px solid #f3f4f6;">
                    <summary style="font-weight: bold; cursor: pointer; color: var(--text-1);">Ã™Æ’Ã™Å Ã™Â Ã˜Â£Ã™â€šÃ™Ë†Ã™â€¦ Ã˜Â¨Ã˜ÂªÃ˜Â´Ã˜ÂºÃ™Å Ã™â€ž Ã˜Â§Ã™â€žÃ™ÂÃ™Å Ã˜Â¯Ã™Å Ã™Ë†Ã˜Å¸</summary>
                    <p style="margin-top: 8px; font-size: 13px; color: var(--text-2);">Ã˜ÂªÃ˜Â£Ã™Æ’Ø¯ Ã™â€¦Ã™â€  Ã˜Â§Ã˜ÂªÃ˜ÂµÃ˜Â§Ã™â€žÃ™Æ’ Ã˜Â¨Ã˜Â§Ã™â€žÃ˜Â¥Ã™â€ Ã˜ÂªÃ˜Â±Ã™â€ Øª Ã™Ë†Ø§Ø¶ØºØ· Ã˜Â¹Ã™â€žÃ™â€° Ø²Ø± Ã˜Â§Ã™â€žÃ˜ÂªÃ˜Â´Ã˜ÂºÃ™Å Ã™â€ž Ã™ÂÃ™Å  Ã™â€¦Ã™â€ Ã˜ÂªÃ˜ÂµÃ™Â Ã˜Â§Ã™â€žØ´Ø§Ø´Ø©.</p>
                </details>
                <details style="padding: 8px; border-bottom: 1px solid #f3f4f6;">
                    <summary style="font-weight: bold; cursor: pointer; color: var(--text-1);">Ã™Æ’Ã™Å Ã™Â Ã˜Â£Ã˜Â¹Ã™Ë†Ø¯ Ã™â€žÃ™â€žÃ˜ÂµÃ™ÂØ­Ø© Ã˜Â§Ã™â€žØ±Ø¦ÙŠØ³ÙŠØ©ØŸ</summary>
                    <p style="margin-top: 8px; font-size: 13px; color: var(--text-2);">Ã™Å Ã™â€¦Ã™Æ’Ã™â€ Ã™Æ’ Ã˜Â§Ã™â€žØ¶ØºØ· Ã˜Â¹Ã™â€žÃ™â€° Ø²Ø± "Ã˜ÂµÃ™â€ Ã˜Â¯Ã™Ë†Ã™â€š Ã˜Â§Ã™â€žÃ™Ë†Ø§Ø±Ø¯" Ã™ÂÃ™Å  Ã˜Â§Ã™â€žÃ™â€šÃ˜Â§Ã˜Â¦Ã™â€¦Ø© Ã˜Â§Ã™â€žÃ˜Â³Ã™ÂÃ™â€žÃ™Å Ø© Ã™â€žÃ™â€žÃ˜Â¹Ã™Ë†Ø¯Ø©.</p>
                </details>
                <details style="padding: 8px;">
                    <summary style="font-weight: bold; cursor: pointer; color: var(--text-1);">Ã™Æ’Ã™Å Ã™Â Ø£Ø¬Ø¯ Ã™â€¦Ã™â€žØ®Øµ Ã˜Â§Ã™â€žØ¯Ø±Ø³ØŸ</summary>
                    <p style="margin-top: 8px; font-size: 13px; color: var(--text-2);">Ã˜Â§Ã™â€žÃ™â€¦Ã™â€žØ®Øµ Ã™â€¦Ã˜ÂªÃ™Ë†Ã™ÂØ± Ã™ÂÃ™Å  Ã™â€šÃ˜Â§Ã˜Â¦Ã™â€¦Ø© Ã˜Â§Ã™â€žØ¯Ø±Ø³ Ø¹Ø¨Ø± Ø²Ø± (Ã˜Â§Ã™â€žÃ˜Â®Ã˜Â±Ã™Å Ø·Ø© Ã˜Â§Ã™â€žÃ˜Â°Ã™â€¡Ã™â€ Ã™Å Ø©).</p>
                </details>
            </div>
            
            <div style="align-self: center; margin-top: 15px; width: 100%; text-align: center;">
                <button onclick="supportFlow.escalateToAdmin()" style="background: #ef4444; color: white; border: none; padding: 12px 20px; border-radius: 24px; font-weight: bold; font-size: 14px; cursor: pointer; box-shadow: 0 4px 10px rgba(239, 68, 68, 0.3);">
                    Ã˜Â¥Ã˜Â±Ã˜Â³Ã˜Â§Ã™â€ž Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã˜Â¥Ã™â€žÃ™â€° Ã˜Â§Ã™â€žØ¥Ø¯Ø§Ø±Ø© Ã°Å¸â€œÂ©
                </button>
            </div>
        `;
        document.getElementById('support-chat-history').insertAdjacentHTML('beforeend', faqs);
        this.scrollToBottom();
    },

    escalateToAdmin: function() {
        // Hide the button
        event.target.style.display = 'none';
        
        this.addMessage("Ã˜Â¥Ã˜Â±Ã˜Â³Ã˜Â§Ã™â€ž Ã˜Â§Ã™â€žÃ™â€¦Ã˜Â´Ã™Æ’Ã™â€žØ© Ã˜Â¥Ã™â€žÃ™â€° Ã˜Â§Ã™â€žØ¥Ø¯Ø§Ø±Ø©", "user");
        
        setTimeout(() => {
            this.addMessage("Ã¢Å“â€¦ Ã˜ÂªÃ™â€¦Øª Ã˜Â¥Ã˜Â­Ã˜Â§Ã™â€žØ© Ã˜Â·Ã™â€žÃ˜Â¨Ã™Æ’ Ã˜Â¥Ã™â€žÃ™â€° Ã˜Â§Ã™â€žØ¥Ø¯Ø§Ø±Ø© Ã˜Â¨Ã™â€ Ø¬Ø§Ø­. Ã˜Â³Ã˜ÂªÃ˜ÂªÃ™â€žÃ™â€šÃ™â€° Ã˜Â±Ã˜Â¯Ã˜Â§Ã™â€¹ Ã™ÂÃ™Å  Ã˜Â£Ã™â€šØ±Ø¨ Ã™Ë†Ã™â€šØª Ã™â€¦Ã™â€¦Ã™Æ’Ã™â€  Ø¹Ø¨Ø± <b>Ã˜ÂµÃ™â€ Ã˜Â¯Ã™Ë†Ã™â€š Ã˜Â§Ã™â€žÃ™Ë†Ø§Ø±Ø¯</b> Ã˜Â§Ã™â€žØ®Ø§Øµ Ø¨Ùƒ.", "bot");
        }, 800);
    },

    addMessage: function(text, sender) {
        const isBot = sender === 'bot';
        const bg = isBot ? 'white' : 'var(--primary)';
        const color = isBot ? 'var(--text-1)' : 'white';
        const align = isBot ? 'flex-start' : 'flex-end';
        const radius = isBot ? '16px 16px 0 16px' : '16px 16px 16px 0';
        
        const html = `
            <div style="align-self: ${align}; background: ${bg}; color: ${color}; padding: 12px 16px; border-radius: ${radius}; box-shadow: 0 1px 2px rgba(0,0,0,0.1); max-width: 85%; line-height: 1.5;">
                ${text}
            </div>
        `;
        document.getElementById('support-chat-history').insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();
    },
    
    scrollToBottom: function() {
        const hist = document.getElementById('support-chat-history');
        hist.scrollTop = hist.scrollHeight;
    }
};




// ==========================================
// JOURNEY TAB (ROADMAP) LOGIC
// ==========================================

let currentJourneyLesson = null;

let currentView = 'lesson';
let taxonomyData = [];

function switchView(viewName) {
    currentView = viewName;
    document.querySelectorAll('.view-btn').forEach(b => {
        b.style.background = 'transparent';
        b.style.color = 'var(--text-2)';
        b.classList.remove('active');
    });
    
    const activeBtn = document.getElementById('btn-' + viewName);
    if(activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.style.background = 'var(--primary)';
        activeBtn.style.color = 'white';
        activeBtn.style.boxShadow = '0 2px 10px rgba(59,130,246,0.3)';
    }
    
    renderView();
}

async function fetchTaxonomy() {
    const subject = (typeof state !== 'undefined' && state ? state.subject : document.getElementById('subject-select') ? document.getElementById('subject-select').value : 'sira') || 'sira';
    const userId = (typeof state !== 'undefined' && state ? state.userId : 1);
    
    try {
        const res = await fetch('/api/student/quiz/taxonomy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId, subject })
        });
        const textData = await res.text();
        let data;
        try {
            data = JSON.parse(textData);
        } catch(parseErr) {
            throw new Error("Invalid JSON from server. Status: " + res.status + " | First 50 chars: " + textData.substring(0, 50));
        }
        if(data.success) {
            taxonomyData = data.questions || [];
            renderView();
        } else {
            document.getElementById('smart-tracker-container').innerHTML = `<div style="text-align:center; padding:20px; color:red;">خطأ في تحميل البيانات</div>`;
        }
    } catch(e) {
        console.error(e);
        document.getElementById('smart-tracker-container').innerHTML = `<div style="text-align:center; padding:20px; color:red;">فشل الاتصال: ${e.message}</div>`;
    }
}

function getProgressStats(qs) {
    let count = 0;
    qs.forEach(q => { 
        if (typeof state !== 'undefined' && state && state.progress && state.progress[q.id] === 'correct') count++; 
    });
    let percent = qs.length > 0 ? Math.round((count / qs.length) * 100) : 0;
    return { count, total: qs.length, percent, isDone: percent === 100 };
}

function renderProgressRing(prog) {
    let color = prog.isDone ? '#10b981' : 'var(--primary)';
    let offset = 125.6 - (125.6 * prog.percent / 100);
    return `
    <div style="position:relative; width:45px; height:45px; display:flex; align-items:center; justify-content:center; border-radius:50%; background:var(--surface); box-shadow:0 2px 5px rgba(0,0,0,0.1); flex-shrink:0;">
        <svg width="45" height="45" style="position:absolute; top:0; left:0; transform:rotate(-90deg);">
            <circle cx="22.5" cy="22.5" r="20" fill="none" stroke="var(--border-color)" stroke-width="3"></circle>
            <circle cx="22.5" cy="22.5" r="20" fill="none" stroke="${color}" stroke-width="3" stroke-dasharray="125.6" stroke-dashoffset="${offset}" style="transition:0.5s;"></circle>
        </svg>
        <span style="font-size:0.75rem; font-weight:bold; color:var(--text-2); z-index:1;">${prog.percent}%</span>
    </div>`;
}

function renderView() {
    const container = document.getElementById('smart-tracker-container');
    container.innerHTML = '';
    
    if (taxonomyData.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-3); font-family: 'Tajawal', sans-serif;">لا توجد أسئلة لهذه المادة حالياً.</div>`;
        return;
    }
    
    if (currentView === 'lesson') {
        let lessons = {};
        taxonomyData.forEach(q => {
            if(!lessons[q.lessonNum]) lessons[q.lessonNum] = { title: `الدرس ${q.lessonNum}`, qs: [] };
            lessons[q.lessonNum].qs.push(q);
        });

        Object.keys(lessons).sort((a,b)=>a-b).forEach(k => {
            let l = lessons[k];
            let prog = getProgressStats(l.qs);
            let cardColor = prog.isDone ? 'rgba(16, 185, 129, 0.05)' : 'var(--bg)';
            let borderColor = prog.isDone ? '#10b981' : 'var(--border-color)';
            let titleColor = prog.isDone ? '#10b981' : 'var(--text-1)';
            
            container.innerHTML += `
                <div onclick='openSheet("${l.title}", "تمرين شامل على الدرس", ${JSON.stringify(l.qs).replace(/'/g, "&apos;")})' style="background:${cardColor}; border:1px solid ${borderColor}; border-radius:12px; padding:12px 16px; display:flex; align-items:center; justify-content:space-between; cursor:pointer; font-family: 'Tajawal', sans-serif;">
                    <div style="display:flex; align-items:center; gap:12px;">
                        ${renderProgressRing(prog)}
                        <div>
                            <div style="font-weight:bold; font-size:1rem; color:${titleColor};">${l.title}</div>
                            <div style="font-size:0.8rem; color:var(--text-3);">${prog.count} من ${prog.total} مكتمل</div>
                        </div>
                    </div>
                    <div style="color:var(--text-3);"><i class="fa-solid fa-chevron-left"></i></div>
                </div>
            `;
        });
        
    } else if (currentView === 'theme') {
        // V2: TREE VIEW
        let themes = {};
        taxonomyData.forEach(q => {
            if(!themes[q.theme]) themes[q.theme] = {};
            if(!themes[q.theme][q.subTheme]) themes[q.theme][q.subTheme] = [];
            themes[q.theme][q.subTheme].push(q);
        });

        Object.keys(themes).forEach(tName => {
            let subThemes = themes[tName];
            let themeQs = [];
            Object.values(subThemes).forEach(qs => themeQs = themeQs.concat(qs));
            let themeProg = getProgressStats(themeQs);
            
            let html = `
            <div style="margin-bottom:20px; font-family: 'Tajawal', sans-serif;">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
                    <div style="width:12px; height:12px; border-radius:50%; background:var(--primary); box-shadow:0 0 8px rgba(59,130,246,0.5);"></div>
                    <div style="font-weight:bold; font-size:1.2rem; color:var(--text-1);">${tName}</div>
                    <div style="flex-grow:1; height:2px; background:var(--border-color); border-radius:2px; overflow:hidden;">
                        <div style="width:${themeProg.percent}%; height:100%; background:var(--primary); transition:0.5s;"></div>
                    </div>
                    <div style="font-size:0.85rem; font-weight:bold; color:var(--text-2);">${themeProg.percent}%</div>
                </div>
                <div style="padding-right:24px; border-right:2px solid var(--border-color); margin-right:5px; padding-top:8px;">
            `;
            
            Object.keys(subThemes).forEach(stName => {
                let qs = subThemes[stName];
                let prog = getProgressStats(qs);
                let isDone = prog.isDone;
                let dotColor = isDone ? '#10b981' : (prog.percent > 0 ? '#f59e0b' : 'var(--text-3)');
                
                html += `
                    <div onclick='openSheet("${stName}", "موضوع: ${tName}", ${JSON.stringify(qs).replace(/'/g, "&apos;")})' style="display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-radius:12px; background:var(--surface); border:1px solid var(--border-color); margin-bottom:8px; cursor:pointer; position:relative; box-shadow:0 2px 4px rgba(0,0,0,0.02); transition:0.2s;" onmouseover="this.style.borderColor='var(--primary)'" onmouseout="this.style.borderColor='var(--border-color)'">
                        <div style="position:absolute; right:-26px; top:50%; width:24px; height:2px; background:var(--border-color);"></div>
                        <div style="display:flex; align-items:center; gap:12px;">
                            <i class="${isDone ? 'fa-solid fa-circle-check' : 'fa-regular fa-circle'}" style="color:${dotColor}; font-size:1.1rem;"></i>
                            <div style="font-size:0.95rem; font-weight:bold; color:${isDone ? '#10b981' : 'var(--text-1)'};">${stName}</div>
                        </div>
                        <div style="font-size:0.8rem; font-weight:bold; color:white; background:${dotColor}; padding:2px 8px; border-radius:12px;">${prog.count}/${prog.total}</div>
                    </div>
                `;
            });
            
            html += `</div></div>`;
            container.innerHTML += html;
        });
        
    } else if (currentView === 'chrono') {
        let chronos = {};
        taxonomyData.forEach(q => {
            if(!chronos[q.hijriYear]) chronos[q.hijriYear] = [];
            chronos[q.hijriYear].push(q);
        });
        
        let html = `<div style="position:relative; padding-right:20px; font-family: 'Tajawal', sans-serif;">
                    <div style="position:absolute; top:0; bottom:0; right:9px; width:2px; background:var(--border-color);"></div>`;
                    
        Object.keys(chronos).forEach(year => {
            let qs = chronos[year];
            let prog = getProgressStats(qs);
            html += `
                <div onclick='openSheet("${year}", "الفترة الزمنية", ${JSON.stringify(qs).replace(/'/g, "&apos;")})' style="position:relative; padding-right:20px; margin-bottom:20px;">
                    <div style="position:absolute; right:-24px; top:4px; width:10px; height:10px; border-radius:50%; background:var(--primary); border:4px solid var(--surface);"></div>
                    <div style="background:var(--surface); border:1px solid var(--border-color); border-radius:12px; padding:12px; cursor:pointer;">
                        <div style="font-weight:bold; color:var(--primary); margin-bottom:4px; font-size:1.1rem;">${year}</div>
                        <div style="font-size:0.85rem; color:var(--text-2); display:flex; justify-content:space-between;">
                            <span>${qs.length} أسئلة في هذه الفترة</span>
                            <span style="font-weight:bold;">${prog.percent}%</span>
                        </div>
                    </div>
                </div>
            `;
        });
        html += `</div>`;
        container.innerHTML = html;
        
    } else if (currentView === 'weak') {
        // V2: WEAK POINTS TAB
        let weakQs = taxonomyData.filter(q => typeof state !== 'undefined' && state && state.progress && state.progress[q.id] === 'wrong');
        
        if (weakQs.length === 0) {
            container.innerHTML = `
                <div style="text-align:center; padding:40px 20px; font-family: 'Tajawal', sans-serif;">
                    <i class="fa-solid fa-trophy" style="font-size:3rem; color:#10b981; margin-bottom:16px;"></i>
                    <h3 style="color:var(--text-1); margin-bottom:8px;">أنت رائع!</h3>
                    <p style="color:var(--text-2);">لا توجد لديك أي أخطاء متراكمة في هذه المادة حالياً.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div style="background:linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(245, 158, 11, 0.1)); border-radius:16px; padding:24px; text-align:center; margin-bottom:20px; border:1px solid rgba(239, 68, 68, 0.2); font-family: 'Tajawal', sans-serif;">
                <i class="fa-solid fa-brain" style="font-size:2.5rem; color:#ef4444; margin-bottom:12px;"></i>
                <h3 style="color:#ef4444; margin-bottom:8px;">${weakQs.length} نقاط ضعف تحتاج للمراجعة</h3>
                <p style="color:var(--text-2); font-size:0.9rem; margin-bottom:20px;">الأسئلة التي أجبت عليها بشكل خاطئ سابقاً. المراجعة المتباعدة هي سر الإتقان.</p>
                
                <button onclick='startSpecificQuiz(${JSON.stringify(weakQs).replace(/'/g, "&apos;")})' style="background:#ef4444; color:white; border:none; padding:12px 24px; border-radius:12px; font-weight:bold; font-size:1rem; cursor:pointer; width:100%; box-shadow:0 4px 12px rgba(239,68,68,0.3); font-family: 'Tajawal', sans-serif;">
                    <i class="fa-solid fa-dumbbell"></i> ابدأ مراجعة الأخطاء
                </button>
            </div>
        `;
        
        // List them by theme
        let html = '<div style="display:flex; flex-direction:column; gap:10px; font-family: \'Tajawal\', sans-serif;">';
        weakQs.forEach(q => {
            html += `
                <div style="background:var(--surface); border-left:4px solid #ef4444; border-radius:8px; padding:12px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <div style="font-weight:bold; font-size:0.95rem; color:var(--text-1); margin-bottom:4px;">${q.title}</div>
                    <div style="display:flex; gap:8px; font-size:0.75rem;">
                        <span style="background:rgba(59,130,246,0.1); color:var(--primary); padding:2px 8px; border-radius:6px;">الدرس ${q.lessonNum}</span>
                        <span style="background:var(--bg); color:var(--text-2); padding:2px 8px; border-radius:6px;">${q.subTheme}</span>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML += html;
    }
}

// BUG FIX: Directly start quiz with specific questions array without relying on select elements
function startSpecificQuiz(questionsArray) {
    if(!window.quizEngine) return;
    
    // We override the quizEngine's internal questions array
    quizEngine.questions = questionsArray;
    
    // Switch to quiz view manually if needed (quizEngine.start usually handles this)
    if (typeof openTab === 'function') openTab('quiz');
    
    // Reset internal state and start
    quizEngine.currentQuestionIndex = 0;
    quizEngine.correctAnswers = 0;
    quizEngine.wrongAnswers = 0;
    quizEngine.startTimer();
    quizEngine.showQuestion();
    
    // Update UI elements if they exist
    const container = document.getElementById('quiz-container');
    const resultDiv = document.getElementById('quiz-result');
    const paramsDiv = document.getElementById('quiz-params');
    if(container) container.style.display = 'block';
    if(resultDiv) resultDiv.style.display = 'none';
    if(paramsDiv) paramsDiv.style.display = 'none';
}

function openSheet(title, subtitle, questions) {
    document.getElementById('sheet-title').innerText = title;
    
    let sheetHeader = document.getElementById('sheet-title').parentNode;
    let sub = document.getElementById('sheet-subtitle');
    if(!sub) {
        sub = document.createElement('div');
        sub.id = 'sheet-subtitle';
        sub.style = "font-size:0.85rem; color:var(--text-3); margin-top:4px; font-family: 'Tajawal', sans-serif;";
        sheetHeader.insertBefore(sub, sheetHeader.childNodes[1]);
    }
    sub.innerText = subtitle;
    
    const grid = document.getElementById('journey-q-grid');
    grid.innerHTML = '';
    
    let progressProg = getProgressStats(questions);
    
    grid.style.display = 'grid';
    grid.style.gridTemplateColumns = '1fr';
    grid.style.gap = '10px';
    
    questions.forEach((q, idx) => {
        const row = document.createElement('div');
        let qStatus = (typeof state !== 'undefined' && state && state.progress) ? state.progress[q.id] || 'unanswered' : 'unanswered';
        
        let rowClass = 'background:var(--bg); border:1px solid var(--border-color); border-radius:12px; padding:12px; display:flex; align-items:center; justify-content:space-between; cursor:pointer; transition:0.2s; font-family: \'Tajawal\', sans-serif;';
        if(qStatus === 'correct') rowClass += ' border-left: 4px solid #10b981; background: rgba(16, 185, 129, 0.05);';
        if(qStatus === 'wrong') rowClass += ' border-left: 4px solid #ef4444; background: rgba(239, 68, 68, 0.05);';
        row.style.cssText = rowClass;
        
        let iconHtml = `<div style="width:30px; height:30px; border-radius:50%; display:flex; justify-content:center; align-items:center; font-weight:bold; font-size:0.9rem; color:var(--text-2); background:var(--surface); border:1px solid var(--border-color); flex-shrink:0;">${idx+1}</div>`;
        if(qStatus === 'correct') iconHtml = `<div style="width:30px; height:30px; border-radius:50%; display:flex; justify-content:center; align-items:center; font-weight:bold; font-size:0.9rem; color:#10b981; background:rgba(16, 185, 129, 0.1); border:1px solid #10b981; flex-shrink:0;"><i class="fa-solid fa-check"></i></div>`;
        if(qStatus === 'wrong') iconHtml = `<div style="width:30px; height:30px; border-radius:50%; display:flex; justify-content:center; align-items:center; font-weight:bold; font-size:0.9rem; color:#ef4444; background:rgba(239, 68, 68, 0.1); border:1px solid #ef4444; flex-shrink:0;"><i class="fa-solid fa-xmark"></i></div>`;
        
        let badgeHtml = currentView !== 'lesson' ? `<div style="font-size:0.7rem; background:var(--primary); color:white; padding:2px 8px; border-radius:6px; font-weight:bold;">الدرس ${q.lessonNum}</div>` : '';
        let truncatedTitle = q.title ? q.title.substring(0, 45) + (q.title.length > 45 ? '...' : '') : 'سؤال';
        
        row.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px;">
                ${iconHtml}
                <div style="font-size:0.95rem; font-weight:bold; color:var(--text-1);">${truncatedTitle}</div>
            </div>
            ${badgeHtml}
        `;
        
        row.onclick = () => {
            closeJourneySheet();
            setTimeout(() => {
                startSpecificQuiz([q]);
            }, 300);
        };
        grid.appendChild(row);
    });
    
    // Update the main button to play ALL questions in this sheet
    const btn = document.getElementById('btn-play-all-lesson');
    if(btn) {
        if(progressProg.isDone) {
            btn.innerHTML = '<i class="fa-solid fa-rotate-right"></i> إعادة التدريب';
            btn.style.background = 'var(--text-2)';
        } else {
            btn.innerHTML = '<i class="fa-solid fa-play"></i> ابدأ التدريب';
            btn.style.background = 'var(--primary)';
        }
        btn.onclick = () => {
            closeJourneySheet();
            setTimeout(() => {
                startSpecificQuiz(questions);
            }, 300);
        };
    }
    
    document.getElementById('journey-bottom-sheet').classList.add('open');
    document.getElementById('journey-sheet-overlay').classList.add('open');
}

function closeJourneySheet() {
    document.getElementById('journey-bottom-sheet').classList.remove('open');
    document.getElementById('journey-sheet-overlay').classList.remove('open');
}

function renderJourneyTimeline() {
    fetchTaxonomy();
}


function playWholeLesson() {
    closeJourneySheet();
    setTimeout(() => {
        if(window.quizEngine) {
            document.getElementById('subject-select').value = (typeof state !== 'undefined' && state ? state.subject : document.getElementById('subject-select') ? document.getElementById('subject-select').value : 'sira') || 'sira';
            document.getElementById('lesson-select').value = currentJourneyLesson;
            quizEngine.start();
        }
    }, 300);
}

