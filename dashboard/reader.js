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
    'sira': 'Ø§Ù„Ø³ÙŠØ±Ø© Ø§Ù„Ù†Ø¨ÙˆÙŠØ©',
    'fiqh': 'Ø§Ù„ÙÙ‚Ù‡',
    'tahawi': 'Ø§Ù„Ø¹Ù‚ÙŠØ¯Ø© Ø§Ù„Ø·Ø­Ø§ÙˆÙŠØ©',
    'adab': 'Ø§Ù„Ø£Ø¯Ø¨',
    'nahw': 'Ø§Ù„Ù†Ø­Ùˆ'
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
                switchTab('home');
            }
        } else {
            switchTab('home');
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
                btnSticky.title = "Ã‰pingler la vidÃ©o";
                sommaireWrapper.style.top = '0px';
            } else {
                // Pin
                videoWrapper.classList.add('pinned');
                videoWrapper.style.position = 'sticky';
                btnSticky.style.opacity = '1';
                btnSticky.title = "DÃ©sÃ©pingler la vidÃ©o";
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
        if(currentTheme === 'dark') themeBtn.textContent = 'â˜€ï¸';
        else if(currentTheme === 'sepia') themeBtn.textContent = 'ðŸ“œ';
        else themeBtn.textContent = 'ðŸŒ™';

        themeBtn.addEventListener('click', () => {
            if (currentTheme === 'light') currentTheme = 'sepia';
            else if (currentTheme === 'sepia') currentTheme = 'dark';
            else currentTheme = 'light';
            
            document.documentElement.setAttribute('data-theme', currentTheme);
            localStorage.setItem('readerTheme', currentTheme);
            
            if (currentTheme === 'dark') themeBtn.textContent = 'â˜€ï¸';
            else if (currentTheme === 'sepia') themeBtn.textContent = 'ðŸ“œ';
            else themeBtn.textContent = 'ðŸŒ™';
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
                    <p style="margin-bottom: 4px; font-weight: 600; color: var(--subject-color, var(--primary));">Ø§Ù„Ø¯Ø±ÙˆØ³: ${data.lessons.length}</p>
                    <p style="color: var(--text-2); font-size: 13px;">Ø§Ù„Ù…Ø­Ø§ÙˆØ± Ø§Ù„Ù…Ù†Ø¬Ø²Ø©: ${completedBlocks}/${totalBlocks}</p>
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
            subjHeader.innerHTML = `<h3>${data.label}</h3><span class="chev">â–¼</span>`;
            
            const subjContent = document.createElement('div');
            subjContent.className = 'subject-content subject-list';
            
            data.lessons.forEach(l => {
                let html = `<div style="background:var(--bg); border-radius:12px; margin-bottom:10px; overflow:hidden;">
                    <div style="padding:12px; background:var(--surface); border-bottom:1px solid var(--border-color); font-weight:bold; display:flex; justify-content:space-between; align-items:center;" onclick="openLessonFromList('${l.subject}', ${l.lessonNum})">
                        <span>Ø§Ù„Ø¯Ø±Ø³ ${l.lessonNum} - ${l.title || ''}</span>
                    </div>
                    <div style="padding:10px;">`;
                
                if (l.thematic_blocks && l.thematic_blocks.length) {
                    l.thematic_blocks.forEach((b, idx) => {
                        const compKey = `${l.subject}_${l.lessonNum}_${idx}`;
                        const isComp = !!syllabusCompletion[compKey];
                        html += `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px; background:white; margin-bottom:6px; border-radius:8px; border:1px solid ${isComp ? 'var(--primary)' : 'var(--border-color)'};">
                            <button onclick="toggleChapterCompletion(event, '${l.subject}', ${l.lessonNum}, ${idx})" style="width:24px; height:24px; border-radius:50%; border:2px solid ${isComp ? 'var(--primary)' : '#cbd5e1'}; background:${isComp ? 'var(--primary)' : 'none'}; color:white; font-size:12px; cursor:pointer; display:flex; justify-content:center; align-items:center; flex-shrink:0;">${isComp ? 'âœ“' : ''}</button>
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
        <button class="back-btn" onclick="buildSyllabusTab(DB)">Ø±Ø¬ÙˆØ¹ âž¡ï¸</button>
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
                badgeHtml = `<div style="font-size: 11px; font-weight: bold; color: var(--success, #10b981); background: rgba(16, 185, 129, 0.1); padding: 2px 6px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; width: 100%; box-sizing: border-box; margin-top: 4px; line-height: 1.2;">âœ… ${comp}/${total} Ù…Ø­Ø§ÙˆØ±</div>`;
            } else if (comp > 0) {
                badgeHtml = `<div style="font-size: 11px; font-weight: bold; color: var(--subject-color, var(--primary, var(--accent-color))); background: rgba(0, 0, 0, 0.05); padding: 2px 6px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; width: 100%; box-sizing: border-box; margin-top: 4px; line-height: 1.2;">â–¶ï¸ ${comp}/${total} Ù…Ø­Ø§ÙˆØ±</div>`;
            } else {
                badgeHtml = `<div style="font-size: 11px; font-weight: bold; color: var(--text-3); background: rgba(0, 0, 0, 0.05); padding: 2px 6px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; width: 100%; box-sizing: border-box; margin-top: 4px; line-height: 1.2;">${total} Ù…Ø­Ø§ÙˆØ±</div>`;
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
        videoWrapper.innerHTML = '<div style="background:#1e293b; color:white; height:100%; display:flex; align-items:center; justify-content:center; flex-direction:column;"><span style="font-size:32px;margin-bottom:8px;">ðŸŽ¥</span><span style="font-size:14px;">Ø§Ù„ÙÙŠØ¯ÙŠÙˆ ØºÙŠØ± Ù…ØªÙˆÙØ± Ù„Ù‡Ø°Ø§ Ø§Ù„Ø¯Ø±Ø³</span></div>';
    } else {
        if (!document.getElementById('youtube-player')) {
            videoWrapper.innerHTML = '<div id="youtube-player"></div>';
        }
        if (window.YT && window.YT.Player) {
            initYouTubePlayer(videoId);
        } else {
            // API non prÃªte
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
            title: "LeÃ§on complÃ¨te",
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
                const numBadge = part.num ? `<div style="position: absolute; top: -14px; right: 20px; background: var(--gold, #d4af37); color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 2px solid white;">Ø¨ÙŠØª ${part.num}</div>` : '';
                
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
                    <span class="explanation-icon">ðŸ’¡</span>
                    <span class="explanation-title">ØªÙˆØ¬ÙŠÙ‡ ÙˆÙØ§Ø¦Ø¯Ø© (Note du Professeur)</span>
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
        sheetTitle.textContent = `Ù…Ø­Ø§ÙˆØ± Ø§Ù„Ø¯Ø±Ø³ ${currentLessonData.lessonNum}`;
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
        checkBtn.innerHTML = isComp ? 'âœ“' : '';
        checkBtn.onclick = (e) => {
            e.stopPropagation();
            isComp = !isComp;
            syllabusCompletion[compKey] = isComp;
            localStorage.setItem('academy_syllabus_completions', JSON.stringify(syllabusCompletion));
            checkBtn.className = 'sommaire-check-btn ' + (isComp ? 'completed' : '');
            checkBtn.innerHTML = isComp ? 'âœ“' : '';
            
            updateDashboardProgress();
            
            if (currentTabIndex === index) {
                const vBtn = document.querySelector('.validate-chapter-btn');
                if (vBtn) {
                    vBtn.className = isComp ? 'validate-chapter-btn completed' : 'validate-chapter-btn';
                    vBtn.innerHTML = isComp ? 'âœ“ ØªÙ… Ø¥Ù†Ø¬Ø§Ø² Ø§Ù„Ù…Ø­ÙˆØ±' : 'ØªØ¹Ù„ÙŠÙ… ÙƒÙ…Ù‚Ø±ÙˆØ¡';
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
        courseBadge.textContent = `${subjLabel} â€¢ Ø§Ù„Ø¯Ø±Ø³ ${currentLessonNum}`;
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
        finishBtn.innerHTML = 'âœ… Ø£ÙƒÙ…Ù„Øª Ù‡Ø°Ø§ Ø§Ù„Ù…Ø­ÙˆØ±';
        finishBtn.onclick = (e) => {
            toggleChapterCompletion(e, currentSubject, currentLessonNum, index);
            if (finishBtn.classList.contains('completed')) {
                finishBtn.classList.remove('completed');
                finishBtn.innerHTML = 'âœ… Ø£ÙƒÙ…Ù„Øª Ù‡Ø°Ø§ Ø§Ù„Ù…Ø­ÙˆØ±';
                finishBtn.style.background = 'var(--surface)';
                finishBtn.style.color = 'var(--text)';
            } else {
                finishBtn.classList.add('completed');
                finishBtn.innerHTML = 'âœ”ï¸ ØªÙ… Ø¥Ù†Ø¬Ø§Ø² Ø§Ù„Ù…Ø­ÙˆØ±';
                finishBtn.style.background = 'var(--success, #10b981)';
                finishBtn.style.color = 'white';
            }
        };
        
        // Check if already completed
        const compKey = `${currentSubject}_${currentLessonNum}_${index}`;
        if (syllabusCompletion[compKey]) {
            finishBtn.classList.add('completed');
            finishBtn.innerHTML = 'âœ”ï¸ ØªÙ… Ø¥Ù†Ø¬Ø§Ø² Ø§Ù„Ù…Ø­ÙˆØ±';
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
        nextBtn.innerHTML = `Ø§Ù„ØªØ§Ù„ÙŠ: ${thematicData[index+1].title} â¬…ï¸`;
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
        markBtn.textContent = 'âœ“ Ù…ÙƒØªÙ…Ù„';
        markBtn.disabled = true;
    } else {
        markBtn.style.background = 'var(--primary)';
        markBtn.style.color = 'white';
        markBtn.textContent = 'âœ… Ø¥Ù†Ù‡Ø§Ø¡ Ù‡Ø°Ø§ Ø§Ù„Ù…Ø­ÙˆØ±';
        markBtn.onclick = () => {
            if (currentLessonData) {
                toggleChapterCompletion(null, currentLessonData.subject, currentLessonData.lessonNum, index);
                markBtn.style.background = '#e2e8f0';
                markBtn.style.color = '#64748b';
                markBtn.textContent = 'âœ“ Ù…ÙƒØªÙ…Ù„';
                markBtn.disabled = true;
                
                // Show completion toast or visual effect
                let tst = document.createElement('div');
                tst.textContent = 'ØªÙ… ØªØ³Ø¬ÙŠÙ„ Ø§Ù„ØªÙ‚Ø¯Ù…!';
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
        practiceBtn.innerHTML = 'ðŸŽ¯ Ø§Ù„ØªØ¯Ø±ÙŠØ¨ Ø¹Ù„Ù‰ Ù‡Ø°Ø§ Ø§Ù„Ø¯Ø±Ø³';
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
    if (text.includes("ðŸ“")) {
        let parts = text.split("ðŸ“");
        text = parts[0].trim();
        sourceText = "ðŸ“ " + parts[1].trim();
    } else if (text.includes("Ø§Ù„Ù…ØµØ¯Ø±")) {
        let parts = text.split("Ø§Ù„Ù…ØµØ¯Ø±");
        text = parts[0].trim();
        sourceText = "ðŸ“ Ø§Ù„Ù…ØµØ¯Ø± " + parts[1].trim();
    }

    let profNote = "";
    const profPatterns = ["ØªÙˆØ¬ÙŠÙ‡ ÙˆÙØ§Ø¦Ø¯Ø© :", "Ù…Ù„Ø§Ø­Ø¸Ø© Ø§Ù„Ø£Ø³ØªØ§Ø° :", "ÙØ§Ø¦Ø¯Ø© :"];
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
        parsedHtml += `<div class="exp-main" style="margin-bottom:12px; font-size:14px;"><strong>Ø§Ù„ØªÙˆØ¶ÙŠØ­:</strong><br>${text}</div>`;
    }
    if (profNote) {
        parsedHtml += `<div class="exp-prof" style="margin-bottom:12px; background:var(--surface-2); padding:12px; border-radius:8px; border-right:3px solid var(--primary); font-size:13.5px;"><span style="font-size:16px;">ðŸ’¡</span> <strong>ØªÙˆØ¬ÙŠÙ‡ ÙˆÙØ§Ø¦Ø¯Ø©:</strong><br>${profNote}</div>`;
    }
    if (sourceText) {
        parsedHtml += `<div class="exp-source" style="font-size:12px; color:var(--text-3); margin-top:8px;">${sourceText}</div>`;
    }

    container.innerHTML = `
        <div class="quiz-header">Ø³Ø¤Ø§Ù„ ØªÙØ§Ø¹Ù„ÙŠ</div>
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

// â”€â”€ RICH TEXT PARSERS â”€â”€
function formatProse(text) {
    if (!text) return '';
    let result = text;
    // Quranic verses inside {}
    result = result.replace(/\{([^{}]+)\}/g, (match, verse) => {
        const cleanVerse = verse.trim();
        return `<span class="quran-verse">ï´¿ ${cleanVerse} ï´¾</span>`;
    });
    result = highlightGlossary(result);
    return result;
}

function highlightGlossary(text) {
    let result = text;
    
    // Order matters: longer/more specific patterns first to avoid partial matches
    const GLOSSARY_MATCHERS = [
        // â”€â”€ Ù†Ø³Ø§Ø¡ (rose/pink) â”€â”€
        { term: "Ø®Ø¯ÙŠØ¬Ø© Ø¨Ù†Øª Ø®ÙˆÙŠÙ„Ø¯",         pattern: "Ø®Ø¯ÙŠØ¬[Ø©Ù‡] Ø¨Ù†Øª Ø®ÙˆÙŠÙ„Ø¯|Ø®Ø¯ÙŠØ¬[Ø©Ù‡] Ø±Ø¶ÙŠ Ø§Ù„Ù„Ù‡ Ø¹Ù†Ù‡Ø§|Ø®Ø¯ÙŠØ¬[Ø©Ù‡]" },
        { term: "Ø¹Ø§Ø¦Ø´Ø© Ø¨Ù†Øª Ø£Ø¨ÙŠ Ø¨ÙƒØ±",        pattern: "Ø¹Ø§Ø¦Ø´[Ø©Ù‡] Ø¨Ù†Øª [Ø£Ø§]Ø¨ÙŠ Ø¨ÙƒØ±|Ø¹Ø§Ø¦Ø´[Ø©Ù‡] Ø±Ø¶ÙŠ Ø§Ù„Ù„Ù‡ Ø¹Ù†Ù‡Ø§|Ø¹Ø§Ø¦Ø´[Ø©Ù‡]|Ø§Ù„Ø³ÙŠØ¯Ø© Ø¹Ø§Ø¦Ø´[Ø©Ù‡]" },
        { term: "ÙØ§Ø·Ù…Ø© Ø§Ù„Ø²Ù‡Ø±Ø§Ø¡",            pattern: "ÙØ§Ø·Ù…[Ø©Ù‡] Ø§Ù„Ø²Ù‡Ø±Ø§Ø¡|ÙØ§Ø·Ù…[Ø©Ù‡] Ø¨Ù†Øª Ù…Ø­Ù…Ø¯|ÙØ§Ø·Ù…[Ø©Ù‡]" },
        { term: "Ø²ÙŠÙ†Ø¨ Ø¨Ù†Øª Ø¬Ø­Ø´",            pattern: "Ø²ÙŠÙ†Ø¨ Ø¨Ù†Øª Ø¬Ø­Ø´|Ø§Ù„Ø³ÙŠØ¯Ø© Ø²ÙŠÙ†Ø¨" },
        { term: "Ø²ÙŠÙ†Ø¨ Ø¨Ù†Øª Ù…Ø­Ù…Ø¯",            pattern: "Ø²ÙŠÙ†Ø¨ Ø¨Ù†Øª Ù…Ø­Ù…Ø¯|Ø²ÙŠÙ†Ø¨ Ø¨Ù†Øª Ø§Ù„Ù†Ø¨ÙŠ|Ø²ÙŠÙ†Ø¨" },
        { term: "Ø£Ù… Ø³Ù„Ù…Ø©",                 pattern: "[Ø£Ø§]Ù… Ø³Ù„Ù…[Ø©Ù‡]|Ù‡Ù†Ø¯ Ø¨Ù†Øª [Ø£Ø§]Ø¨ÙŠ [Ø£Ø§]Ù…ÙŠ[Ø©Ù‡]" },
        { term: "ØµÙÙŠØ© Ø¨Ù†Øª Ø­ÙŠÙŠ",            pattern: "ØµÙÙŠ[Ø©Ù‡] Ø¨Ù†Øª Ø­ÙŠÙŠ|ØµÙÙŠ[Ø©Ù‡]" },
        { term: "Ø­ÙØµØ© Ø¨Ù†Øª Ø¹Ù…Ø±",            pattern: "Ø­ÙØµ[Ø©Ù‡] Ø¨Ù†Øª Ø¹Ù…Ø±|Ø­ÙØµ[Ø©Ù‡]" },
        { term: "Ø±Ù‚ÙŠØ© Ø¨Ù†Øª Ù…Ø­Ù…Ø¯",            pattern: "Ø±Ù‚ÙŠ[Ø©Ù‡] Ø¨Ù†Øª Ù…Ø­Ù…Ø¯|Ø±Ù‚ÙŠ[Ø©Ù‡]" },
        { term: "Ø£Ù… ÙƒÙ„Ø«ÙˆÙ… Ø¨Ù†Øª Ù…Ø­Ù…Ø¯",        pattern: "[Ø£Ø§]Ù… ÙƒÙ„Ø«ÙˆÙ… Ø¨Ù†Øª Ù…Ø­Ù…Ø¯|[Ø£Ø§]Ù… ÙƒÙ„Ø«ÙˆÙ…" },
        { term: "Ù‡Ù†Ø¯ Ø¨Ù†Øª Ø¹ØªØ¨Ø©",             pattern: "Ù‡Ù†Ø¯ Ø¨Ù†Øª Ø¹ØªØ¨[Ø©Ù‡]|Ù‡Ù†Ø¯" },
        { term: "Ø£Ø³Ù…Ø§Ø¡ Ø¨Ù†Øª Ø£Ø¨ÙŠ Ø¨ÙƒØ±",        pattern: "[Ø£Ø§]Ø³Ù…Ø§Ø¡ Ø¨Ù†Øª [Ø£Ø§]Ø¨ÙŠ Ø¨ÙƒØ±|[Ø£Ø§]Ø³Ù…Ø§Ø¡|Ø°Ø§Øª Ø§Ù„Ù†Ø·Ø§Ù‚ÙŠÙ†" },
        { term: "Ù…Ø§Ø±ÙŠØ§ Ø§Ù„Ù‚Ø¨Ø·ÙŠØ©",            pattern: "Ù…Ø§Ø±ÙŠ[Ø©Ø§] Ø§Ù„Ù‚Ø¨Ø·ÙŠ[Ø©Ù‡]|Ù…Ø§Ø±ÙŠ[Ø©Ø§]" },
        // â”€â”€ Ø±Ø¬Ø§Ù„ (bleu) â”€â”€
        { term: "Ø£Ø¨Ùˆ Ø¨ÙƒØ± Ø§Ù„ØµØ¯ÙŠÙ‚",           pattern: "[Ø£Ø§]Ø¨Ùˆ Ø¨ÙƒØ± Ø§Ù„ØµØ¯ÙŠÙ‚|Ø§Ù„ØµØ¯ÙŠÙ‚|[Ø£Ø§]Ø¨Ùˆ Ø¨ÙƒØ±" },
        { term: "Ø¹Ù…Ø± Ø¨Ù† Ø§Ù„Ø®Ø·Ø§Ø¨",            pattern: "Ø¹Ù…Ø± Ø¨Ù† Ø§Ù„Ø®Ø·Ø§Ø¨|Ø§Ù„ÙØ§Ø±ÙˆÙ‚ Ø¹Ù…Ø±|Ø¹Ù…Ø± Ø¨Ù† Ø§Ù„Ø®Ø·Ø§Ø¨|Ø¹Ù…Ø±" },
        { term: "Ø¹Ø«Ù…Ø§Ù† Ø¨Ù† Ø¹ÙØ§Ù†",            pattern: "Ø¹Ø«Ù…Ø§Ù† Ø¨Ù† Ø¹ÙØ§Ù†|Ø°Ùˆ Ø§Ù„Ù†ÙˆØ±ÙŠÙ†|Ø¹Ø«Ù…Ø§Ù†" },
        { term: "Ø¹Ù„ÙŠ Ø¨Ù† Ø£Ø¨ÙŠ Ø·Ø§Ù„Ø¨",          pattern: "Ø¹Ù„ÙŠ Ø¨Ù† [Ø£Ø§]Ø¨ÙŠ Ø·Ø§Ù„Ø¨|Ø¹Ù„ÙŠ Ø±Ø¶ÙŠ Ø§Ù„Ù„Ù‡ Ø¹Ù†Ù‡|Ø¹Ù„ÙŠ" },
        { term: "Ø®Ø§Ù„Ø¯ Ø¨Ù† Ø§Ù„ÙˆÙ„ÙŠØ¯",           pattern: "Ø®Ø§Ù„Ø¯ Ø¨Ù† Ø§Ù„ÙˆÙ„ÙŠØ¯|Ø³ÙŠÙ Ø§Ù„Ù„Ù‡ Ø§Ù„Ù…Ø³Ù„ÙˆÙ„|Ø®Ø§Ù„Ø¯" },
        { term: "Ø¨Ù„Ø§Ù„ Ø¨Ù† Ø±Ø¨Ø§Ø­",             pattern: "Ø¨Ù„Ø§Ù„ Ø¨Ù† Ø±Ø¨Ø§Ø­|Ø¨Ù„Ø§Ù„" },
        { term: "Ø£Ø¨Ùˆ Ù‡Ø±ÙŠØ±Ø©",               pattern: "[Ø£Ø§]Ø¨Ùˆ Ù‡Ø±ÙŠØ±[Ø©Ù‡]" },
        { term: "Ø¹Ø¨Ø¯ Ø§Ù„Ù„Ù‡ Ø¨Ù† Ù…Ø³Ø¹ÙˆØ¯",        pattern: "Ø¹Ø¨Ø¯ Ø§Ù„Ù„Ù‡ Ø¨Ù† Ù…Ø³Ø¹ÙˆØ¯|Ø§Ø¨Ù† Ù…Ø³Ø¹ÙˆØ¯" },
        { term: "Ø­Ù…Ø²Ø© Ø¨Ù† Ø¹Ø¨Ø¯ Ø§Ù„Ù…Ø·Ù„Ø¨",       pattern: "Ø­Ù…Ø²[Ø©Ù‡] Ø¨Ù† Ø¹Ø¨Ø¯ Ø§Ù„Ù…Ø·Ù„Ø¨|Ø­Ù…Ø²[Ø©Ù‡]" },
        { term: "Ù…ØµØ¹Ø¨ Ø¨Ù† Ø¹Ù…ÙŠØ±",            pattern: "Ù…ØµØ¹Ø¨ Ø¨Ù† Ø¹Ù…ÙŠØ±|Ù…ØµØ¹Ø¨" },
        { term: "Ø¹Ù…Ø±Ùˆ Ø¨Ù† Ø§Ù„Ø¹Ø§Øµ",            pattern: "Ø¹Ù…Ø±Ùˆ Ø¨Ù† Ø§Ù„Ø¹Ø§Øµ|Ø¹Ù…Ø±Ùˆ" },
        { term: "Ø·Ù„Ø­Ø© Ø¨Ù† Ø¹Ø¨ÙŠØ¯ Ø§Ù„Ù„Ù‡",        pattern: "Ø·Ù„Ø­[Ø©Ù‡] Ø¨Ù† Ø¹Ø¨ÙŠØ¯ Ø§Ù„Ù„Ù‡|Ø·Ù„Ø­[Ø©Ù‡]" },
        { term: "Ø§Ù„Ø²Ø¨ÙŠØ± Ø¨Ù† Ø§Ù„Ø¹ÙˆØ§Ù…",          pattern: "Ø§Ù„Ø²Ø¨ÙŠØ± Ø¨Ù† Ø§Ù„Ø¹ÙˆØ§Ù…|Ø§Ù„Ø²Ø¨ÙŠØ±" },
        { term: "ÙƒØ¹Ø¨ Ø¨Ù† Ø§Ù„Ø£Ø´Ø±Ù",           pattern: "ÙƒØ¹Ø¨ Ø¨Ù† Ø§Ù„Ø£Ø´Ø±Ù|ÙƒØ¹Ø¨" },
        { term: "Ø³Ø¹Ø¯ Ø¨Ù† Ø¹Ø¨Ø§Ø¯Ø©",            pattern: "Ø³Ø¹Ø¯ Ø¨Ù† Ø¹Ø¨Ø§Ø¯[Ø©Ù‡]" },
        { term: "Ø²ÙŠØ¯ Ø¨Ù† Ø­Ø§Ø±Ø«Ø©",            pattern: "Ø²ÙŠØ¯ Ø¨Ù† Ø­Ø§Ø±Ø«[Ø©Ù‡]|Ø²ÙŠØ¯" },
        { term: "Ø³Ù„Ù…Ø§Ù† Ø§Ù„ÙØ§Ø±Ø³ÙŠ",           pattern: "Ø³Ù„Ù…Ø§Ù† Ø§Ù„ÙØ§Ø±Ø³ÙŠ|Ø³Ù„Ù…Ø§Ù†" },
        { term: "Ø³Ø¹Ø¯ Ø¨Ù† Ù…Ø¹Ø§Ø°",             pattern: "Ø³Ø¹Ø¯ Ø¨Ù† Ù…Ø¹Ø§Ø°|Ø³Ø¹Ø¯" },
        { term: "Ø­ÙŠÙŠ Ø¨Ù† Ø£Ø®Ø·Ø¨",             pattern: "Ø­ÙŠÙŠ Ø¨Ù† [Ø£Ø§]Ø®Ø·Ø¨|Ø­ÙŠÙŠ" },
        { term: "Ù†Ø¹ÙŠÙ… Ø¨Ù† Ù…Ø³Ø¹ÙˆØ¯",           pattern: "Ù†Ø¹ÙŠÙ… Ø¨Ù† Ù…Ø³Ø¹ÙˆØ¯|Ù†Ø¹ÙŠÙ…" },
        { term: "Ø¹Ø¨Ø¯ Ø§Ù„Ù„Ù‡ Ø¨Ù† Ø³Ù„Ø§Ù…",         pattern: "Ø¹Ø¨Ø¯ Ø§Ù„Ù„Ù‡ Ø¨Ù† Ø³Ù„Ø§Ù…|Ø§Ø¨Ù† Ø³Ù„Ø§Ù…" },
        { term: "Ø¹Ø¨Ø¯ Ø§Ù„Ù„Ù‡ Ø¨Ù† Ø£Ø¨ÙŠ Ø¨Ù† Ø³Ù„ÙˆÙ„",  pattern: "Ø¹Ø¨Ø¯ Ø§Ù„Ù„Ù‡ Ø¨Ù† [Ø£Ø§]Ø¨ÙŠ Ø¨Ù† Ø³Ù„ÙˆÙ„|Ø§Ø¨Ù† Ø³Ù„ÙˆÙ„|Ø¹Ø¨Ø¯ Ø§Ù„Ù„Ù‡ Ø¨Ù† [Ø£Ø§]Ø¨ÙŠ" },
        { term: "ØµÙÙˆØ§Ù† Ø¨Ù† Ø§Ù„Ù…Ø¹Ø·Ù„",          pattern: "ØµÙÙˆØ§Ù† Ø¨Ù† Ø§Ù„Ù…Ø¹Ø·Ù„|ØµÙÙˆØ§Ù†" },
        { term: "ÙˆØ­Ø´ÙŠ Ø¨Ù† Ø­Ø±Ø¨",             pattern: "ÙˆØ­Ø´ÙŠ Ø¨Ù† Ø­Ø±Ø¨|ÙˆØ­Ø´ÙŠ" },
        { term: "Ø£Ø¨Ùˆ Ø¬Ù‡Ù„",                 pattern: "[Ø£Ø§]Ø¨Ùˆ Ø¬Ù‡Ù„|ÙØ±Ø¹ÙˆÙ† [Ø£Ø§]Ù…Ø©" },
        { term: "Ø£Ø¨Ùˆ Ù„Ù‡Ø¨",                 pattern: "[Ø£Ø§]Ø¨Ùˆ Ù„Ù‡Ø¨" },
        { term: "Ø£Ø¨Ùˆ Ø³ÙÙŠØ§Ù†",               pattern: "[Ø£Ø§]Ø¨Ùˆ Ø³ÙÙŠØ§Ù†|[Ø£Ø§]Ø¨ÙŠ Ø³ÙÙŠØ§Ù†|[Ø£Ø§]Ø¨Ø§ Ø³ÙÙŠØ§Ù†" },
        { term: "Ø£Ù…ÙŠØ© Ø¨Ù† Ø®Ù„Ù",             pattern: "[Ø£Ø§]Ù…ÙŠ[Ø©Ù‡] Ø¨Ù† Ø®Ù„Ù" },
        { term: "Ø§Ù„Ø­Ø³Ù† Ø¨Ù† Ø¹Ù„ÙŠ",            pattern: "Ø§Ù„Ø­Ø³Ù† Ø¨Ù† Ø¹Ù„ÙŠ|Ø§Ù„Ø³Ø¨Ø· Ø§Ù„Ø­Ø³Ù†|Ø§Ù„Ø­Ø³Ù†" },
        { term: "Ø§Ù„Ø­Ø³ÙŠÙ† Ø¨Ù† Ø¹Ù„ÙŠ",           pattern: "Ø§Ù„Ø­Ø³ÙŠÙ† Ø¨Ù† Ø¹Ù„ÙŠ|Ø§Ù„Ø³Ø¨Ø· Ø§Ù„Ø­Ø³ÙŠÙ†|Ø§Ù„Ø­Ø³ÙŠÙ†" },
        { term: "Ø§Ù„Ù†Ø¬Ø§Ø´ÙŠ",                 pattern: "Ø§Ù„Ù†Ø¬Ø§Ø´ÙŠ|Ù†Ø¬Ø§Ø´ÙŠ Ø§Ù„Ø­Ø¨Ø´[Ø©Ù‡]" },
        // â”€â”€ Ù‚Ø¨Ø§Ø¦Ù„ ÙˆØ£Ø­Ø¯Ø§Ø« â”€â”€
        { term: "Ø¨Ù†Ùˆ Ù‚Ø±ÙŠØ¸Ø©",               pattern: "Ø¨Ù†Ùˆ Ù‚Ø±ÙŠØ¸[Ø©Ù‡]|Ø¨Ù†ÙŠ Ù‚Ø±ÙŠØ¸[Ø©Ù‡]" },
        { term: "Ø¨Ù†Ùˆ Ù‚ÙŠÙ†Ù‚Ø§Ø¹",              pattern: "Ø¨Ù†Ùˆ Ù‚ÙŠÙ†Ù‚Ø§Ø¹|Ø¨Ù†ÙŠ Ù‚ÙŠÙ†Ù‚Ø§Ø¹" },
        { term: "Ø¨Ù†Ùˆ Ø§Ù„Ù†Ø¶ÙŠØ±",              pattern: "Ø¨Ù†Ùˆ Ø§Ù„Ù†Ø¶ÙŠØ±|Ø¨Ù†ÙŠ Ø§Ù„Ù†Ø¶ÙŠØ±" },
        { term: "ØºØ²ÙˆØ© Ø§Ù„Ø£Ø­Ø²Ø§Ø¨",            pattern: "ØºØ²Ùˆ[Ø©Ù‡] Ø§Ù„Ø£Ø­Ø²Ø§Ø¨|Ø§Ù„Ø£Ø­Ø²Ø§Ø¨" },
        { term: "Ø¨Ø¯Ø± Ø§Ù„Ù…ÙˆØ¹Ø¯",              pattern: "Ø¨Ø¯Ø± Ø§Ù„Ù…ÙˆØ¹Ø¯" },
        { term: "Ø°Ø§Øª Ø§Ù„Ø±Ù‚Ø§Ø¹",              pattern: "Ø°Ø§Øª Ø§Ù„Ø±Ù‚Ø§Ø¹" },
        { term: "Ø¯ÙˆÙ…Ø© Ø§Ù„Ø¬Ù†Ø¯Ù„",             pattern: "Ø¯ÙˆÙ…[Ø©Ù‡] Ø§Ù„Ø¬Ù†Ø¯Ù„" },
        { term: "ØºØ²ÙˆØ© Ø¨Ù†ÙŠ Ø§Ù„Ù…ØµØ·Ù„Ù‚",        pattern: "ØºØ²Ùˆ[Ø©Ù‡] Ø¨Ù†ÙŠ Ø§Ù„Ù…ØµØ·Ù„Ù‚|Ø¨Ù†ÙŠ Ø§Ù„Ù…ØµØ·Ù„Ù‚|Ø§Ù„Ù…Ø±ÙŠØ³ÙŠØ¹" }
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

// â”€â”€ GLOSSARY & MINDMAP POPUPS â”€â”€
const GLOSSARY = {
    // Ø±Ø¬Ø§Ù„ Ø§Ù„ØµØ­Ø§Ø¨Ø© ÙˆØ§Ù„Ù…Ø¹Ø§ØµØ±ÙˆÙ†
    "Ø²ÙŠØ¯ Ø¨Ù† Ø­Ø§Ø±Ø«Ø©": { def: "ØµØ­Ø§Ø¨ÙŠ Ø¬Ù„ÙŠÙ„ØŒ ÙƒØ§Ù† ÙŠØ¯Ø¹Ù‰ Ø²ÙŠØ¯ Ø¨Ù† Ù…Ø­Ù…Ø¯ Ø¨Ø§Ù„ØªØ¨Ù†ÙŠ Ù‚Ø¨Ù„ ØªØ­Ø±ÙŠÙ…Ù‡ØŒ ÙˆÙ‡Ùˆ Ø§Ù„ØµØ­Ø§Ø¨ÙŠ Ø§Ù„ÙˆØ­ÙŠØ¯ Ø§Ù„Ø°ÙŠ Ø°ÙÙƒØ± Ø§Ø³Ù…Ù‡ ØµØ±Ø§Ø­Ø© ÙÙŠ Ø§Ù„Ù‚Ø±Ø¢Ù† Ø§Ù„ÙƒØ±ÙŠÙ….", type: "person", gender: "male" },
    "Ø£Ø¨Ùˆ Ø³ÙÙŠØ§Ù†": { def: "Ø²Ø¹ÙŠÙ… Ù…Ø´Ø±ÙƒÙŠ Ù‚Ø±ÙŠØ´ ÙˆÙ‚Ø§Ø¦Ø¯ Ù‚ÙˆØ§ÙÙ„Ù‡Ù… ÙˆØ¬ÙŠÙˆØ´Ù‡Ù… ÙÙŠ ØºØ²Ùˆ Ø£Ø­Ø¯ ÙˆØ§Ù„Ø£Ø­Ø²Ø§Ø¨ Ù‚Ø¨Ù„ Ø¥Ø³Ù„Ø§Ù…Ù‡ ÙŠÙˆÙ… ÙØªØ­ Ù…ÙƒØ©.", type: "person", gender: "male" },
    "Ø³Ù„Ù…Ø§Ù† Ø§Ù„ÙØ§Ø±Ø³ÙŠ": { def: "ØµØ­Ø§Ø¨ÙŠ Ø¬Ù„ÙŠÙ„ Ù…Ù† Ø¨Ù„Ø§Ø¯ ÙØ§Ø±Ø³ØŒ ÙˆÙ‡Ùˆ ØµØ§Ø­Ø¨ ÙÙƒØ±Ø© Ø­ÙØ± Ø§Ù„Ø®Ù†Ø¯Ù‚ Ù„Ø­Ù…Ø§ÙŠØ© Ø§Ù„Ù…Ø¯ÙŠÙ†Ø© ÙÙŠ ØºØ²ÙˆØ© Ø§Ù„Ø£Ø­Ø²Ø§Ø¨.", type: "person", gender: "male" },
    "Ø³Ø¹Ø¯ Ø¨Ù† Ù…Ø¹Ø§Ø°": { def: "Ø³ÙŠØ¯ Ø§Ù„Ø£ÙˆØ³ ÙˆØµØ­Ø§Ø¨ÙŠ Ø¬Ù„ÙŠÙ„ Ø§Ù‡ØªØ² Ù„ÙˆÙØ§ØªÙ‡ Ø¹Ø±Ø´ Ø§Ù„Ø±Ø­Ù…Ù†ØŒ ÙˆÙ‡Ùˆ Ø§Ù„Ø°ÙŠ Ø­ÙƒÙ… ÙÙŠ Ø¨Ù†ÙŠ Ù‚Ø±ÙŠØ¸Ø© Ø¨Ø­ÙƒÙ… Ø§Ù„Ù„Ù‡ ÙˆØ±Ø³ÙˆÙ„Ù‡.", type: "person", gender: "male" },
    "Ø­ÙŠÙŠ Ø¨Ù† Ø£Ø®Ø·Ø¨": { def: "Ø²Ø¹ÙŠÙ… Ø¨Ù†ÙŠ Ø§Ù„Ù†Ø¶ÙŠØ± ÙˆØ£Ø­Ø¯ Ø£Ù„Ø¯ Ø£Ø¹Ø¯Ø§Ø¡ Ø§Ù„Ø¥Ø³Ù„Ø§Ù…ØŒ Ø­Ø±Ù‘Ø¶ Ø§Ù„Ø£Ø­Ø²Ø§Ø¨ Ø¶Ø¯ Ø§Ù„Ù…Ø¯ÙŠÙ†Ø© ÙˆØºØ¯Ø± Ø¨Ø§Ù„Ø¹Ù‡Ø¯ Ø«Ù… Ù‚ÙØªÙ„ Ù…Ø¹ Ø¨Ù†ÙŠ Ù‚Ø±ÙŠØ¸Ø©.", type: "person", gender: "male" },
    "Ù†Ø¹ÙŠÙ… Ø¨Ù† Ù…Ø³Ø¹ÙˆØ¯": { def: "ØµØ­Ø§Ø¨ÙŠ Ø¬Ù„ÙŠÙ„ Ø£Ø³Ù„Ù… Ø³Ø±Ù‘Ø§Ù‹ ÙŠÙˆÙ… Ø§Ù„Ø£Ø­Ø²Ø§Ø¨ ÙˆÙ†Ø¬Ø­ Ø¨Ø¯Ù‡Ø§Ø¦Ù‡ ÙÙŠ Ø®Ø°Ù„ Ø§Ù„Ù…Ø´Ø±ÙƒÙŠÙ† ÙˆØ¥ÙŠÙ‚Ø§Ø¹ Ø§Ù„Ø®Ù„Ø§Ù Ø¨ÙŠÙ† Ù‚Ø±ÙŠØ´ ÙˆØ¨Ù†ÙŠ Ù‚Ø±ÙŠØ¸Ø©.", type: "person", gender: "male" },
    "Ø¹Ø¨Ø¯ Ø§Ù„Ù„Ù‡ Ø¨Ù† Ø£Ø¨ÙŠ Ø¨Ù† Ø³Ù„ÙˆÙ„": { def: "Ø±Ø£Ø³ Ø§Ù„Ù†ÙØ§Ù‚ ÙÙŠ Ø§Ù„Ù…Ø¯ÙŠÙ†Ø©ØŒ Ø§Ø³ØªØºÙ„ ØºØ²ÙˆØ© Ø¨Ù†ÙŠ Ø§Ù„Ù…ØµØ·Ù„Ù‚ Ù„Ø¥Ø«Ø§Ø±Ø© Ø§Ù„ÙØªÙ† ÙˆØªÙˆÙ„Ù‰ ÙƒÙØ¨Ø± Ø­Ø§Ø¯Ø«Ø© Ø§Ù„Ø¥ÙÙƒ Ø·Ø¹Ù†Ø§Ù‹ ÙÙŠ Ø£Ù… Ø§Ù„Ù…Ø¤Ù…Ù†ÙŠÙ† Ø¹Ø§Ø¦Ø´Ø©.", type: "person", gender: "male" },
    "ØµÙÙˆØ§Ù† Ø¨Ù† Ø§Ù„Ù…Ø¹Ø·Ù„": { def: "ØµØ­Ø§Ø¨ÙŠ Ø¬Ù„ÙŠÙ„ Ù…Ù† Ø®ÙŠØ±Ø© Ø§Ù„ØµØ­Ø§Ø¨Ø©ØŒ Ø§ØªÙ‡Ù…Ù‡ Ø§Ù„Ù…Ù†Ø§ÙÙ‚ÙˆÙ† Ø¸Ù„Ù…Ø§Ù‹ ÙˆØ²ÙˆØ±Ø§Ù‹ ÙÙŠ Ø­Ø§Ø¯Ø«Ø© Ø§Ù„Ø¥ÙÙƒ ÙˆØ¨Ø±Ø£Ù‡ Ø§Ù„Ù„Ù‡ Ø¹Ø² ÙˆØ¬Ù„ Ø¨Ø¢ÙŠØ§Øª Ø³ÙˆØ±Ø© Ø§Ù„Ù†ÙˆØ±.", type: "person", gender: "male" },
    "Ø£Ù…ÙŠØ© Ø¨Ù† Ø®Ù„Ù": { def: "Ø£Ø­Ø¯ Ø£Ø¦Ù…Ø© Ø§Ù„ÙƒÙØ± Ø¨Ù…ÙƒØ©ØŒ ÙƒØ§Ù† ÙŠØ¹Ø°Ø¨ Ø¨Ù„Ø§Ù„ Ø¨Ù† Ø±Ø¨Ø§Ø­ØŒ ÙˆÙ‚ÙØªÙ„ ÙÙŠ Ù…Ø¹Ø±ÙƒØ© Ø¨Ø¯Ø± Ø§Ù„ÙƒØ¨Ø±Ù‰ Ø¹Ù„Ù‰ ÙŠØ¯ Ø§Ù„Ù…Ø³Ù„Ù…ÙŠÙ†.", type: "person", gender: "male" },
    "Ø­Ù…Ø²Ø© Ø¨Ù† Ø¹Ø¨Ø¯ Ø§Ù„Ù…Ø·Ù„Ø¨": { def: "Ø£Ø³Ø¯ Ø§Ù„Ù„Ù‡ ÙˆØ±Ø³ÙˆÙ„Ù‡ ÙˆØ¹Ù… Ø§Ù„Ù†Ø¨ÙŠ ï·ºØŒ Ø§Ø³ØªØ´Ù‡Ø¯ ÙÙŠ ØºØ²ÙˆØ© Ø£Ø­Ø¯ Ø¹Ù„Ù‰ ÙŠØ¯ ÙˆØ­Ø´ÙŠ ÙˆÙ…Ø«Ù„ Ø§Ù„Ù…Ø´Ø±ÙƒÙˆÙ† Ø¨Ø¬Ø³Ø¯Ù‡ Ø§Ù„Ø´Ø±ÙŠÙ.", type: "person", gender: "male" },
    "Ù…ØµØ¹Ø¨ Ø¨Ù† Ø¹Ù…ÙŠØ±": { def: "Ø£ÙˆÙ„ Ø³ÙÙŠØ± ÙÙŠ Ø§Ù„Ø¥Ø³Ù„Ø§Ù…ØŒ Ø­Ù…Ù„ Ø±Ø§ÙŠØ© Ø§Ù„Ù…Ø³Ù„Ù…ÙŠÙ† ÙÙŠ ØºØ²Ùˆ Ø£ÙØ­Ø¯ ÙˆØ§Ø³ØªØ´Ù‡Ø¯ Ù…Ù‚Ø¨Ù„Ø§Ù‹ ØºÙŠØ± Ù…Ø¯Ø¨Ø± Ø±Ø¶ÙŠ Ø§Ù„Ù„Ù‡ Ø¹Ù†Ù‡.", type: "person", gender: "male" },
    "Ø¹Ø¨Ø¯ Ø§Ù„Ù„Ù‡ Ø¨Ù† Ø³Ù„Ø§Ù…": { def: "Ø­Ø¨Ø± Ù…Ù† Ø£Ø­Ø¨Ø§Ø± ÙŠÙ‡ÙˆØ¯ Ø¨Ù†ÙŠ Ù‚ÙŠÙ†Ù‚Ø§Ø¹ Ø¨Ø§Ù„Ù…Ø¯ÙŠÙ†Ø©ØŒ Ø£Ø³Ù„Ù… Ù…Ø¹ Ø¨Ø¯Ø§ÙŠØ© Ù‡Ø¬Ø±Ø© Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙˆØ´Ù‡Ø¯ Ø¨ØµØ¯Ù‚ Ù†Ø¨ÙˆØªÙ‡ ÙˆÙ‡Ùˆ Ù…Ù† ÙƒØ¨Ø§Ø± Ø§Ù„ØµØ­Ø§Ø¨Ø©.", type: "person", gender: "male" },
    "Ø£Ø¨Ùˆ Ø¨ÙƒØ± Ø§Ù„ØµØ¯ÙŠÙ‚": { def: "Ø£ÙˆÙ„ Ø§Ù„Ø®Ù„ÙØ§Ø¡ Ø§Ù„Ø±Ø§Ø´Ø¯ÙŠÙ† ÙˆØ£Ù‚Ø±Ø¨ Ø§Ù„ØµØ­Ø§Ø¨Ø© Ø¥Ù„Ù‰ Ø§Ù„Ù†Ø¨ÙŠ ï·ºØŒ Ø±ÙÙŠÙ‚Ù‡ ÙÙŠ Ø§Ù„Ù‡Ø¬Ø±Ø© ÙˆØµØ§Ø­Ø¨ Ø§Ù„ØºØ§Ø±ØŒ ÙˆØ£ÙˆÙ„ Ù…Ù† ØµØ¯Ù‘Ù‚ Ø¨Ø§Ù„Ø¥Ø³Ø±Ø§Ø¡ ÙˆØ§Ù„Ù…Ø¹Ø±Ø§Ø¬.", type: "person", gender: "male" },
    "Ø¹Ù…Ø± Ø¨Ù† Ø§Ù„Ø®Ø·Ø§Ø¨": { def: "Ø«Ø§Ù†ÙŠ Ø§Ù„Ø®Ù„ÙØ§Ø¡ Ø§Ù„Ø±Ø§Ø´Ø¯ÙŠÙ†ØŒ Ø§Ù„ÙØ§Ø±ÙˆÙ‚ Ø§Ù„Ø°ÙŠ Ø£Ø¹Ø² Ø§Ù„Ù„Ù‡ Ø¨Ù‡ Ø§Ù„Ø¥Ø³Ù„Ø§Ù…ØŒ Ø¹ÙØ±Ù Ø¨Ø´Ø¯ØªÙ‡ ÙÙŠ Ø§Ù„Ø­Ù‚ ÙˆØ¹Ø¯Ù„Ù‡ Ø§Ù„Ø°ÙŠ Ø¶Ø±Ø¨ Ø¨Ù‡ Ø§Ù„Ø£Ù…Ø«Ø§Ù„ ÙÙŠ ÙƒÙ„ Ù…ÙƒØ§Ù†.", type: "person", gender: "male" },
    "Ø¹Ø«Ù…Ø§Ù† Ø¨Ù† Ø¹ÙØ§Ù†": { def: "Ø«Ø§Ù„Ø« Ø§Ù„Ø®Ù„ÙØ§Ø¡ Ø§Ù„Ø±Ø§Ø´Ø¯ÙŠÙ† ÙˆØ°Ùˆ Ø§Ù„Ù†ÙˆØ±ÙŠÙ†ØŒ Ø²ÙˆØ¬ Ø±Ù‚ÙŠØ© Ø«Ù… Ø£Ù… ÙƒÙ„Ø«ÙˆÙ… Ø¨Ù†ØªÙŽÙŠ Ø§Ù„Ù†Ø¨ÙŠ ï·ºØŒ Ø¬Ù‡Ù‘Ø² Ø¬ÙŠØ´ Ø§Ù„Ø¹Ø³Ø±Ø© Ù…Ù† Ù…Ø§Ù„Ù‡ ÙˆØ¬Ù…Ø¹ Ø§Ù„Ù‚Ø±Ø¢Ù†.", type: "person", gender: "male" },
    "Ø¹Ù„ÙŠ Ø¨Ù† Ø£Ø¨ÙŠ Ø·Ø§Ù„Ø¨": { def: "Ø±Ø§Ø¨Ø¹ Ø§Ù„Ø®Ù„ÙØ§Ø¡ Ø§Ù„Ø±Ø§Ø´Ø¯ÙŠÙ† ÙˆØ§Ø¨Ù† Ø¹Ù… Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙˆØ²ÙˆØ¬ ÙØ§Ø·Ù…Ø© Ø§Ù„Ø²Ù‡Ø±Ø§Ø¡ØŒ Ø£Ø³Ù„Ù… ÙˆÙ‡Ùˆ ØµØºÙŠØ± ÙˆÙƒØ§Ù† Ù…Ù† Ø£Ø´Ø¬Ø¹ ÙØ±Ø³Ø§Ù† Ø§Ù„Ø¥Ø³Ù„Ø§Ù….", type: "person", gender: "male" },
    "Ø®Ø§Ù„Ø¯ Ø¨Ù† Ø§Ù„ÙˆÙ„ÙŠØ¯": { def: "Ø³ÙŠÙ Ø§Ù„Ù„Ù‡ Ø§Ù„Ù…Ø³Ù„ÙˆÙ„ØŒ Ø£Ø³Ù„Ù… Ù‚ÙØ¨ÙŠÙ„ ÙØªØ­ Ù…ÙƒØ© ÙˆÙ‚Ø§Ø¯ Ù…Ø¹Ø§Ø±Ùƒ Ø­Ø§Ø³Ù…Ø© ÙÙŠ Ø§Ù„ÙŠÙ…Ø§Ù…Ø© ÙˆØ§Ù„Ø´Ø§Ù… ÙˆØ§Ù„Ø¹Ø±Ø§Ù‚ ÙˆÙ„Ù… ÙŠÙÙ‡Ø²Ù… ÙÙŠ Ø­Ø±Ø¨ Ù‚Ø·.", type: "person", gender: "male" },
    "Ø¨Ù„Ø§Ù„ Ø¨Ù† Ø±Ø¨Ø§Ø­": { def: "Ø£ÙˆÙ„ Ù…Ø¤Ø°Ù† ÙÙŠ Ø§Ù„Ø¥Ø³Ù„Ø§Ù…ØŒ Ø¹Ø¨Ø¯ Ø­Ø¨Ø´ÙŠ ÙƒØ§Ù† ÙŠØ¹Ø°Ø¨Ù‡ Ø£Ù…ÙŠØ© Ø¨Ù† Ø®Ù„Ù Ø¨Ø§Ù„Ø±Ù…Ø¶Ø§Ø¡ Ù„ÙŠØªØ±Ùƒ Ø¯ÙŠÙ†Ù‡ØŒ Ø­ØªÙ‰ Ø§Ø´ØªØ±Ø§Ù‡ Ø£Ø¨Ùˆ Ø¨ÙƒØ± ÙˆØ£Ø¹ØªÙ‚Ù‡.", type: "person", gender: "male" },
    "Ø£Ø¨Ùˆ Ù‡Ø±ÙŠØ±Ø©": { def: "Ø£ÙƒØ«Ø± Ø§Ù„ØµØ­Ø§Ø¨Ø© Ø±ÙˆØ§ÙŠØ© Ù„Ù„Ø­Ø¯ÙŠØ« Ø§Ù„Ù†Ø¨ÙˆÙŠØŒ Ø£Ø³Ù„Ù… Ø¹Ø§Ù… Ø®ÙŠØ¨Ø± ÙˆØ¸Ù„ Ù…Ù„Ø§Ø²Ù…Ø§Ù‹ Ù„Ù„Ù†Ø¨ÙŠ ï·º Ø­ØªÙ‰ ÙˆÙØ§ØªÙ‡ ÙˆØ±ÙˆÙ‰ Ø£ÙƒØ«Ø± Ù…Ù† Ø®Ù…Ø³Ø© Ø¢Ù„Ø§Ù Ø­Ø¯ÙŠØ«.", type: "person", gender: "male" },
    "Ø¹Ø¨Ø¯ Ø§Ù„Ù„Ù‡ Ø¨Ù† Ù…Ø³Ø¹ÙˆØ¯": { def: "ØµØ­Ø§Ø¨ÙŠ Ù…Ù† Ø£ÙˆØ§Ø¦Ù„ Ø§Ù„Ù…Ø³Ù„Ù…ÙŠÙ†ØŒ Ø®Ø§Ø¯Ù… Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙˆØ£Ø¹Ù„Ù… Ø§Ù„ØµØ­Ø§Ø¨Ø© Ø¨Ø§Ù„Ù‚Ø±Ø¢Ù† Ø§Ù„ÙƒØ±ÙŠÙ… ÙˆØ§Ù„ØªÙØ³ÙŠØ±ØŒ Ù‚Ø§Ù„ Ø¹Ù†Ù‡ Ø§Ù„Ù†Ø¨ÙŠ ï·º: Ù…Ù† Ø³Ø±Ù‡ Ø£Ù† ÙŠÙ‚Ø±Ø£ Ø§Ù„Ù‚Ø±Ø¢Ù† ØºØ¶Ø§Ù‹ ÙÙ„ÙŠÙ‚Ø±Ø£ Ø¹Ù„Ù‰ Ù‚Ø±Ø§Ø¡Ø© Ø§Ø¨Ù† Ø£Ù… Ø¹Ø¨Ø¯.", type: "person", gender: "male" },
    "ÙˆØ­Ø´ÙŠ Ø¨Ù† Ø­Ø±Ø¨": { def: "Ø§Ù„Ø­Ø¨Ø´ÙŠ Ø§Ù„Ø°ÙŠ Ù‚ØªÙ„ Ø­Ù…Ø²Ø© Ø¨Ù† Ø¹Ø¨Ø¯ Ø§Ù„Ù…Ø·Ù„Ø¨ Ø¨Ø£Ù…Ø± Ù‡Ù†Ø¯ ÙŠÙˆÙ… Ø£Ø­Ø¯ØŒ Ø«Ù… Ø£Ø³Ù„Ù… Ø¨Ø¹Ø¯ ÙØªØ­ Ù…ÙƒØ© ÙˆÙ‚ØªÙ„ Ù…Ø³ÙŠÙ„Ù…Ø© Ø§Ù„ÙƒØ°Ø§Ø¨ ÙÙŠ Ø­Ø±ÙˆØ¨ Ø§Ù„Ø±Ø¯Ø©.", type: "person", gender: "male" },
    "Ø¹Ù…Ø±Ùˆ Ø¨Ù† Ø§Ù„Ø¹Ø§Øµ": { def: "ØµØ­Ø§Ø¨ÙŠ ÙˆÙ‚Ø§Ø¦Ø¯ Ø¹Ø³ÙƒØ±ÙŠ Ø¨Ø§Ø±Ø¹ØŒ Ø£Ø³Ù„Ù… Ù‚ÙØ¨ÙŠÙ„ ÙØªØ­ Ù…ÙƒØ© ÙˆÙØªØ­ Ù…ØµØ± ÙÙŠ Ø¹Ù‡Ø¯ Ø¹Ù…Ø± Ø¨Ù† Ø§Ù„Ø®Ø·Ø§Ø¨ Ø±Ø¶ÙŠ Ø§Ù„Ù„Ù‡ Ø¹Ù†Ù‡.", type: "person", gender: "male" },
    "Ø§Ù„Ø­Ø³Ù† Ø¨Ù† Ø¹Ù„ÙŠ": { def: "Ø³Ø¨Ø· Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙˆØ±ÙŠØ­Ø§Ù†ØªÙ‡ØŒ Ø§Ø¨Ù† Ø¹Ù„ÙŠ ÙˆÙØ§Ø·Ù…Ø©ØŒ Ù‚Ø§Ù„ ÙÙŠÙ‡ Ø§Ù„Ù†Ø¨ÙŠ: Ø§Ù„Ø­Ø³Ù† ÙˆØ§Ù„Ø­Ø³ÙŠÙ† Ø³ÙŠØ¯Ø§ Ø´Ø¨Ø§Ø¨ Ø£Ù‡Ù„ Ø§Ù„Ø¬Ù†Ø©.", type: "person", gender: "male" },
    "Ø§Ù„Ø­Ø³ÙŠÙ† Ø¨Ù† Ø¹Ù„ÙŠ": { def: "Ø³Ø¨Ø· Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙˆØ±ÙŠØ­Ø§Ù†ØªÙ‡ØŒ Ø£ÙÙˆÙ„Ø¯ ÙÙŠ Ø§Ù„Ø³Ù†Ø© Ø§Ù„Ø±Ø§Ø¨Ø¹Ø© Ù„Ù„Ù‡Ø¬Ø±Ø©ØŒ ÙˆÙ‚Ø§Ù„ ÙÙŠÙ‡ Ø§Ù„Ù†Ø¨ÙŠ: Ø§Ù„Ø­Ø³ÙŠÙ† Ù…Ù†ÙŠ ÙˆØ£Ù†Ø§ Ù…Ù† Ø§Ù„Ø­Ø³ÙŠÙ†.", type: "person", gender: "male" },
    "Ø§Ù„Ù†Ø¬Ø§Ø´ÙŠ": { def: "Ù…Ù„Ùƒ Ø§Ù„Ø­Ø¨Ø´Ø© Ø§Ù„Ø°ÙŠ Ø£Ø¬Ø§Ø± Ø§Ù„Ù…Ù‡Ø§Ø¬Ø±ÙŠÙ† Ø§Ù„Ø£ÙˆÙ„ÙŠÙ† ÙˆØ£Ù†ØµÙÙ‡Ù…ØŒ Ø£Ø³Ù„Ù… ÙÙŠ Ù‚Ù„Ø¨Ù‡ ÙˆØµÙ„Ù‰ Ø¹Ù„ÙŠÙ‡ Ø§Ù„Ù†Ø¨ÙŠ ï·º ØµÙ„Ø§Ø© Ø§Ù„ØºØ§Ø¦Ø¨ Ù„Ù…Ø§ Ù…Ø§Øª.", type: "person", gender: "male" },
    "Ø£Ø¨Ùˆ Ø¬Ù‡Ù„": { def: "ÙØ±Ø¹ÙˆÙ† Ù‡Ø°Ù‡ Ø§Ù„Ø£Ù…Ø© ÙˆØ§Ø³Ù…Ù‡ Ø¹Ù…Ø±Ùˆ Ø¨Ù† Ù‡Ø´Ø§Ù…ØŒ Ù…Ù† Ø£Ø´Ø¯ Ø£Ø¹Ø¯Ø§Ø¡ Ø§Ù„Ø¥Ø³Ù„Ø§Ù… ÙˆØ£ÙƒØ«Ø±Ù‡Ù… Ø¥ÙŠØ°Ø§Ø¡Ù‹ Ù„Ù„Ù…Ø³Ù„Ù…ÙŠÙ†ØŒ Ù‚ÙØªÙ„ ÙÙŠ ØºØ²ÙˆØ© Ø¨Ø¯Ø± Ø§Ù„ÙƒØ¨Ø±Ù‰.", type: "person", gender: "male" },
    "Ø£Ø¨Ùˆ Ù„Ù‡Ø¨": { def: "Ø¹Ù… Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙˆØ¹Ø¯ÙˆÙ‡ Ø§Ù„Ù„Ø¯ÙˆØ¯ØŒ Ù†Ø²Ù„Øª ÙÙŠÙ‡ ÙˆØ²ÙˆØ¬ØªÙ‡ Ø³ÙˆØ±Ø© Ø§Ù„Ù…Ø³Ø¯ØŒ Ù„Ø¹Ù†Ù‡ Ø§Ù„Ù„Ù‡ Ù„Ø´Ø¯Ø© Ø¹Ø¯Ø§Ø¦Ù‡ Ù„Ù„Ø¥Ø³Ù„Ø§Ù… ÙˆØ±Ø³ÙˆÙ„Ù‡.", type: "person", gender: "male" },
    "Ø³Ø¹Ø¯ Ø¨Ù† Ø¹Ø¨Ø§Ø¯Ø©": { def: "Ø³ÙŠØ¯ Ø§Ù„Ø®Ø²Ø±Ø¬ ÙˆØ²Ø¹ÙŠÙ… Ø§Ù„Ø£Ù†ØµØ§Ø±ØŒ ÙƒØ§Ù† ÙŠÙ†Ø§ÙØ³ Ø³Ø¹Ø¯ Ø¨Ù† Ù…Ø¹Ø§Ø° Ø¹Ù„Ù‰ Ø¥Ù…Ø§Ø±Ø© Ø§Ù„Ø£Ù†ØµØ§Ø± ÙˆØ´Ù‡Ø¯ ØºØ²ÙˆØ§Øª ÙƒØ«ÙŠØ±Ø© Ù…Ø¹ Ø§Ù„Ù†Ø¨ÙŠ ï·º.", type: "person", gender: "male" },
    "Ø·Ù„Ø­Ø© Ø¨Ù† Ø¹Ø¨ÙŠØ¯ Ø§Ù„Ù„Ù‡": { def: "Ø£Ø­Ø¯ Ø§Ù„Ø¹Ø´Ø±Ø© Ø§Ù„Ù…Ø¨Ø´Ø±ÙŠÙ† Ø¨Ø§Ù„Ø¬Ù†Ø©ØŒ ÙˆÙ‚Ù ÙŠÙˆÙ… Ø£ÙØ­Ø¯ Ø¯Ø±Ø¹Ø§Ù‹ Ù„Ù„Ù†Ø¨ÙŠ ï·º ÙˆØ£ØµÙŠØ¨Øª ÙŠØ¯Ù‡ Ø­ÙŠÙ† Ø£Ù†Ù‚Ø°Ù‡ØŒ ÙÙ‚Ø§Ù„ Ø§Ù„Ù†Ø¨ÙŠ: Ø£ÙˆØ¬Ø¨ Ø·Ù„Ø­Ø©.", type: "person", gender: "male" },
    "Ø§Ù„Ø²Ø¨ÙŠØ± Ø¨Ù† Ø§Ù„Ø¹ÙˆØ§Ù…": { def: "Ø£Ø­Ø¯ Ø§Ù„Ø¹Ø´Ø±Ø© Ø§Ù„Ù…Ø¨Ø´Ø±ÙŠÙ† Ø¨Ø§Ù„Ø¬Ù†Ø© ÙˆØ­ÙˆØ§Ø±ÙŠ Ø±Ø³ÙˆÙ„ Ø§Ù„Ù„Ù‡ ï·º ÙˆØ§Ø¨Ù† Ø¹Ù…ØªÙ‡ ØµÙÙŠØ©ØŒ ÙƒØ§Ù† ÙØ§Ø±Ø³Ø§Ù‹ Ø´Ø¬Ø§Ø¹Ø§Ù‹ Ù„Ø§ ÙŠÙØ¨Ø§Ø±Ù‰ ÙÙŠ Ù…ÙŠØ§Ø¯ÙŠÙ† Ø§Ù„Ù‚ØªØ§Ù„.", type: "person", gender: "male" },
    "ÙƒØ¹Ø¨ Ø¨Ù† Ø§Ù„Ø£Ø´Ø±Ù": { def: "Ø²Ø¹ÙŠÙ… ÙŠÙ‡ÙˆØ¯ÙŠ Ù…Ù† Ø¨Ù†ÙŠ Ø§Ù„Ù†Ø¶ÙŠØ±ØŒ Ø­Ø±Ù‘Ø¶ Ø§Ù„Ù…Ø´Ø±ÙƒÙŠÙ† Ø¶Ø¯ Ø§Ù„Ù…Ø³Ù„Ù…ÙŠÙ† ÙˆÙ‡Ø¬Ø§ Ø§Ù„Ù†Ø¨ÙŠ ï·º Ø¨Ø´Ø¹Ø±Ù‡ØŒ ÙØ£Ø°Ù† Ø§Ù„Ù†Ø¨ÙŠ Ø¨Ù‚ØªÙ„Ù‡ ÙÙ†ÙØ° Ø§Ù„Ø£Ù…Ø± Ù…Ø­Ù…Ø¯ Ø¨Ù† Ù…Ø³Ù„Ù…Ø©.", type: "person", gender: "male" },
    // Ù†Ø³Ø§Ø¡ Ø§Ù„ØµØ­Ø§Ø¨Ø© ÙˆØ£Ù…Ù‡Ø§Øª Ø§Ù„Ù…Ø¤Ù…Ù†ÙŠÙ†
    "Ø²ÙŠÙ†Ø¨ Ø¨Ù†Øª Ø¬Ø­Ø´": { def: "Ø£Ù… Ø§Ù„Ù…Ø¤Ù…Ù†ÙŠÙ†ØŒ Ø²ÙˆØ¬Ø© Ø§Ù„Ù†Ø¨ÙŠ ï·ºØŒ ØªØ²ÙˆØ¬Ù‡Ø§ Ø¨Ø£Ù…Ø± Ù…Ù† Ø§Ù„Ù„Ù‡ Ù„Ø¥Ø¨Ø·Ø§Ù„ Ø­ÙƒÙ… Ø§Ù„ØªØ¨Ù†ÙŠ Ø¹Ù…Ù„ÙŠØ§Ù‹ØŒ ÙˆÙƒØ§Ù†Øª ØªÙØ®Ø± Ø¨Ø£Ù† Ø§Ù„Ù„Ù‡ Ø²ÙˆÙ‘Ø¬Ù‡Ø§ Ù…Ù† ÙÙˆÙ‚ Ø³Ø¨Ø¹ Ø³Ù…Ø§ÙˆØ§Øª.", type: "person", gender: "female" },
    "Ø¹Ø§Ø¦Ø´Ø© Ø¨Ù†Øª Ø£Ø¨ÙŠ Ø¨ÙƒØ±": { def: "Ø£Ù… Ø§Ù„Ù…Ø¤Ù…Ù†ÙŠÙ† ÙˆØ­Ø¨ÙŠØ¨Ø© Ø±Ø³ÙˆÙ„ Ø§Ù„Ù„Ù‡ ï·ºØŒ Ø£ÙƒØ«Ø± Ø§Ù„ØµØ­Ø§Ø¨Ø© Ø±ÙˆØ§ÙŠØ© Ù„Ù„Ø­Ø¯ÙŠØ« Ø¨Ø¹Ø¯ Ø£Ø¨ÙŠ Ù‡Ø±ÙŠØ±Ø©ØŒ Ø¨Ø±Ø£Ù‡Ø§ Ø§Ù„Ù„Ù‡ ÙÙŠ Ø§Ù„Ù‚Ø±Ø¢Ù† Ù…Ù† Ø­Ø§Ø¯Ø«Ø© Ø§Ù„Ø¥ÙÙƒ.", type: "person", gender: "female" },
    "Ø®Ø¯ÙŠØ¬Ø© Ø¨Ù†Øª Ø®ÙˆÙŠÙ„Ø¯": { def: "Ø£ÙˆÙ„ Ø£Ù…Ù‡Ø§Øª Ø§Ù„Ù…Ø¤Ù…Ù†ÙŠÙ† ÙˆØ£ÙˆÙ„ Ù…Ù† Ø¢Ù…Ù† Ø¨Ø§Ù„Ù†Ø¨ÙŠ ï·ºØŒ ÙˆÙ‡Ø¨Øª Ù…Ø§Ù„Ù‡Ø§ ÙˆÙ†ÙØ³Ù‡Ø§ Ù„Ù„Ø¯Ø¹ÙˆØ©ØŒ ÙˆØ¨Ø´Ù‘Ø±Ù‡Ø§ Ø§Ù„Ù†Ø¨ÙŠ ï·º Ø¨Ø¨ÙŠØª ÙÙŠ Ø§Ù„Ø¬Ù†Ø© Ù…Ù† Ù‚ØµØ¨ Ù„Ø§ ØµØ®Ø¨ ÙÙŠÙ‡ ÙˆÙ„Ø§ Ù†ØµØ¨.", type: "person", gender: "female" },
    "ÙØ§Ø·Ù…Ø© Ø§Ù„Ø²Ù‡Ø±Ø§Ø¡": { def: "Ø³ÙŠØ¯Ø© Ù†Ø³Ø§Ø¡ Ø§Ù„Ø¹Ø§Ù„Ù…ÙŠÙ† ÙˆØ§Ø¨Ù†Ø© Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙˆØ²ÙˆØ¬Ø© Ø¹Ù„ÙŠ Ø¨Ù† Ø£Ø¨ÙŠ Ø·Ø§Ù„Ø¨ØŒ Ù‚Ø§Ù„ Ø¹Ù†Ù‡Ø§ Ø§Ù„Ù†Ø¨ÙŠ: ÙØ§Ø·Ù…Ø© Ø¨Ø¶Ø¹Ø© Ù…Ù†ÙŠ ÙÙ…Ù† Ø¢Ø°Ø§Ù‡Ø§ ÙÙ‚Ø¯ Ø¢Ø°Ø§Ù†ÙŠ.", type: "person", gender: "female" },
    "Ø£Ù… Ø³Ù„Ù…Ø©": { def: "Ø£Ù… Ø§Ù„Ù…Ø¤Ù…Ù†ÙŠÙ† Ù‡Ù†Ø¯ Ø¨Ù†Øª Ø£Ø¨ÙŠ Ø£Ù…ÙŠØ©ØŒ Ù‡Ø§Ø¬Ø±Øª Ø¥Ù„Ù‰ Ø§Ù„Ø­Ø¨Ø´Ø© Ø«Ù… Ø§Ù„Ù…Ø¯ÙŠÙ†Ø©ØŒ Ø§Ø´ØªÙÙ‡Ø±Øª Ø¨Ø­ÙƒÙ…ØªÙ‡Ø§ ÙˆÙ†ØµØ­Ù‡Ø§ Ù„Ù„Ù†Ø¨ÙŠ ï·º ÙŠÙˆÙ… Ø§Ù„Ø­Ø¯ÙŠØ¨ÙŠØ©.", type: "person", gender: "female" },
    "ØµÙÙŠØ© Ø¨Ù†Øª Ø­ÙŠÙŠ": { def: "Ø£Ù… Ø§Ù„Ù…Ø¤Ù…Ù†ÙŠÙ†ØŒ Ø¨Ù†Øª Ø²Ø¹ÙŠÙ… Ø¨Ù†ÙŠ Ø§Ù„Ù†Ø¶ÙŠØ± Ø­ÙŠÙŠ Ø¨Ù† Ø£Ø®Ø·Ø¨ØŒ ØªØ²ÙˆØ¬Ù‡Ø§ Ø§Ù„Ù†Ø¨ÙŠ ï·º Ø¨Ø¹Ø¯ ØºØ²ÙˆØ© Ø®ÙŠØ¨Ø±ØŒ ÙˆÙƒØ§Ù†Øª ØªØ¯Ø§ÙØ¹ Ø¹Ù† Ø´Ø±Ù Ø§Ù„Ù†Ø¨ÙŠ ï·º Ø¨Ù„Ø³Ø§Ù†Ù‡Ø§.", type: "person", gender: "female" },
    "Ø­ÙØµØ© Ø¨Ù†Øª Ø¹Ù…Ø±": { def: "Ø£Ù… Ø§Ù„Ù…Ø¤Ù…Ù†ÙŠÙ† ÙˆØ§Ø¨Ù†Ø© Ø¹Ù…Ø± Ø¨Ù† Ø§Ù„Ø®Ø·Ø§Ø¨ØŒ Ø§Ø´ØªÙ‡Ø±Øª Ø¨Ø§Ù„ØµÙŠØ§Ù… ÙˆØ§Ù„Ù‚ÙŠØ§Ù…ØŒ ÙˆØ¹Ù†Ø¯Ù‡Ø§ Ø­ÙÙØ¸Øª Ø§Ù„Ù…ØµØ­Ù Ø§Ù„Ø£ÙˆÙ„ Ø§Ù„Ø°ÙŠ Ø¬Ù…Ø¹Ù‡ Ø£Ø¨Ùˆ Ø¨ÙƒØ± Ø±Ø¶ÙŠ Ø§Ù„Ù„Ù‡ Ø¹Ù†Ù‡.", type: "person", gender: "female" },
    "Ø±Ù‚ÙŠØ© Ø¨Ù†Øª Ù…Ø­Ù…Ø¯": { def: "Ø¨Ù†Øª Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙˆØ²ÙˆØ¬Ø© Ø¹Ø«Ù…Ø§Ù† Ø¨Ù† Ø¹ÙØ§Ù†ØŒ Ù‡Ø§Ø¬Ø±Øª Ù…Ø¹Ù‡ Ø¥Ù„Ù‰ Ø§Ù„Ø­Ø¨Ø´Ø© Ø«Ù… Ø§Ù„Ù…Ø¯ÙŠÙ†Ø©ØŒ ÙˆØªÙˆÙÙŠØª ÙŠÙˆÙ… ØºØ²ÙˆØ© Ø¨Ø¯Ø± ÙˆÙ‡Ùˆ ÙÙŠ Ø§Ù„Ù…Ø¹Ø±ÙƒØ©.", type: "person", gender: "female" },
    "Ø£Ù… ÙƒÙ„Ø«ÙˆÙ… Ø¨Ù†Øª Ù…Ø­Ù…Ø¯": { def: "Ø¨Ù†Øª Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙˆØ²ÙˆØ¬Ø© Ø¹Ø«Ù…Ø§Ù† Ø¨Ù† Ø¹ÙØ§Ù† Ø¨Ø¹Ø¯ ÙˆÙØ§Ø© Ø£Ø®ØªÙ‡Ø§ Ø±Ù‚ÙŠØ©ØŒ ÙˆÙ„Ù‡Ø°Ø§ Ø³ÙÙ…ÙŠ Ø¹Ø«Ù…Ø§Ù† Ø¨Ø°ÙŠ Ø§Ù„Ù†ÙˆØ±ÙŠÙ†.", type: "person", gender: "female" },
    "Ø²ÙŠÙ†Ø¨ Ø¨Ù†Øª Ù…Ø­Ù…Ø¯": { def: "Ø£ÙƒØ¨Ø± Ø¨Ù†Ø§Øª Ø§Ù„Ù†Ø¨ÙŠ ï·ºØŒ ØªØ²ÙˆØ¬Øª Ø£Ø¨Ø§ Ø§Ù„Ø¹Ø§Øµ Ø¨Ù† Ø§Ù„Ø±Ø¨ÙŠØ¹ Ù‚Ø¨Ù„ Ø§Ù„Ø¥Ø³Ù„Ø§Ù…ØŒ ÙˆÙ‡Ø§Ø¬Ø±Øª Ø¥Ù„Ù‰ Ø§Ù„Ù…Ø¯ÙŠÙ†Ø© Ø¨Ø¹Ø¯ ØºØ²ÙˆØ© Ø¨Ø¯Ø± ÙˆØªÙˆÙÙŠØª ÙÙŠ Ø§Ù„Ø³Ù†Ø© Ø§Ù„Ø«Ø§Ù…Ù†Ø©.", type: "person", gender: "female" },
    "Ù‡Ù†Ø¯ Ø¨Ù†Øª Ø¹ØªØ¨Ø©": { def: "Ø²ÙˆØ¬Ø© Ø£Ø¨ÙŠ Ø³ÙÙŠØ§Ù† ÙˆØ£Ù… Ù…Ø¹Ø§ÙˆÙŠØ©ØŒ Ø£Ù…Ø±Øª Ø¨Ù‚ØªÙ„ Ø­Ù…Ø²Ø© ÙŠÙˆÙ… Ø£ÙØ­Ø¯ ÙˆØ´Ù‚Øª ØµØ¯Ø±Ù‡ØŒ Ø£Ø³Ù„Ù…Øª ÙŠÙˆÙ… ÙØªØ­ Ù…ÙƒØ© ÙˆØ­Ø³Ù† Ø¥Ø³Ù„Ø§Ù…Ù‡Ø§.", type: "person", gender: "female" },
    "Ø£Ø³Ù…Ø§Ø¡ Ø¨Ù†Øª Ø£Ø¨ÙŠ Ø¨ÙƒØ±": { def: "Ø°Ø§Øª Ø§Ù„Ù†Ø·Ø§Ù‚ÙŠÙ† ÙˆØ£Ø®Øª Ø¹Ø§Ø¦Ø´Ø©ØŒ Ø£Ø¹Ø§Ù†Øª Ø£Ø¨Ø§Ù‡Ø§ ÙˆØ²ÙˆØ¬ Ø£Ø®ØªÙ‡Ø§ Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙÙŠ Ø§Ù„Ù‡Ø¬Ø±Ø© Ø¨Ø­Ù…Ù„ Ø§Ù„Ø²Ø§Ø¯ØŒ ÙˆØ£Ù†Ø¬Ø¨Øª Ø£ÙˆÙ„ Ù…ÙˆÙ„ÙˆØ¯ ÙÙŠ Ø§Ù„Ø¥Ø³Ù„Ø§Ù… Ø¨Ø§Ù„Ù…Ø¯ÙŠÙ†Ø©.", type: "person", gender: "female" },
    "Ù…Ø§Ø±ÙŠØ§ Ø§Ù„Ù‚Ø¨Ø·ÙŠØ©": { def: "Ø£Ù… Ø¥Ø¨Ø±Ø§Ù‡ÙŠÙ… Ø§Ø¨Ù† Ø§Ù„Ù†Ø¨ÙŠ ï·ºØŒ Ø£Ù‡Ø¯Ø§Ù‡Ø§ Ø§Ù„Ù…Ù‚ÙˆÙ‚Ø³ Ù…Ù„Ùƒ Ù…ØµØ± Ø¥Ù„Ù‰ Ø§Ù„Ù†Ø¨ÙŠ ï·ºØŒ ÙˆØªÙˆÙÙŠ Ø§Ø¨Ù†Ù‡Ø§ Ø¥Ø¨Ø±Ø§Ù‡ÙŠÙ… ØµØºÙŠØ±Ø§Ù‹ ÙØ¨ÙƒÙ‰ Ø§Ù„Ù†Ø¨ÙŠ ÙˆÙ‚Ø§Ù„: Ø¥Ù† Ø§Ù„Ø¹ÙŠÙ† ØªØ¯Ù…Ø¹ ÙˆØ§Ù„Ù‚Ù„Ø¨ ÙŠØ­Ø²Ù†.", type: "person", gender: "female" },
    // Ø§Ù„Ø£Ø­Ø¯Ø§Ø« ÙˆØ§Ù„ØºØ²ÙˆØ§Øª
    "Ø¨Ù†Ùˆ Ù‚ÙŠÙ†Ù‚Ø§Ø¹": { def: "Ø£ÙˆÙ„ Ù‚Ø¨Ø§Ø¦Ù„ Ø§Ù„ÙŠÙ‡ÙˆØ¯ Ø¨Ø§Ù„Ù…Ø¯ÙŠÙ†Ø© Ù†Ù‚Ø¶Ø§Ù‹ Ù„Ù„Ø¹Ù‡Ø¯ Ù…Ø¹ Ø§Ù„Ù†Ø¨ÙŠ ï·º Ø¨Ø¹Ø¯ ØºØ²ÙˆØ© Ø¨Ø¯Ø±ØŒ ÙØªÙ… Ø­ØµØ§Ø±Ù‡Ù… ÙˆØ¥Ø¬Ù„Ø§Ø¤Ù‡Ù… Ø¹Ù† Ø§Ù„Ù…Ø¯ÙŠÙ†Ø©.", type: "tribe" },
    "Ø¨Ù†Ùˆ Ù‚Ø±ÙŠØ¸Ø©": { def: "Ø¥Ø­Ø¯Ù‰ Ù‚Ø¨Ø§Ø¦Ù„ Ø§Ù„ÙŠÙ‡ÙˆØ¯ Ø¨Ø§Ù„Ù…Ø¯ÙŠÙ†Ø© Ø§Ù„Ø°ÙŠÙ† ØªØ­Ø§Ù„ÙÙˆØ§ Ù…Ø¹ Ø§Ù„Ø£Ø­Ø²Ø§Ø¨ ÙˆÙ†Ù‚Ø¶ÙˆØ§ Ø¹Ù‡Ø¯Ù‡Ù… Ù…Ø¹ Ø§Ù„Ù…Ø³Ù„Ù…ÙŠÙ†ØŒ ÙØ­ÙÙˆØµØ±ÙˆØ§ ÙˆØ­ÙƒÙ… ÙÙŠÙ‡Ù… Ø³Ø¹Ø¯ Ø¨Ù† Ù…Ø¹Ø§Ø°.", type: "tribe" },
    "Ø¨Ù†Ùˆ Ø§Ù„Ù†Ø¶ÙŠØ±": { def: "Ù‚Ø¨ÙŠÙ„Ø© ÙŠÙ‡ÙˆØ¯ÙŠØ© Ø¨Ø§Ù„Ù…Ø¯ÙŠÙ†Ø© ØªØ¢Ù…Ø±Øª Ø¹Ù„Ù‰ Ù‚ØªÙ„ Ø§Ù„Ù†Ø¨ÙŠ ï·º Ø¨Ù„Ù‚Ø§Ø¡ ØµØ®Ø±Ø©ØŒ ÙØ­Ø§ØµØ±Ù‡Ù… ÙˆØ£Ø¬Ù„Ø§Ù‡Ù… Ø¥Ù„Ù‰ Ø®ÙŠØ¨Ø± ÙˆØ§Ù„Ø´Ø§Ù….", type: "tribe" },
    "Ø¨Ø¯Ø± Ø§Ù„Ù…ÙˆØ¹Ø¯": { def: "ØºØ²ÙˆØ© Ø¨Ø¯Ø± Ø§Ù„ØµØºØ±Ù‰ Ø£Ùˆ Ø§Ù„Ø«Ø§Ù†ÙŠØ©ØŒ Ø®Ø±Ø¬ ÙÙŠÙ‡Ø§ Ø§Ù„Ù…Ø³Ù„Ù…ÙˆÙ† Ù„Ù„Ù‚Ø§Ø¡ Ù‚Ø±ÙŠØ´ ÙÙŠ Ø§Ù„Ø³Ù†Ø© Ø§Ù„Ø±Ø§Ø¨Ø¹Ø© Ù„Ù„Ù‡Ø¬Ø±Ø© ÙˆØªØ±Ø§Ø¬Ø¹ Ø§Ù„Ù…Ø´Ø±ÙƒÙˆÙ† Ø±Ø¹Ø¨Ø§Ù‹.", type: "event" },
    "Ø²ÙƒØ§Ø© Ø§Ù„ÙØ·Ø±": { def: "ØµØ¯Ù‚Ø© ØªØ¬Ø¨ Ø¹Ù„Ù‰ ÙƒÙ„ Ù…Ø³Ù„Ù… Ù‚Ø¨Ù„ ØµÙ„Ø§Ø© Ø¹ÙŠØ¯ Ø§Ù„ÙØ·Ø± Ø·Ù‡Ø±Ø© Ù„Ù„ØµØ§Ø¦Ù… ÙˆØ·Ø¹Ù…Ø© Ù„Ù„Ù…Ø³Ø§ÙƒÙŠÙ†ØŒ ÙØ±Ø¶Øª ÙÙŠ Ø´Ø¹Ø¨Ø§Ù† Ù…Ù† Ø§Ù„Ø³Ù†Ø© Ø§Ù„Ø«Ø§Ù†ÙŠØ© Ù„Ù„Ù‡Ø¬Ø±Ø©.", type: "concept" },
    "Ø§Ù„ØªØ¨Ù†ÙŠ": { def: "Ø§Ø¯Ø¹Ø§Ø¡ Ø¨Ù†ÙˆØ© Ø·ÙÙ„ Ù„ØºÙŠØ± Ø£Ø¨ÙŠÙ‡ Ø§Ù„Ø­Ù‚ÙŠÙ‚ÙŠØŒ ÙˆÙ‚Ø¯ Ø£Ø¨Ø·Ù„Ù‡ Ø§Ù„Ø¥Ø³Ù„Ø§Ù… Ø¹Ù…Ù„ÙŠØ§Ù‹ ÙˆÙ†Ø¸Ø±ÙŠØ§Ù‹ Ù„ØµÙŠØ§Ù†Ø© Ø§Ù„Ø£Ù†Ø³Ø§Ø¨ Ù…Ù† Ø§Ù„Ø¶ÙŠØ§Ø¹.", type: "concept" },
    "Ø°Ø§Øª Ø§Ù„Ø±Ù‚Ø§Ø¹": { def: "ØºØ²ÙˆØ© Ø³ÙÙ…ÙŠØª Ø¨Ø°Ù„Ùƒ Ù„Ø£Ù† Ø§Ù„ØµØ­Ø§Ø¨Ø© Ø±Ø¶ÙŠ Ø§Ù„Ù„Ù‡ Ø¹Ù†Ù‡Ù… Ù„ÙÙˆØ§ Ø§Ù„Ø®Ø±Ù‚ Ø¹Ù„Ù‰ Ø£Ù‚Ø¯Ø§Ù…Ù‡Ù… Ù…Ù† Ø´Ø¯Ø© Ø§Ù„Ø­Ø± ÙˆØ§Ù„Ù…Ø´ÙŠØŒ ÙˆÙ†Ø²Ù„Øª ÙÙŠÙ‡Ø§ Ø±Ø®Øµ ÙƒØµÙ„Ø§Ø© Ø§Ù„Ø®ÙˆÙ ÙˆØ§Ù„ØªÙŠÙ…Ù….", type: "event" },
    "ØºØ²ÙˆØ© Ø§Ù„Ø£Ø­Ø²Ø§Ø¨": { def: "ØºØ²ÙˆØ© Ø§Ù„Ø®Ù†Ø¯Ù‚ (Ø§Ù„Ø³Ù†Ø© Ø§Ù„Ø®Ø§Ù…Ø³Ø© Ù„Ù„Ù‡Ø¬Ø±Ø©) Ø­ÙŠØ« ØªØ¬Ù…Ø¹Øª Ù‚Ø¨Ø§Ø¦Ù„ Ø§Ù„Ù…Ø´Ø±ÙƒÙŠÙ† ÙˆØ§Ù„ÙŠÙ‡ÙˆØ¯ Ù„Ù…Ø­Ø§ØµØ±Ø© Ø§Ù„Ù…Ø³Ù„Ù…ÙŠÙ†ØŒ ÙÙ‡Ø²Ù…Ù‡Ù… Ø§Ù„Ù„Ù‡ Ø¨Ø§Ù„Ø±ÙŠØ­ ÙˆØ§Ù„Ø¬Ù†ÙˆØ¯.", type: "event" },
    "ØºØ²ÙˆØ© Ø¨Ù†ÙŠ Ø§Ù„Ù…ØµØ·Ù„Ù‚": { def: "ØºØ²ÙˆØ© Ø§Ù„Ù…Ø±ÙŠØ³ÙŠØ¹ (Ø§Ù„Ø³Ù†Ø© Ø§Ù„Ø³Ø§Ø¯Ø³Ø© Ù„Ù„Ù‡Ø¬Ø±Ø©) Ù‡Ø²Ù… ÙÙŠÙ‡Ø§ Ø§Ù„Ù…Ø³Ù„Ù…ÙˆÙ† Ø¨Ù†ÙŠ Ø§Ù„Ù…ØµØ·Ù„Ù‚ ÙˆØ­Ø¯Ø«Øª ÙÙŠÙ‡Ø§ Ø­Ø§Ø¯Ø«Ø© Ø§Ù„Ø¥ÙÙƒ Ø§Ù„Ù…ÙØªØ±ÙŠØ©.", type: "event" },
    "Ø¯ÙˆÙ…Ø© Ø§Ù„Ø¬Ù†Ø¯Ù„": { def: "ØºØ²ÙˆØ© Ù‚Ø§Ø¯Ù‡Ø§ Ø§Ù„Ù†Ø¨ÙŠ ï·º ÙÙŠ Ø§Ù„Ø³Ù†Ø© Ø§Ù„Ø®Ø§Ù…Ø³Ø© Ù„Ù„Ù‡Ø¬Ø±Ø© Ù„ØªØ£Ù…ÙŠÙ† Ø§Ù„Ø­Ø¯ÙˆØ¯ Ø§Ù„Ø´Ù…Ø§Ù„ÙŠØ© ÙˆØªÙØ±ÙŠÙ‚ Ù‚Ø¨Ø§Ø¦Ù„ Ù‡Ù†Ø§Ùƒ ÙƒØ§Ù†Øª ØªØªÙ‡ÙŠØ£ Ù„ØºØ²Ùˆ Ø§Ù„Ù…Ø¯ÙŠÙ†Ø©.", type: "event" }
};

function showGlossaryPopup(event, term) {
    if (event) event.stopPropagation();
    const item = GLOSSARY[term];
    if (!item) return;
    
    let icon = 'ðŸ“Œ';
    let color = '#4f46e5';
    let termColor = 'var(--primary)';
    
    if (item.type === 'person') {
        if (item.gender === 'female') {
            icon = 'â™€ï¸'; color = '#ec4899'; termColor = '#be185d';
        } else {
            icon = 'â™‚ï¸'; color = '#3b82f6'; termColor = '#1d4ed8';
        }
    } else if (item.type === 'event') {
        icon = 'âš”ï¸'; color = '#10b981'; termColor = '#047857';
    } else if (item.type === 'tribe') {
        icon = 'ðŸ¹'; color = '#7c3aed'; termColor = '#6d28d9';
    } else if (item.type === 'concept') {
        icon = 'ðŸ’¡'; color = '#f59e0b'; termColor = '#b45309';
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

// â”€â”€ MIND MAP POPUP â”€â”€
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

// â”€â”€â”€ AI SUPPORT ENGINE â”€â”€â”€
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
            alert('Ø§Ù„Ø±Ø¬Ø§Ø¡ ÙƒØªØ§Ø¨Ø© Ø§Ù„Ø³Ø¤Ø§Ù„ Ø£Ùˆ Ø§Ù„Ø§Ø³ØªÙØ³Ø§Ø± Ø£ÙˆÙ„Ø§Ù‹');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Ø¬Ø§Ø±ÙŠ Ø§Ù„ØªØ­Ù„ÙŠÙ„ Ø¨Ø§Ù„Ø°ÙƒØ§Ø¡ Ø§Ù„Ø§ØµØ·Ù†Ø§Ø¹ÙŠ... â³</span>';
        responseBox.style.display = 'block';
        badgeEl.textContent = 'ðŸ” Ø¬Ø§Ø±ÙŠ ØªØ­Ù„ÙŠÙ„ ÙˆØªØµÙ†ÙŠÙ Ø§Ù„Ø³Ø¤Ø§Ù„...';
        suggestionsEl.innerHTML = '';
        ticketConfEl.style.display = 'none';

        // 1. Detect Category automatically
        let category = 'Ø¹Ø§Ù…';
        if (text.match(/ÙÙŠØ¯ÙŠÙˆ|ØªØ·Ø¨ÙŠÙ‚|Ø¨Ø·ÙŠØ¡|Ø®Ø·Ø£|Ù„Ø§ ÙŠØ¹Ù…Ù„|Ù…Ø´ÙƒÙ„Ø©|Ø´Ø§Ø´Ø©/i)) {
            category = 'ðŸ› ï¸ Ù…Ø´ÙƒÙ„Ø© ØªÙ‚Ù†ÙŠØ©';
        } else if (text.match(/ØµÙ„Ø§Ø©|ÙˆØ¶ÙˆØ¡|ÙÙ‚Ù‡|ØµÙŠØ§Ù…|Ø·Ù‡Ø§Ø±Ø©|Ø¥Ù…Ø§Ù…|Ø²ÙƒØ§Ø©/i)) {
            category = 'âš–ï¸ Ø§Ù„ÙÙ‚Ù‡ Ø§Ù„Ø¥Ø³Ù„Ø§Ù…ÙŠ';
        } else if (text.match(/ØªØ¬ÙˆÙŠØ¯|Ø£Ø­ÙƒØ§Ù…|Ù†ÙˆÙ†|Ø¥Ø¸Ù‡Ø§Ø±|Ø¥Ø¯ØºØ§Ù…|Ù…Ø®Ø±Ø¬/i)) {
            category = 'ðŸ“– Ø£Ø­ÙƒØ§Ù… Ø§Ù„ØªØ¬ÙˆÙŠØ¯';
        } else if (text.match(/Ø³ÙŠØ±Ø©|ØºØ²ÙˆØ©|Ø±Ø³ÙˆÙ„|Ù†Ø¨ÙŠ|ØµØ­Ø§Ø¨ÙŠ/i)) {
            category = 'ðŸ“œ Ø§Ù„Ø³ÙŠØ±Ø© Ø§Ù„Ù†Ø¨ÙˆÙŠØ©';
        }

        setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>ØªØ­Ù„ÙŠÙ„ Ø§Ù„Ø³Ø¤Ø§Ù„ Ø¨ÙˆØ§Ø³Ø·Ø© Ø§Ù„Ø°ÙƒØ§Ø¡ Ø§Ù„Ø§ØµØ·Ù†Ø§Ø¹ÙŠ âœ¨</span>';

            if (isPrivateInput.checked) {
                badgeEl.textContent = `ðŸ”’ Ø³Ø¤Ø§Ù„ Ø®Ø§Øµ / Ø´Ø®ØµÙŠ - ${category}`;
                suggestionsEl.innerHTML = `
                    <p style="color:var(--text-2); font-size:14px;">ØªÙ… Ø§Ù„Ù‚ÙÙ„ Ø¹Ù„Ù‰ Ø³Ø¤Ø§Ù„Ùƒ ÙƒØ³Ø¤Ø§Ù„ Ø´Ø®ØµÙŠ/Ø®Ø§Øµ. ØªÙ…Øª Ø¥Ø­Ø§Ù„Ø© Ø§Ù„Ø³Ø¤Ø§Ù„ Ù…Ø¨Ø§Ø´Ø±Ø© Ø¥Ù„Ù‰ Ø¥Ø¯Ø§Ø±Ø© Ø§Ù„Ø£ÙƒØ§Ø¯ÙŠÙ…ÙŠØ© Ù„Ù„Ø­ÙØ§Ø¸ Ø¹Ù„Ù‰ Ø®ØµÙˆØµÙŠØªÙƒ.</p>
                `;
                ticketConfEl.style.display = 'block';
            } else {
                badgeEl.textContent = `ðŸŽ¯ Ø§Ù„ØªØµÙ†ÙŠÙ Ø§Ù„ØªÙ„Ù‚Ø§Ø¦ÙŠ: ${category}`;
                suggestionsEl.innerHTML = `
                    <h4 style="margin: 0 0 10px 0; color:var(--text); font-size:15px;">ðŸ’¡ Ø¥Ø¬Ø§Ø¨Ø© Ù…Ù‚ØªØ±Ø­Ø© Ù…Ù† Ø§Ù„Ø£Ø±Ø´ÙŠÙ / Ø§Ù„ØªÙ„Ø®ÙŠØµ:</h4>
                    <div style="background:var(--bg); border-right:4px solid var(--primary); padding:12px; border-radius:8px; font-size:14px; color:var(--text-2); line-height:1.6; margin-bottom:12px;">
                        Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ ØªÙØ±ÙŠØº Ø§Ù„Ø¯Ø±ÙˆØ³ Ø§Ù„Ù…ØªØ¹Ù„Ù‚Ø© Ø¨Ù€ <strong>${category}</strong>: ÙŠØªÙ… Ù…Ø±Ø§Ø¬Ø¹Ø© Ø§Ù„Ù…Ø³Ø£Ù„Ø© Ø¨Ø­Ø³Ø¨ Ø§Ù„Ø´Ø±ÙˆØ· Ø§Ù„Ù…Ø°ÙƒÙˆØ±Ø© ÙÙŠ Ø§Ù„Ø´Ø±Ø­ØŒ ÙˆØ¥Ø°Ø§ ÙƒØ§Ù† Ø§Ù„Ø³Ø¤Ø§Ù„ Ø¯Ù‚ÙŠÙ‚Ø§Ù‹ ÙŠÙ…ÙƒÙ†Ùƒ ØªØ£ÙƒÙŠØ¯ Ø¥Ø±Ø³Ø§Ù„Ù‡ Ù„Ù„Ø¥Ø¯Ø§Ø±Ø©.
                    </div>
                    <div style="display:flex; gap:10px;">
                        <button onclick="alert('Ø§Ù„Ø­Ù…Ø¯ Ù„Ù„Ù‡! Ø³Ø¹Ø¯Ø§Ø¡ Ø¨Ø®Ø¯Ù…ØªÙƒ.')" style="flex:1; padding:10px; background:#dcfce7; color:#166534; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Ø¥Ø¬Ø§Ø¨Ø© ÙˆØ§Ø¶Ø­Ø© ðŸ‘</button>
                        <button onclick="document.getElementById('support-ticket-confirmation').style.display='block'" style="flex:1; padding:10px; background:var(--primary-light); color:var(--primary); border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Ø¥Ø±Ø³Ø§Ù„ Ù„Ù„Ø¥Ø¯Ø§Ø±Ø© ðŸ“©</button>
                    </div>
                `;
            }
        }, 800);
    }
};

// â”€â”€â”€ SPA TAB LOGIC â”€â”€â”€
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

// â”€â”€â”€ PROGRESS LOGIC â”€â”€â”€
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
            recentContainer.innerHTML = '<p style="color:var(--text-3); font-size:14px;">Ù„Ù… ØªÙØªØ­ Ø£ÙŠ Ø¯Ø±Ø³ Ø¨Ø¹Ø¯.</p>';
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
                    btn.innerHTML = `<span style="font-size:20px;">ðŸ“˜</span> <div><h4 style="margin:0; font-size:15px;">${lessonObj.title}</h4><span style="font-size:12px; color:var(--text-2);">${lessonObj.subjectLabel}</span></div>`;
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

// â”€â”€â”€ SEARCH LOGIC â”€â”€â”€
function buildIndex() {
    const stop = new Set(["ÙÙŠ","Ù…Ù†","Ø¹Ù„Ù‰","Ø¥Ù„Ù‰","Ø¹Ù†","Ù‡Ø°Ø§","Ù‡Ø°Ù‡","Ø§Ù„ØªÙŠ","Ø§Ù„Ø°ÙŠ","Ø£Ù†","Ø¥Ù†","Ù„Ø§","Ù…Ø§","Ù…Ø¹","ÙƒØ§Ù†","ÙƒØ§Ù†Øª","Ø«Ù…","Ø£Ùˆ","Ø£Ù…","ÙƒÙ„","ÙŠÙˆÙ…","Ø¨Ø¹Ø¯","Ù‚Ø¨Ù„","Ø¹Ù†Ø¯","Ù‡Ùˆ","Ù‡ÙŠ","ÙˆÙ‚Ø¯","Ù‚Ø¯","ÙÙ‚Ø¯","ÙˆÙ‡Ùˆ","ÙˆÙ‡ÙŠ","ÙˆÙƒØ§Ù†"]);
    const seen = new Set();
    DB.forEach(item => {
        ((item.full_text||'')+' '+(item.blocks_search_text||'')).split(/[\sØŒ.ØŸ!():Ø›]+/).forEach(w=>{
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
        resContainer.innerHTML = `<div class="empty-state"><p style="color:var(--text-3);">Ù„Ø§ ØªÙˆØ¬Ø¯ Ù†ØªØ§Ø¦Ø¬</p></div>`;
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
                        â± ${formatSeconds(b.start_seconds)}
                    </div>
                </div>
            </div>
        </div>`;
    });
    resContainer.innerHTML = html;
}

function resetSearch() {
    const res = document.getElementById('search-results');
    if(res) res.innerHTML = `<div class="empty-state"><p style="color:var(--text-3);">Ø§ÙƒØªØ¨ ÙƒÙ„Ù…Ø© Ù„Ù„Ø¨Ø­Ø«</p></div>`;
}

function openSearchResult(subject, lessonNum, startTime) {
    const lesson = DB.find(l => l.subject === subject && l.lessonNum === lessonNum);
    if(lesson) {
        if (startTime !== null) pendingSeekTime = startTime;
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
                stickyToggleBtn.setAttribute('title', 'DÃ©sÃ©pingler la vidÃ©o');
            } else {
                videoWrapper.style.display = 'none';
                stickyToggleBtn.style.background = 'var(--primary)';
                stickyToggleBtn.style.color = 'white';
                stickyToggleBtn.setAttribute('title', 'Ã‰pingler la vidÃ©o');
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

    title.textContent = 'Ø§Ù„Ø¯Ø±Ø³ ' + l.lessonNum + ' - ' + (l.title || l.subjectLabel || l.subject);

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
                <div class="preview-checkbox ${isComp ? 'checked' : ''}" onclick="togglePreviewChapter(event, '${l.subject}', ${l.lessonNum}, ${idx}, this.parentElement)">${isComp ? 'âœ“' : ''}</div>
                <div class="preview-chapter-info" style="margin-right: 12px; text-align: right; cursor: pointer; flex: 1;" onclick="startLessonFromChapter('${l.subject}', ${l.lessonNum}, ${b.start_seconds})">
                    <div class="preview-chapter-title" style="transition: color 0.2s;">${idx + 1}. ${b.title}</div>
                </div>
            </div>`;
        });
    } else {
        html = '<div style="text-align:center; color:var(--text-2); padding: 20px;">Ù„Ø§ ØªÙˆØ¬Ø¯ Ù…Ø­Ø§ÙˆØ± Ù…ØªØ§Ø­Ø©</div>';
    }
    list.innerHTML = html;

    if (l.thematic_blocks && l.thematic_blocks.length > 0) {
        if (totalCompleted === 0) {
            startBtn.innerHTML = `ðŸ“– Ø§Ø¨Ø¯Ø£ Ø§Ù„Ù‚Ø±Ø§Ø¡Ø©`;
        } else if (totalCompleted === l.thematic_blocks.length) {
            startBtn.innerHTML = `ðŸ”„ Ø£Ø¹Ø¯ Ù‚Ø±Ø§Ø¡Ø© Ø§Ù„Ø¯Ø±Ø³`;
        } else {
            startBtn.innerHTML = `â–¶ï¸ Ø§Ø³ØªØ¦Ù†Ø§Ù (Ø§Ù„Ù…Ø­ÙˆØ± ${firstUnreadIdx + 1})`;
        }
    } else {
        startBtn.innerHTML = `ðŸ“– Ø§Ø¨Ø¯Ø£ Ø§Ù„Ù‚Ø±Ø§Ø¡Ø©`;
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
        cb.textContent = 'âœ“';
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

// â”€â”€â”€ QUIZ ENGINE (PRACTICE TAB) â”€â”€â”€
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
            if(cat === 'ØªÙ‚Ù†ÙŠØ©') {
                subText = 'Ù‡Ù„ Ø§Ù„Ù…Ø´ÙƒÙ„Ø© Ù…ØªØ¹Ù„Ù‚Ø© Ø¨Ù€:';
                subBtns = `
                    <button onclick="supportFlow.selectSubcategory('Ø§Ù„ÙÙŠØ¯ÙŠÙˆ Ù„Ø§ ÙŠØ¹Ù…Ù„')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ø§Ù„ÙÙŠØ¯ÙŠÙˆ Ù„Ø§ ÙŠØ¹Ù…Ù„</button>
                    <button onclick="supportFlow.selectSubcategory('Ù„Ø§ ÙŠÙˆØ¬Ø¯ ØµÙˆØª')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ù„Ø§ ÙŠÙˆØ¬Ø¯ ØµÙˆØª</button>
                    <button onclick="supportFlow.selectSubcategory('Ù…Ø´ÙƒÙ„Ø© ÙÙŠ Ø§Ù„ØªØ·Ø¨ÙŠÙ‚')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ù…Ø´ÙƒÙ„Ø© ÙÙŠ Ø§Ù„ØªØ·Ø¨ÙŠÙ‚</button>
                `;
            } else if(cat === 'Ø¥Ø¯Ø§Ø±ÙŠØ©') {
                subText = 'Ø§Ù„Ù…Ø±Ø¬Ùˆ ØªØ­Ø¯ÙŠØ¯ Ø§Ù„Ù…Ø´ÙƒÙ„Ø©:';
                subBtns = `
                    <button onclick="supportFlow.selectSubcategory('ØªØ¬Ø¯ÙŠØ¯ Ø§Ù„Ø§Ø´ØªØ±Ø§Ùƒ')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">ØªØ¬Ø¯ÙŠØ¯ Ø§Ù„Ø§Ø´ØªØ±Ø§Ùƒ</button>
                    <button onclick="supportFlow.selectSubcategory('Ù…Ø´ÙƒÙ„Ø© ÙÙŠ Ø§Ù„Ø¯ÙØ¹')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ù…Ø´ÙƒÙ„Ø© ÙÙŠ Ø§Ù„Ø¯ÙØ¹</button>
                `;
            } else {
                subText = 'Ù‡Ù„ Ø§Ù„Ù…Ø´ÙƒÙ„Ø© ÙÙŠ:';
                subBtns = `
                    <button onclick="supportFlow.selectSubcategory('ÙÙ‡Ù… Ø§Ù„Ø¯Ø±Ø³')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">ÙÙ‡Ù… Ø§Ù„Ø¯Ø±Ø³</button>
                    <button onclick="supportFlow.selectSubcategory('Ø³Ø¤Ø§Ù„ Ø­ÙˆÙ„ Ø§Ù„Ø§Ø®ØªØ¨Ø§Ø±')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">Ø³Ø¤Ø§Ù„ Ø­ÙˆÙ„ Ø§Ù„Ø§Ø®ØªØ¨Ø§Ø±</button>
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
            if (sub === 'Ø§Ù„ÙÙŠØ¯ÙŠÙˆ Ù„Ø§ ÙŠØ¹Ù…Ù„' || sub === 'Ù„Ø§ ÙŠÙˆØ¬Ø¯ ØµÙˆØª') {
                tip = 'ðŸ’¡ Ù†ØµÙŠØ­Ø© Ø³Ø±ÙŠØ¹Ø©: 90% Ù…Ù† Ù…Ø´Ø§ÙƒÙ„ Ø§Ù„ÙÙŠØ¯ÙŠÙˆ ØªÙØ­Ù„ Ø¨Ù…Ø¬Ø±Ø¯ ØªØ­Ø¯ÙŠØ« Ø§Ù„ØµÙØ­Ø© Ø£Ùˆ Ù…Ø³Ø­ Ø°Ø§ÙƒØ±Ø© Ø§Ù„ØªØ®Ø²ÙŠÙ† Ø§Ù„Ù…Ø¤Ù‚Øª (Cache). Ù‡Ù„ ØªØ±ÙŠØ¯ ØªØ¬Ø±Ø¨Ø© Ø°Ù„ÙƒØŸ<br><br>';
            } else if (sub === 'Ù…Ø´ÙƒÙ„Ø© ÙÙŠ Ø§Ù„Ø¯ÙØ¹' || sub === 'ØªØ¬Ø¯ÙŠØ¯ Ø§Ù„Ø§Ø´ØªØ±Ø§Ùƒ') {
                tip = 'ðŸ’¡ Ù…Ù„Ø§Ø­Ø¸Ø©: ØªÙØ¹ÙŠÙ„ Ø§Ù„Ø§Ø´ØªØ±Ø§ÙƒØ§Øª Ù‚Ø¯ ÙŠØ£Ø®Ø° Ù…Ø§ Ø¨ÙŠÙ† 5 Ø¥Ù„Ù‰ 15 Ø¯Ù‚ÙŠÙ‚Ø© Ù„Ù„Ø¸Ù‡ÙˆØ± ÙÙŠ Ø§Ù„ØªØ·Ø¨ÙŠÙ‚ Ø¨Ø¹Ø¯ Ø§Ù„Ø¯ÙØ¹.<br><br>';
            } else if (sub === 'ÙÙ‡Ù… Ø§Ù„Ø¯Ø±Ø³') {
                tip = 'ðŸ’¡ Ù‡Ù„ ØªØ¹Ù„Ù…ØŸ ÙŠÙ…ÙƒÙ†Ùƒ Ø§Ø³ØªØ®Ø¯Ø§Ù… "Ø§Ù„Ø®Ø±ÙŠØ·Ø© Ø§Ù„Ø°Ù‡Ù†ÙŠØ©" Ø£Ùˆ "Ù…Ù„Ø®Øµ Ø§Ù„Ø¯Ø±Ø³" Ø§Ù„Ù…ØªÙˆÙØ±Ø© ÙÙŠ Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ø¯Ø±Ø³ Ù„Ù„Ø­ØµÙˆÙ„ Ø¹Ù„Ù‰ ÙÙƒØ±Ø© Ø£ÙˆØ¶Ø­ Ù‚Ø¨Ù„ Ø·Ø±Ø­ Ø§Ù„Ø³Ø¤Ø§Ù„.<br><br>';
            }
            
            this.addMessage(tip + 'Ø¥Ø°Ø§ ÙƒØ§Ù†Øª Ø§Ù„Ù…Ø´ÙƒÙ„Ø© Ù…Ø³ØªÙ…Ø±Ø©ØŒ ÙŠØ±Ø¬Ù‰ ÙƒØªØ§Ø¨Ø© Ø§Ù„ØªÙØ§ØµÙŠÙ„ Ø£Ø¯Ù†Ø§Ù‡:', 'bot');
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
                    <span style="font-size: 12px; color: #6b7280; margin-right: 8px;">Ø¬Ø§Ø±ÙŠ Ø§Ù„Ø¨Ø­Ø« ÙÙŠ Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª...</span>
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
        const msg = `Ù„Ù„Ø£Ø³Ù Ù„Ù… Ø£Ø¬Ø¯ Ø¥Ø¬Ø§Ø¨Ø© Ù…Ø¨Ø§Ø´Ø±Ø© Ù„Ù…Ø´ÙƒÙ„ØªÙƒ. ÙŠÙ…ÙƒÙ†Ùƒ ØªØµÙØ­ Ø§Ù„Ø£Ø³Ø¦Ù„Ø© Ø§Ù„Ø´Ø§Ø¦Ø¹Ø© Ø£Ø¯Ù†Ø§Ù‡. Ø¥Ø°Ø§ Ù„Ù… ØªØ¬Ø¯ Ø­Ù„Ø§Ù‹ØŒ ÙŠÙ…ÙƒÙ†Ùƒ ØªØ­ÙˆÙŠÙ„ Ø·Ù„Ø¨Ùƒ Ù„Ù„Ø¥Ø¯Ø§Ø±Ø©.`;
        this.addMessage(msg, 'bot');
        
        const faqs = `
            <div style="background: white; border-radius: 12px; padding: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); align-self: flex-start; width: 100%; max-width: 90%; margin-top: 5px;">
                <details style="padding: 8px; border-bottom: 1px solid #f3f4f6;">
                    <summary style="font-weight: bold; cursor: pointer; color: var(--text-1);">ÙƒÙŠÙ Ø£Ù‚ÙˆÙ… Ø¨ØªØ´ØºÙŠÙ„ Ø§Ù„ÙÙŠØ¯ÙŠÙˆØŸ</summary>
                    <p style="margin-top: 8px; font-size: 13px; color: var(--text-2);">ØªØ£ÙƒØ¯ Ù…Ù† Ø§ØªØµØ§Ù„Ùƒ Ø¨Ø§Ù„Ø¥Ù†ØªØ±Ù†Øª ÙˆØ§Ø¶ØºØ· Ø¹Ù„Ù‰ Ø²Ø± Ø§Ù„ØªØ´ØºÙŠÙ„ ÙÙŠ Ù…Ù†ØªØµÙ Ø§Ù„Ø´Ø§Ø´Ø©.</p>
                </details>
                <details style="padding: 8px; border-bottom: 1px solid #f3f4f6;">
                    <summary style="font-weight: bold; cursor: pointer; color: var(--text-1);">ÙƒÙŠÙ Ø£Ø¹ÙˆØ¯ Ù„Ù„ØµÙØ­Ø© Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ©ØŸ</summary>
                    <p style="margin-top: 8px; font-size: 13px; color: var(--text-2);">ÙŠÙ…ÙƒÙ†Ùƒ Ø§Ù„Ø¶ØºØ· Ø¹Ù„Ù‰ Ø²Ø± "ØµÙ†Ø¯ÙˆÙ‚ Ø§Ù„ÙˆØ§Ø±Ø¯" ÙÙŠ Ø§Ù„Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ø³ÙÙ„ÙŠØ© Ù„Ù„Ø¹ÙˆØ¯Ø©.</p>
                </details>
                <details style="padding: 8px;">
                    <summary style="font-weight: bold; cursor: pointer; color: var(--text-1);">ÙƒÙŠÙ Ø£Ø¬Ø¯ Ù…Ù„Ø®Øµ Ø§Ù„Ø¯Ø±Ø³ØŸ</summary>
                    <p style="margin-top: 8px; font-size: 13px; color: var(--text-2);">Ø§Ù„Ù…Ù„Ø®Øµ Ù…ØªÙˆÙØ± ÙÙŠ Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ø¯Ø±Ø³ Ø¹Ø¨Ø± Ø²Ø± (Ø§Ù„Ø®Ø±ÙŠØ·Ø© Ø§Ù„Ø°Ù‡Ù†ÙŠØ©).</p>
                </details>
            </div>
            
            <div style="align-self: center; margin-top: 15px; width: 100%; text-align: center;">
                <button onclick="supportFlow.escalateToAdmin()" style="background: #ef4444; color: white; border: none; padding: 12px 20px; border-radius: 24px; font-weight: bold; font-size: 14px; cursor: pointer; box-shadow: 0 4px 10px rgba(239, 68, 68, 0.3);">
                    Ø¥Ø±Ø³Ø§Ù„ Ø§Ù„Ù…Ø´ÙƒÙ„Ø© Ø¥Ù„Ù‰ Ø§Ù„Ø¥Ø¯Ø§Ø±Ø© ðŸ“©
                </button>
            </div>
        `;
        document.getElementById('support-chat-history').insertAdjacentHTML('beforeend', faqs);
        this.scrollToBottom();
    },

    escalateToAdmin: function() {
        // Hide the button
        event.target.style.display = 'none';
        
        this.addMessage("Ø¥Ø±Ø³Ø§Ù„ Ø§Ù„Ù…Ø´ÙƒÙ„Ø© Ø¥Ù„Ù‰ Ø§Ù„Ø¥Ø¯Ø§Ø±Ø©", "user");
        
        setTimeout(() => {
            this.addMessage("âœ… ØªÙ…Øª Ø¥Ø­Ø§Ù„Ø© Ø·Ù„Ø¨Ùƒ Ø¥Ù„Ù‰ Ø§Ù„Ø¥Ø¯Ø§Ø±Ø© Ø¨Ù†Ø¬Ø§Ø­. Ø³ØªØªÙ„Ù‚Ù‰ Ø±Ø¯Ø§Ù‹ ÙÙŠ Ø£Ù‚Ø±Ø¨ ÙˆÙ‚Øª Ù…Ù…ÙƒÙ† Ø¹Ø¨Ø± <b>ØµÙ†Ø¯ÙˆÙ‚ Ø§Ù„ÙˆØ§Ø±Ø¯</b> Ø§Ù„Ø®Ø§Øµ Ø¨Ùƒ.", "bot");
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


