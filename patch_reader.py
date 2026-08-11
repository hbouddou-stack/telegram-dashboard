import re
import sys

def patch():
    with open('reader.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Rename switchTab to switchThemeTab
    content = re.sub(r'\bswitchTab\(', 'switchThemeTab(', content)
    content = content.replace('function switchThemeTab(index, shouldSeek = true) {', 'function switchThemeTab(index, shouldSeek = true) {')

    # 2. Add Globals
    globals_str = """let player; 
let currentLessonData = null;
let currentTabIndex = 0;
let thematicData = []; // Array of objects { title, startTime, endTime, htmlContent, questions: [] }
let DB = [];
let wordIndex = [];
"""
    content = re.sub(r'let player;[\s\S]*?let thematicData = \[\];[^\n]*\n', globals_str, content, count=1)

    # 3. Rewrite DOMContentLoaded
    old_dom_content_loaded = re.search(r"document\.addEventListener\('DOMContentLoaded', async \(\) => \{[\s\S]*?\}\);", content)
    if not old_dom_content_loaded:
        print("Could not find DOMContentLoaded")
        return

    new_dom_content_loaded = """document.addEventListener('DOMContentLoaded', async () => {
    initUIControls();

    try {
        const urlParams = new URLSearchParams(window.location.search);
        let lessonParam = urlParams.get('lesson'); 
        let subjectParam = urlParams.get('subject'); 

        const response = await fetch('transcripts.json');
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

function openLesson(lesson) {
    currentLessonData = lesson;
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
"""
    content = content.replace(old_dom_content_loaded.group(0), new_dom_content_loaded)

    # 4. Replace buildGlobalSidebar with buildSyllabusTab
    sidebar_regex = re.search(r"function buildGlobalSidebar\([\s\S]*?\}\n\}\n", content)
    if sidebar_regex:
        new_sidebar = """function buildSyllabusTab(transcripts) {
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
        subjContent.className = 'subject-content';
        
        data.lessons.forEach(l => {
            const btn = document.createElement('button');
            btn.className = 'lesson-nav-btn';
            btn.innerHTML = `<span class="lesson-num">${l.lessonNum}</span> <span class="lesson-title-nav">${l.title}</span>`;
            btn.onclick = () => {
                openLesson(l);
                switchTab('reader');
            };
            subjContent.appendChild(btn);
        });

        subjHeader.onclick = () => {
            // Collapse others!
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
}
"""
        content = content.replace(sidebar_regex.group(0), new_sidebar)
    else:
        print("Could not find buildGlobalSidebar")

    # 5. Remove overlay controls that used global-sidebar
    content = re.sub(r"document\.getElementById\('open-global-sidebar'\)\.onclick\s*=\s*\(\)\s*=>\s*\{[\s\S]*?\}\);", "", content)
    content = re.sub(r"document\.getElementById\('close-global-sidebar'\)\.onclick\s*=\s*\(\)\s*=>\s*\{[\s\S]*?\}\);", "", content)
    
    # 6. Append SPA logic
    spa_logic = """
// ─── SPA TAB LOGIC ───
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
}

// ─── PROGRESS LOGIC ───
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
    if (subtitle) subtitle.textContent = `${openedCount} / ${totalLessons} درس`;

    const recentContainer = document.getElementById('recent-lessons-container');
    if (recentContainer) {
        if (recent.length === 0) {
            recentContainer.innerHTML = '<p style="color:var(--text-3); font-size:14px;">لم تفتح أي درس بعد.</p>';
        } else {
            recentContainer.innerHTML = '';
            recent.forEach(r => {
                const lessonObj = DB.find(l => l.subject === r.subject && l.lessonNum == r.lessonNum);
                if (lessonObj) {
                    const btn = document.createElement('div');
                    btn.style.padding = '12px';
                    btn.style.background = 'var(--surface)';
                    btn.style.border = '1px solid var(--border)';
                    btn.style.borderRadius = '12px';
                    btn.style.marginBottom = '8px';
                    btn.style.cursor = 'pointer';
                    btn.style.display = 'flex';
                    btn.style.alignItems = 'center';
                    btn.style.gap = '12px';
                    btn.innerHTML = `<span style="font-size:20px;">📘</span> <div><h4 style="margin:0; font-size:15px;">${lessonObj.title}</h4><span style="font-size:12px; color:var(--text-2);">${lessonObj.subjectLabel}</span></div>`;
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

// ─── SEARCH LOGIC ───
function buildIndex() {
    const stop = new Set(["في","من","على","إلى","عن","هذا","هذه","التي","الذي","أن","إن","لا","ما","مع","كان","كانت","ثم","أو","أم","كل","يوم","بعد","قبل","عند","هو","هي","وقد","قد","فقد","وهو","وهي","وكان"]);
    const seen = new Set();
    DB.forEach(item => {
        ((item.full_text||'')+' '+(item.blocks_search_text||'')).split(/[\s،.؟!():؛]+/).forEach(w=>{
            const c=w.trim();
            if(c.length>=3&&c.length<=10&&!stop.has(c)&&!seen.has(c)){
                seen.add(c);
                wordIndex.push({text:c,subjectLabel:item.subjectLabel,cls:'badge-'+item.subject});
            }
        });
    });
}

function strip(html){return new DOMParser().parseFromString(html,'text/html').body.textContent||'';}
function esc(str){return str.replace(/[.*+?^${}()|[\]\\\]/g,'\\$&');}
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
        resContainer.innerHTML = `<div class="empty-state"><p style="color:var(--text-3);">لا توجد نتائج</p></div>`;
        return;
    }
    
    let html = '';
    top.forEach(r => {
        const item = r.item;
        const b = r.block;
        html += `<div class="s-card" style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:12px; margin-bottom:10px; cursor:pointer;" onclick="openSearchResult('${item.subject}', ${item.lessonNum}, ${b.startTime})">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <h4 style="margin:0; font-size:14px; color:var(--text);">${hl(b.title, queries[0])}</h4>
                <span class="badge badge-${item.subject}">${item.subjectLabel} ${item.lessonNum}</span>
            </div>
            <div style="font-size:12px; color:var(--text-2);">${formatSeconds(b.startTime)}</div>
        </div>`;
    });
    resContainer.innerHTML = html;
}

function resetSearch() {
    const res = document.getElementById('search-results');
    if(res) res.innerHTML = `<div class="empty-state"><p style="color:var(--text-3);">اكتب كلمة للبحث</p></div>`;
}

function openSearchResult(subject, lessonNum, startTime) {
    const lesson = DB.find(l => l.subject === subject && l.lessonNum === lessonNum);
    if(lesson) {
        openLesson(lesson);
        switchTab('reader');
        if(player && typeof player.seekTo === 'function') {
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
        }
        
        // Find matching theme tab index based on startTime
        const idx = thematicData.findIndex(t => t.startTime <= startTime && t.endTime > startTime);
        if(idx !== -1) {
            switchThemeTab(idx, false);
        }
    }
}
"""
    content += spa_logic

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Patched reader.js")

if __name__ == "__main__":
    patch()
