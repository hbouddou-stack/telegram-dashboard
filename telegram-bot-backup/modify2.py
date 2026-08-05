import sys, re

with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    content = f.read()

search_logic = '''            if (isReadingMode) {
                let textToRender = b.explanation && b.explanation.trim() !== "" ? b.explanation : (b.search_text || "");
                if (!isMain && b.title) {
                    res += `<h3 id="reading-subtheme-${bObj.idx}" style="color: var(--primary); margin-top: 24px; margin-bottom: 12px;">${b.title}</h3>`;
                    subThemesList.push({ id: `reading-subtheme-${bObj.idx}`, title: b.title, time: b.start_seconds });
                }
                
                let paragraphs = textToRender.split('\\n').filter(p => p.trim());
                paragraphs.forEach(p => {
                    res += `<div class="reader-paragraph">${formatProse(p)}</div>`;
                });

            } else {'''

replace_logic = '''            if (isReadingMode) {
                let textToRender = b.search_text || "";
                if (!isMain && b.title) {
                    res += `<h3 id="reading-subtheme-${bObj.idx}" style="color: var(--primary); margin-top: 24px; margin-bottom: 12px;">${b.title}</h3>`;
                    subThemesList.push({ id: `reading-subtheme-${bObj.idx}`, title: b.title, time: b.start_seconds });
                }
                
                const poetryRegex = /\\[POEME(?::(\\d+))?\\](.*?)\\[\\/POEME\\]/g;
                let parts = [];
                let lastIndex = 0;
                let match;

                while ((match = poetryRegex.exec(textToRender)) !== null) {
                    const prose = textToRender.substring(lastIndex, match.index);
                    if (prose) parts.push({ type: 'prose', content: prose });
                    let innerText = match[2].trim();
                    let s1 = innerText, s2 = '';
                    if (innerText.includes('***')) {
                        let split = innerText.split('***');
                        s1 = split[0].trim();
                        s2 = split[1].trim();
                    }
                    parts.push({ type: 'poetry', num: match[1] || null, shatr1: s1, shatr2: s2 });
                    lastIndex = poetryRegex.lastIndex;
                }

                if (lastIndex < textToRender.length) parts.push({ type: 'prose', content: textToRender.substring(lastIndex) });
                if (parts.length === 0) parts.push({ type: 'prose', content: textToRender });

                parts.forEach(part => {
                    if (part.type === 'prose') {
                        if (!part.content.trim()) return;
                        let paragraphs = part.content.split('\\n').filter(p => p.trim());
                        paragraphs.forEach(p => {
                            res += `<div class="reader-paragraph">${formatProse(p)}</div>`;
                        });
                    } else {
                        const s1 = formatProse(part.shatr1.trim());
                        const s2 = part.shatr2 ? formatProse(part.shatr2.trim()) : '';
                        const numBadge = part.num ? `<div style="position: absolute; top: -14px; right: 20px; background: var(--gold, #d4af37); color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 2px solid white;">بيت ${part.num}</div>` : '';
                        res += `<div class="poetry-verse-container" style="position: relative; margin: 28px auto 18px auto; max-width: 90%; direction: rtl; text-align: center;">${numBadge}<div class="poetry-verse" style="background: #fffdf5; border: 1.1px solid #f2e7c9; border-radius: 14px; padding: 16px 16px 12px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); font-family: 'Amiri', serif; line-height: 1.8; display: inline-block; width: 100%; box-sizing: border-box; margin-top: ${part.num ? '8px' : '0'};"><div class="shatr" style="font-size: 16.5px; font-weight: 700; color: #854d0e; margin-bottom: ${s2 ? '6px' : '0'}; text-align: center;">${s1}</div>${s2 ? `<div class="shatr" style="font-size: 16.5px; font-weight: 700; color: #854d0e; text-align: center;">${s2}</div>` : ''}</div></div>`;
                    }
                });

                if (b.explanation && b.explanation.trim() !== "") {
                    res += `<div class="reader-chapter-explanation"><div class="explanation-header"><span class="explanation-icon">💡</span><span class="explanation-title">توجيه وفائدة (Note du Professeur)</span></div><div class="explanation-content">${b.explanation}</div></div>`;
                }

            } else {'''
