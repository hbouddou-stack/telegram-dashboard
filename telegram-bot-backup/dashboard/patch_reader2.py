import re

file_path = "reader.js"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_prepare = """
function prepareThematicData(lesson) {
    thematicData = [];
    
    let blocks = lesson.thematic_blocks || [];
    if(blocks.length === 0) {
        thematicData.push({
            title: "Leçon complète",
            startTime: 0,
            endTime: 99999,
            htmlContent: `<div class="reader-paragraph">${lesson.full_text || lesson.summary || ''}</div>`,
            questions: lesson.quiz || []
        });
        return;
    }

    // Group blocks: Main Theme + its Sub Themes
    let groupedThemes = [];
    let currentMain = null;

    blocks.forEach((block, idx) => {
        let text = block.reading_text || block.search_text || "";
        // Re-apply poetry formatting if it exists manually typed
        const poetryRegex = /\\[POEME(?::(\\d+))?\\](.*?)\\[\\/POEME\\]/g;
        let formattedText = text.replace(poetryRegex, (match, num, inner) => {
            let s1 = inner, s2 = '';
            if (inner.includes('***')) {
                let split = inner.split('***');
                s1 = split[0].trim();
                s2 = split[1].trim();
            }
            return `<div class="poetry-block"><div class="poetry-row"><div class="shatr">${s1}</div><div class="shatr-gap"></div><div class="shatr">${s2}</div></div></div>`;
        });
        
        let blockObj = {
            title: block.title || 'Sans titre',
            start: block.start_seconds || 0,
            htmlContent: `<div class="reader-paragraph" style="line-height: 1.8; font-size: 1.05rem; margin-bottom: 20px;">${formattedText}</div>`,
            isSub: !!block.is_sub_theme
        };

        if (!blockObj.isSub) {
            currentMain = {
                title: blockObj.title,
                startTime: blockObj.start,
                endTime: 99999,
                subThemes: [],
                htmlContent: `<div>${blockObj.htmlContent}</div>`
            };
            groupedThemes.push(currentMain);
        } else {
            if (currentMain) {
                currentMain.subThemes.push(blockObj);
            } else {
                // If the first block is somehow a subtheme
                currentMain = {
                    title: "Introduction",
                    startTime: 0,
                    endTime: 99999,
                    subThemes: [blockObj],
                    htmlContent: ""
                };
                groupedThemes.push(currentMain);
            }
        }
    });

    // Fix end times
    for (let i = 0; i < groupedThemes.length; i++) {
        if (i < groupedThemes.length - 1) {
            groupedThemes[i].endTime = groupedThemes[i+1].startTime;
        }
    }

    // Generate final htmlContent with sticky menu
    groupedThemes.forEach((group, gIdx) => {
        let finalHtml = "";
        
        if (group.subThemes.length > 0) {
            // Sticky accordion/menu
            finalHtml += `
            <div class="subthemes-sticky-menu" style="position: sticky; top: 0; background: var(--bg); z-index: 50; padding: 10px 0; border-bottom: 1px solid var(--border-color); display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; margin-bottom: 20px;">
                ${group.subThemes.map((s, sIdx) => `
                    <button onclick="document.getElementById('subtheme-${gIdx}-${sIdx}').scrollIntoView({behavior: 'smooth', block: 'start'})" style="background: var(--surface-2); border: 1px solid var(--border-color); color: var(--text-color); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; white-space: nowrap; cursor: pointer; transition: background 0.2s;">
                        ${s.title}
                    </button>
                `).join('')}
            </div>`;
        }

        finalHtml += group.htmlContent;

        group.subThemes.forEach((s, sIdx) => {
            finalHtml += `
            <div id="subtheme-${gIdx}-${sIdx}" class="subtheme-section" style="margin-top: 30px; margin-bottom: 40px; padding-top: 20px; border-top: 1px dashed var(--border-color);">
                <h3 style="font-size: 1.2rem; font-weight: bold; color: var(--primary); margin-bottom: 15px;">${s.title}</h3>
                ${s.htmlContent}
            </div>
            `;
        });

        thematicData.push({
            title: group.title,
            startTime: group.startTime,
            endTime: group.endTime,
            htmlContent: finalHtml,
            questions: lesson.quiz || [] // We can filter questions by time if needed, but keeping simple
        });
    });
}
"""

pattern_prepare = re.compile(r'function prepareThematicData\(lesson\) \{.*?(?=function renderSyllabusView)', re.DOTALL)
match = pattern_prepare.search(content)
content = content[:match.start()] + new_prepare + "\n" + content[match.end():]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("reader.js prepareThematicData patched successfully.")
