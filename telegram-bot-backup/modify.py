import sys, re

with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Chunk 1
content = content.replace(
    'let thematicData = []; // Array of objects { title, startTime, endTime, htmlContent, questions: [] }\nlet DB = [];',
    'let thematicData = []; // Array of objects { title, startTime, endTime, htmlContent, questions: [] }\nlet isReadingMode = false;\nlet DB = [];'
)

# Chunk 2
init_ui_search = 'function initUIControls() {\\n    // Sticky Video Toggle Logic'
init_ui_replace = '''function initUIControls() {
    const btnReadingMode = document.getElementById('btn-reading-mode-toggle');
    if (btnReadingMode) {
        btnReadingMode.addEventListener('click', () => {
            isReadingMode = !isReadingMode;
            btnReadingMode.style.background = isReadingMode ? 'var(--primary)' : 'var(--surface)';
            btnReadingMode.style.color = isReadingMode ? 'white' : 'var(--primary)';
            btnReadingMode.textContent = isReadingMode ? '🎥 فيديو' : '📖 قراءة';
            
            if (currentLessonData) {
                prepareThematicData(currentLessonData);
                renderTabs();
                switchThemeTab(currentTabIndex, !isReadingMode);
            }
        });
    }

    // Sticky Video Toggle Logic'''
content = content.replace(init_ui_search, init_ui_replace)

