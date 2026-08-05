import re

file_path = "reader.js"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_prepare = """
function prepareThematicData(lesson) {
    thematicData = [];
    
    let blocks = lesson.thematic_blocks || [];
    if(blocks.length === 0) {
        // Fallback
        blocks = [{ title: "Leçon complète", start_seconds: 0, end_seconds: 99999, subthemes: [{title: "Contenu", htmlContent: `<p>${lesson.full_text || lesson.summary}</p>`}] }];
    }

    blocks.forEach((block, idx) => {
        let nextStart = (idx < blocks.length - 1) ? blocks[idx+1].start_seconds : 99999;
        
        let htmlContent = "";
        
        // 1. Build Subthemes Sticky Menu
        const subthemes = block.subthemes || [];
        if (subthemes.length > 0) {
            htmlContent += `
            <div class="subthemes-sticky-menu" style="position: sticky; top: 0; background: var(--bg); z-index: 50; padding: 10px 0; border-bottom: 1px solid var(--border-color); display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; margin-bottom: 20px;">
                ${subthemes.map((s, sIdx) => `
                    <button onclick="document.getElementById('subtheme-${sIdx}').scrollIntoView({behavior: 'smooth', block: 'start'})" style="background: var(--surface-2); border: 1px solid var(--border-color); color: var(--text-color); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; white-space: nowrap; cursor: pointer; transition: background 0.2s;">
                        ${s.title || 'Sous-thème ' + (sIdx+1)}
                    </button>
                `).join('')}
            </div>`;
        }

        // 2. Build Content Blocks
        subthemes.forEach((s, sIdx) => {
            htmlContent += `
            <div id="subtheme-${sIdx}" class="subtheme-section" style="margin-bottom: 40px;">
                <h3 style="font-size: 1.2rem; font-weight: bold; color: var(--primary); margin-bottom: 15px;">${s.title}</h3>
                <div class="reader-paragraph" style="line-height: 1.8; font-size: 1.05rem;">
                    ${s.htmlContent}
                </div>
            </div>
            `;
        });

        // 3. Questions
        let blockQuestions = [];
        if (lesson.quiz) {
            lesson.quiz.forEach(q => {
                if (q.time !== undefined) {
                    if (q.time >= block.start_seconds && q.time < nextStart) {
                        blockQuestions.push(q);
                    }
                }
            });
        }

        thematicData.push({
            title: block.title,
            startTime: block.start_seconds || 0,
            endTime: nextStart,
            htmlContent: htmlContent,
            questions: blockQuestions,
            isSubTheme: false
        });
    });
}
"""

# Regex replacement for prepareThematicData
pattern_prepare = re.compile(r'function prepareThematicData\(lesson\) \{.*?(?=function renderSyllabusView)', re.DOTALL)
content = pattern_prepare.sub(new_prepare + "\n", content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("reader.js prepareThematicData patched successfully.")