content = content.replace(search_logic, replace_logic)

pills_search = '''    let pillsHtml = '';
    if (data.subThemes && data.subThemes.length > 0) {
        pillsHtml = `<div class="sub-themes-container" style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; padding: 10px; background: rgba(0,0,0,0.02); border-radius: 8px;">`;
        data.subThemes.forEach(st => {
            if (isReadingMode) {
                pillsHtml += `<button class="sub-theme-pill" onclick="document.getElementById('${st.id}').scrollIntoView({behavior:'smooth', block:'start'})" style="background: var(--primary); color: white; border: none; border-radius: 20px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: opacity 0.2s; white-space: nowrap;">${st.title}</button>`;
            } else {
                pillsHtml += `<button class="sub-theme-pill" onclick="jumpToSubTheme(${st.time}, '${st.id}')" style="background: var(--primary); color: white; border: none; border-radius: 20px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: opacity 0.2s; white-space: nowrap;">${st.title}</button>`;
            }
        });
        pillsHtml += `</div>`;
    }'''

pills_replace = '''    let pillsHtml = '';
    if ((data.subThemes && data.subThemes.length > 0) || (data.questions && data.questions.length > 0)) {
        pillsHtml = `<div class="sub-themes-container" style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; padding: 10px; background: rgba(0,0,0,0.02); border-radius: 8px;">`;
        
        if (data.subThemes) {
            data.subThemes.forEach(st => {
                if (isReadingMode) {
                    pillsHtml += `<button class="sub-theme-pill" onclick="document.getElementById('${st.id}').scrollIntoView({behavior:'smooth', block:'start'})" style="background: var(--primary); color: white; border: none; border-radius: 20px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: opacity 0.2s; white-space: nowrap;">${st.title}</button>`;
                } else {
                    pillsHtml += `<button class="sub-theme-pill" onclick="jumpToSubTheme(${st.time}, '${st.id}')" style="background: var(--primary); color: white; border: none; border-radius: 20px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: opacity 0.2s; white-space: nowrap;">${st.title}</button>`;
                }
            });
        }
        
        if (data.questions && data.questions.length > 0) {
            pillsHtml += `<button class="sub-theme-pill" onclick="document.querySelector('.inline-quiz-container').scrollIntoView({behavior:'smooth', block:'start'})" style="background: #eab308; color: white; border: none; border-radius: 20px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: opacity 0.2s; white-space: nowrap; font-weight: bold;">❓ الذهاب إلى الأسئلة</button>`;
        }
        
        pillsHtml += `</div>`;
    }'''
content = content.replace(pills_search, pills_replace)

video_search = '''    const videoWrapper = document.getElementById('video-wrapper');
    const videoTools = document.getElementById('video-tools');
    if (isReadingMode) {
        if (videoWrapper) videoWrapper.style.display = 'none';
        if (videoTools) videoTools.style.display = 'none';'''
video_replace = '''    const videoWrapper = document.getElementById('video-wrapper');
    const videoTools = document.getElementById('video-tools');
    const btnZen = document.getElementById('btn-zen-toggle');
    if (isReadingMode) {
        if (videoWrapper) videoWrapper.style.display = 'none';
        if (videoTools) videoTools.style.display = 'none';
        if (btnZen) btnZen.style.display = 'none';'''
content = content.replace(video_search, video_replace)

video_search2 = '''    } else {
        if (videoWrapper) videoWrapper.style.display = 'flex';
        if (videoTools) videoTools.style.display = 'flex';'''
video_replace2 = '''    } else {
        if (videoWrapper) videoWrapper.style.display = 'flex';
        if (videoTools) videoTools.style.display = 'flex';
        if (btnZen) btnZen.style.display = 'inline-block';'''
content = content.replace(video_search2, video_replace2)

with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(content)