# Chunk 3: prepareThematicData
prepare_data_pattern = re.compile(r'function prepareThematicData\(lesson\) \{.*?\n\}\n', re.DOTALL)
prepare_data_replace = '''function prepareThematicData(lesson) {
    thematicData = [];
    if (!lesson.segments || lesson.segments.length === 0) {
        thematicData.push({
            title: "Leçon complète",
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

    let groupedThemes = [];
    blocks.forEach((block, idx) => {
        let nextStart = (idx < blocks.length - 1) ? blocks[idx+1].start_seconds : 99999;
        let blockSegments = lesson.segments.filter(s => s.sec >= block.start_seconds && s.sec < nextStart);
        
        let blockObj = {
            block: block,
            idx: idx,
            nextStart: nextStart,
            segments: blockSegments
        };
        
        if (block.is_sub_theme && groupedThemes.length > 0) {
            groupedThemes[groupedThemes.length - 1].subBlocks.push(blockObj);
        } else {
            blockObj.subBlocks = [];
            groupedThemes.push(blockObj);
        }
    });

    groupedThemes.forEach((themeObj) => {
        const mainBlock = themeObj.block;
        const mainIdx = themeObj.idx;
        
        let htmlContent = "";
        let subThemesList = [];

        function renderBlockToHtml(bObj, isMain) {
            let b = bObj.block;
            let res = "";

            if (isReadingMode) {
                let textToRender = b.explanation && b.explanation.trim() !== "" ? b.explanation : (b.search_text || "");
                if (!isMain && b.title) {
                    res += `<h3 id="reading-subtheme-${bObj.idx}" style="color: var(--primary); margin-top: 24px; margin-bottom: 12px;">${b.title}</h3>`;
                    subThemesList.push({ id: `reading-subtheme-${bObj.idx}`, title: b.title, time: b.start_seconds });
                }
                
                let paragraphs = textToRender.split('\\n').filter(p => p.trim());
                paragraphs.forEach(p => {
                    res += `<div class="reader-paragraph">${formatProse(p)}</div>`;
                });

            } else {
                const poetryRegex = /\\[POEME(?::(\\d+))?\\](.*?)\\[\\/POEME\\]/g;
                let parts = [];
                let lastIndex = 0;
                let match;
                let blockText = bObj.segments.map(s => `[[TS:${s.sec}]]${s.text}`).join(' ');
                let lastTs = b.start_seconds || 0;
                
                function injectKaraokeSpans(htmlString) {
                    let initialTs = lastTs;
                    let out = htmlString.replace(/\\[\\[TS:(\\d+(?:\\.\\d+)?)\\]\\]/g, (m, sec) => {
                        lastTs = sec;
                        return `</span><span class="karaoke-segment" data-start="${sec}">`;
                    });
                    if (out.startsWith('</span>')) out = out.substring(7);
                    else out = `<span class="karaoke-segment" data-start="${initialTs}">` + out;
                    out = out + `</span>`;
                    return out.replace(/<span[^>]*>\\s*<\\/span>/g, '');
                }

                while ((match = poetryRegex.exec(blockText)) !== null) {
                    const prose = blockText.substring(lastIndex, match.index);
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

                if (lastIndex < blockText.length) parts.push({ type: 'prose', content: blockText.substring(lastIndex) });
                if (parts.length === 0) parts.push({ type: 'prose', content: blockText });

                parts.forEach(part => {
                    if (part.type === 'prose') {
                        if (!part.content.trim()) return;
                        let sentences = part.content.match(/[^.!?]+[.!?]*/g) || [part.content];
                        let pText = "", pCount = 0;
                        sentences.forEach(sentence => {
                            pText += sentence.trim() + " "; pCount++;
                            if (pCount >= 4) {
                                res += `<div class="reader-paragraph">${injectKaraokeSpans(formatProse(pText))}</div>`;
                                pText = ""; pCount = 0;
                            }
                        });
                        if (pText.trim() !== "") res += `<div class="reader-paragraph">${injectKaraokeSpans(formatProse(pText))}</div>`;
                    } else {
                        const s1 = injectKaraokeSpans(formatProse(part.shatr1.trim()));
                        const s2 = part.shatr2 ? injectKaraokeSpans(formatProse(part.shatr2.trim())) : '';
                        const numBadge = part.num ? `<div style="position: absolute; top: -14px; right: 20px; background: var(--gold, #d4af37); color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 2px solid white;">بيت ${part.num}</div>` : '';
                        res += `<div class="poetry-verse-container" style="position: relative; margin: 28px auto 18px auto; max-width: 90%; direction: rtl; text-align: center;">${numBadge}<div class="poetry-verse" style="background: #fffdf5; border: 1.1px solid #f2e7c9; border-radius: 14px; padding: 16px 16px 12px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); font-family: 'Amiri', serif; line-height: 1.8; display: inline-block; width: 100%; box-sizing: border-box; margin-top: ${part.num ? '8px' : '0'};"><div class="shatr" style="font-size: 16.5px; font-weight: 700; color: #854d0e; margin-bottom: ${s2 ? '6px' : '0'}; text-align: center;">${s1}</div>${s2 ? `<div class="shatr" style="font-size: 16.5px; font-weight: 700; color: #854d0e; text-align: center;">${s2}</div>` : ''}</div></div>`;
                    }
                });

                if (b.explanation && b.explanation.trim() !== "") {
                    res += `<div class="reader-chapter-explanation"><div class="explanation-header"><span class="explanation-icon">💡</span><span class="explanation-title">توجيه وفائدة (Note du Professeur)</span></div><div class="explanation-content">${b.explanation}</div></div>`;
                }

                let subThemeIndex = 0;
                res = res.replace(/<span([^>]*)>([^<]*)\\[SOUS-THEME:\\s*(.*?)\\]([^<]*)<\\/span>/g, (match, spanAttrs, before, title, after) => {
                    let secMatch = spanAttrs.match(/data-start="([^"]+)"/);
                    let timeSec = secMatch ? parseFloat(secMatch[1]) : (b.start_seconds || 0);
                    let id = `subtheme-${bObj.idx}-${subThemeIndex++}`;
                    subThemesList.push({ id: id, title: title.trim(), time: timeSec });
                    
                    let out = `</div><div class="sub-theme-header" id="${id}"><h3><span class="sub-theme-icon"></span>${title.trim()}</h3></div><div class="reader-paragraph">`;
                    if (before.trim() || after.trim()) {
                        out += `<span${spanAttrs}>${before}${after}</span>`;
                    }
                    return out;
                });
            }
            return res;
        }

        htmlContent += renderBlockToHtml(themeObj, true);
        
        themeObj.subBlocks.forEach(sb => {
            htmlContent += renderBlockToHtml(sb, false);
        });

        let blockQuestions = [];
        let groupEndSec = themeObj.subBlocks.length > 0 ? themeObj.subBlocks[themeObj.subBlocks.length-1].nextStart : themeObj.nextStart;
        for (let i = questions.length - 1; i >= 0; i--) {
            let q = questions[i];
            let qTimeSec = extractSecondsFromExplanation(q.explanation);
            if ((qTimeSec >= mainBlock.start_seconds && qTimeSec < groupEndSec) || (mainIdx === blocks.length - 1 && qTimeSec === -1)) {
                blockQuestions.push(q);
                questions.splice(i, 1);
            }
        }

        thematicData.push({
            title: mainBlock.title,
            level: mainBlock.level || 1,
            startTime: mainBlock.start_seconds,
            endTime: groupEndSec,
            htmlContent: htmlContent,
            questions: blockQuestions.reverse(),
            subThemes: subThemesList,
            originalIndex: mainIdx
        });
    });
}
'''
match = prepare_data_pattern.search(content)
if match:
    content = content[:match.start()] + prepare_data_replace + content[match.end():]
