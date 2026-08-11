import re

def update_html():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    sidebar_pattern = re.compile(r'<!-- Global Navigation Sidebar -->\s*<nav class="global-sidebar" id="global-sidebar">.*?</nav>\s*<div class="sidebar-overlay" id="global-overlay"></div>', re.DOTALL)
    
    tab_syllabus_html = """
    <!-- TAB: SYLLABUS -->
    <div class="tab-panel" id="tab-syllabus">
        <div style="padding: 20px;">
            <h2 style="color:var(--primary); font-weight:800; margin-bottom:20px; text-align:center;">📚 المقررات</h2>
            <div id="subjects-list" class="subjects-accordion">
                <!-- Subjects and lessons injected here -->
            </div>
        </div>
    </div>
"""
    if sidebar_pattern.search(html):
        html = sidebar_pattern.sub(tab_syllabus_html, html)
    else:
        print("Syllabus HTML not found!")
    
    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML updated")

def update_css():
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    if "3D Buttons for Syllabus" not in css:
        css += """
/* --- 3D Buttons for Syllabus --- */
.subject-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    padding: 10px 0;
}
.lesson-3d-btn {
    width: 50px;
    height: 50px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: 800;
    color: white;
    cursor: pointer;
    border: none;
    transition: transform 0.1s, box-shadow 0.1s;
    font-family: inherit;
}
.lesson-3d-btn:active {
    transform: translateY(4px) !important;
    box-shadow: 0 0px 0px rgba(0,0,0,0.2) !important;
}

/* Colors for subjects */
.subject-sira { background: #3b82f6; box-shadow: 0 4px 0 #2563eb; }
.subject-fiqh { background: #10b981; box-shadow: 0 4px 0 #059669; }
.subject-tahawi { background: #f59e0b; box-shadow: 0 4px 0 #d97706; }
.subject-adab { background: #8b5cf6; box-shadow: 0 4px 0 #7c3aed; }
.subject-default { background: #64748b; box-shadow: 0 4px 0 #475569; }
"""
        with open('reader.css', 'w', encoding='utf-8') as f:
            f.write(css)
        print("CSS updated")

def update_js():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()
    
    js = js.replace("""    if (name === 'syllabus') {
        document.getElementById('global-sidebar').classList.add('open');
        document.getElementById('global-overlay').classList.add('show');
        return; // Don't switch active tab
    }""", "")

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
        subjContent.className = 'subject-content subject-grid';
        
        let colorClass = 'subject-default';
        if (subjectKey.includes('sira') || subjectKey.includes('sirah')) colorClass = 'subject-sira';
        else if (subjectKey.includes('fiqh')) colorClass = 'subject-fiqh';
        else if (subjectKey.includes('tahawi') || subjectKey.includes('aqida')) colorClass = 'subject-tahawi';
        else if (subjectKey.includes('adab')) colorClass = 'subject-adab';
        else colorClass = 'subject-sira'; // default fallback colored
        
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
}"""
        js = js.replace(old_build.group(0), new_build)

    if 'let pendingSeekTime = null;' not in js:
        js = js.replace('let wordIndex = [];', 'let wordIndex = [];\nlet pendingSeekTime = null;')

    old_seek = """        if(player && typeof player.seekTo === 'function') {
            player.seekTo(startTime, true);
            player.playVideo();
        } else {
            // Player might not be ready, poll
            const interval = setInterval(() => {
                if(player && typeof player.seekTo === 'function') {
                    player.seekTo(startTime, true);
                    player.playVideo();
                    clearInterval(interval);
                }
            }, 500);
        }"""
    
    new_seek = """        pendingSeekTime = startTime;
        if(player && typeof player.seekTo === 'function') {
            const state = player.getPlayerState();
            if (state === YT.PlayerState.PLAYING || state === YT.PlayerState.PAUSED || state === YT.PlayerState.CUED) {
                player.seekTo(startTime, true);
                player.playVideo();
                pendingSeekTime = null;
            } else {
                player.playVideo(); // triggers state change
            }
        }"""
    js = js.replace(old_seek, new_seek)

    state_change = re.search(r'function onPlayerStateChange\(event\) \{[\s\S]*?\}', js)
    if state_change and 'pendingSeekTime' not in state_change.group(0):
        new_state_change = state_change.group(0).replace('function onPlayerStateChange(event) {', """function onPlayerStateChange(event) {
    if (pendingSeekTime !== null && (event.data === YT.PlayerState.PLAYING || event.data === YT.PlayerState.CUED)) {
        player.seekTo(pendingSeekTime, true);
        player.playVideo();
        pendingSeekTime = null;
    }""")
        js = js.replace(state_change.group(0), new_state_change)

    # Empty state for youtube wrapper
    render_yt = re.search(r'function renderLessonHeader\(lesson\) \{[\s\S]*?\}', js)
    if render_yt:
        new_render = """function renderLessonHeader(lesson) {
    document.getElementById('lesson-title').textContent = lesson.title || `الدرس ${lesson.lessonNum}`;
    document.getElementById('lesson-subject').textContent = lesson.subjectLabel || lesson.subject;
    document.getElementById('lesson-subject').className = `badge badge-${lesson.subject}`;

    const videoId = extractYoutubeId(lesson.videoLink || lesson.url);
    const videoWrapper = document.getElementById('video-wrapper');
    if (!videoId) {
        videoWrapper.innerHTML = '<div style="background:#1e293b; color:white; height:100%; display:flex; align-items:center; justify-content:center; flex-direction:column;"><span style="font-size:32px;margin-bottom:8px;">🎥</span><span style="font-size:14px;">الفيديو غير متوفر لهذا الدرس</span></div>';
    } else {
        videoWrapper.innerHTML = '<div id="youtube-player"></div>';
        if (window.YT && window.YT.Player) {
            initYouTubePlayer(videoId);
        } else {
            // API non prête
            const interval = setInterval(() => {
                if (window.YT && window.YT.Player) {
                    initYouTubePlayer(videoId);
                    clearInterval(interval);
                }
            }, 500);
        }
    }
}"""
        js = js.replace(render_yt.group(0), new_render)


    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print("JS updated")

if __name__ == '__main__':
    update_html()
    update_css()
    update_js()
