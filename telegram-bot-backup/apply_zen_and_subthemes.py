import sys

with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Inject sub-themes parsing into prepareThematicData
target_push = '''        thematicData.push({
            title: block.title || `المحور ${idx + 1}`,
            startTime: block.start_seconds || 0,
            endTime: nextStart,
            htmlContent: htmlContent,
            questions: blockQuestions
        });'''

replacement_push = '''        let subThemes = [];
        let subThemeIndex = 0;
        htmlContent = htmlContent.replace(/<span([^>]*)>([^<]*)\[SOUS-THEME:\s*(.*?)\]([^<]*)<\/span>/g, (match, spanAttrs, before, title, after) => {
            let secMatch = spanAttrs.match(/data-start="([^"]+)"/);
            let timeSec = secMatch ? parseFloat(secMatch[1]) : (block.start_seconds || 0);
            let id = `subtheme-${idx}-${subThemeIndex++}`;
            subThemes.push({ id: id, title: title.trim(), time: timeSec });
            
            let res = `</div><div class="sub-theme-header" id="${id}"><h3><span class="sub-theme-icon"></span>${title.trim()}</h3></div><div class="reader-paragraph">`;
            if (before.trim() || after.trim()) {
                res += `<span${spanAttrs}>${before}${after}</span>`;
            }
            return res;
        });

        thematicData.push({
            title: block.title || `المحور ${idx + 1}`,
            startTime: block.start_seconds || 0,
            endTime: nextStart,
            htmlContent: htmlContent,
            questions: blockQuestions,
            subThemes: subThemes
        });'''

if target_push in content:
    content = content.replace(target_push, replacement_push)
    print("Injected subThemes parsing")
else:
    print("FAILED to inject subThemes parsing")


# 2. Inject pills rendering into switchThemeTab
target_tab = '''    const activeData = thematicData[index];
    document.getElementById('transcript-text').innerHTML = activeData.htmlContent;

    // Load active questions'''

replacement_tab = '''    const activeData = thematicData[index];
    
    let pillsHtml = '';
    if (activeData.subThemes && activeData.subThemes.length > 0) {
        pillsHtml = `<div class="sub-themes-container" style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; padding: 10px; background: rgba(0,0,0,0.02); border-radius: 8px;">`;
        activeData.subThemes.forEach(st => {
            pillsHtml += `<button class="sub-theme-pill" onclick="jumpToSubTheme(${st.time}, '${st.id}')" style="background: var(--primary); color: white; border: none; border-radius: 20px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: opacity 0.2s; white-space: nowrap;">${st.title}</button>`;
        });
        pillsHtml += `</div>`;
    }
    
    document.getElementById('transcript-text').innerHTML = pillsHtml + activeData.htmlContent;

    // Load active questions'''

if target_tab in content:
    content = content.replace(target_tab, replacement_tab)
    print("Injected pills rendering")
else:
    print("FAILED to inject pills rendering")


# 3. Inject jumpToSubTheme function
target_funcs = '''function generateQuizHtml(questions) {'''
replacement_funcs = '''window.jumpToSubTheme = function(time, id) {
    const isZenMode = document.body.classList.contains('zen-mode');
    if (isZenMode) {
        const el = document.getElementById(id);
        if (el) {
            const headerOffset = 180;
            const elementPosition = el.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
            window.scrollTo({
                top: offsetPosition,
                behavior: "smooth"
            });
        }
    } else {
        if (player && typeof player.seekTo === 'function') {
            player.seekTo(time, true);
        }
    }
};

function generateQuizHtml(questions) {'''

if target_funcs in content:
    content = content.replace(target_funcs, replacement_funcs)
    print("Injected jumpToSubTheme")
else:
    print("FAILED to inject jumpToSubTheme")


# 4. Zen Mode highlight logic disabling
target_karaoke = '''    segments.forEach(seg => {
        let start = parseFloat(seg.getAttribute('data-start'));
        if (start === activeStart && currentTime < nextStart) {
            if (!seg.classList.contains('active-karaoke')) {
                seg.classList.add('active-karaoke');
            }
            if (!firstActiveSeg) firstActiveSeg = seg;
        } else {
            if (seg.classList.contains('active-karaoke')) {
                seg.classList.remove('active-karaoke');
            }
        }
    });'''

replacement_karaoke = '''    const isZenMode = document.body.classList.contains('zen-mode');
    segments.forEach(seg => {
        let start = parseFloat(seg.getAttribute('data-start'));
        if (!isZenMode && start === activeStart && currentTime < nextStart) {
            if (!seg.classList.contains('active-karaoke')) {
                seg.classList.add('active-karaoke');
            }
            if (!firstActiveSeg) firstActiveSeg = seg;
        } else {
            if (seg.classList.contains('active-karaoke')) {
                seg.classList.remove('active-karaoke');
            }
        }
    });'''

if target_karaoke in content:
    content = content.replace(target_karaoke, replacement_karaoke)
    print("Injected Zen Mode highlight disable")
else:
    print("FAILED to inject Zen Mode highlight disable")


with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(content)