else:
    print("Pattern 3 not found")

# Chunk 4: Pills Logic
pills_search = '''    let pillsHtml = '';
    if (data.subThemes && data.subThemes.length > 0) {
        pillsHtml = `<div class="sub-themes-container" style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; padding: 10px; background: rgba(0,0,0,0.02); border-radius: 8px;">`;
        data.subThemes.forEach(st => {
            pillsHtml += `<button class="sub-theme-pill" onclick="jumpToSubTheme(${st.time}, '${st.id}')" style="background: var(--primary); color: white; border: none; border-radius: 20px; padding: 6px 14px; font-size: 13px; cursor: pointer; transition: opacity 0.2s; white-space: nowrap;">${st.title}</button>`;
        });
        pillsHtml += `</div>`;
    }'''
pills_replace = '''    let pillsHtml = '';
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
content = content.replace(pills_search, pills_replace)

# Chunk 5: Video logic in switchThemeTab
video_logic_search = '''    // Video Seek
    if (shouldSeek && player && player.seekTo) {
        isSeekingTab = true;
        player.seekTo(data.startTime, true);
        player.playVideo();
        setTimeout(() => { isSeekingTab = false; }, 1500);
        // Scroll to video
        window.scrollTo({top: 0, behavior: 'smooth'});
    } else if (shouldSeek) {
        window.scrollTo({top: 0, behavior: 'smooth'});
    }'''
video_logic_replace = '''    // Video Seek and Reading Mode Toggle
    const videoWrapper = document.getElementById('video-wrapper');
    const videoTools = document.getElementById('video-tools');
    if (isReadingMode) {
        if (videoWrapper) videoWrapper.style.display = 'none';
        if (videoTools) videoTools.style.display = 'none';
        if (player && player.pauseVideo) player.pauseVideo();
        contentArea.style.paddingTop = '20px';
        window.scrollTo({top: 0, behavior: 'smooth'});
    } else {
        if (videoWrapper) videoWrapper.style.display = 'flex';
        if (videoTools) videoTools.style.display = 'flex';
        contentArea.style.paddingTop = '0px';
        if (shouldSeek && player && player.seekTo) {
            isSeekingTab = true;
            player.seekTo(data.startTime, true);
            player.playVideo();
            setTimeout(() => { isSeekingTab = false; }, 1500);
            window.scrollTo({top: 0, behavior: 'smooth'});
        } else if (shouldSeek) {
            window.scrollTo({top: 0, behavior: 'smooth'});
        }
    }'''
content = content.replace(video_logic_search, video_logic_replace)

with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(content)
