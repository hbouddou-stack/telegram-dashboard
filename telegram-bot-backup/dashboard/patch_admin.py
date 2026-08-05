import re

file_path = "admin.js"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace renderTranscriptEditorHTML
new_render_html = """
        function renderTranscriptEditorHTML(lesson) {
            const blocks = lesson.thematic_blocks || [];
            
            let html = `
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding: 16px 24px; background:var(--bg); flex-shrink:0;">
                <div>
                    <h2 style="margin:0; font-size:1.3rem;">📝 Éditeur Structuré de Sous-Thématiques</h2>
                    <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:4px;">Cours ${lesson.lessonNum} — ${lesson.subjectLabel || lesson.subject}</div>
                </div>
                <div style="display:flex; gap:8px; align-items:center;">
                    <button class="btn btn-primary" id="save-transcript-btn" onclick="saveFullTranscript()">💾 Enregistrer les modifications</button>
                    <button class="btn btn-secondary" onclick="closeTranscriptDrawer()">✖ Fermer</button>
                </div>
            </div>
            <div style="flex:1; overflow-y:auto; padding:20px 24px; display:flex; flex-direction:column; gap:25px;" id="transcript-editor-body">`;

            blocks.forEach((block, bIdx) => {
                html += `
                <div class="thematic-block-card" data-bidx="${bIdx}" style="border: 2px solid var(--primary-light, #e0e7ff); border-radius: 12px; padding: 20px; background: #fff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; margin-bottom: 15px;">
                        <div style="display:flex; align-items:center; gap: 10px;">
                            <span style="background: var(--primary); color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; justify-content: center; align-items: center; font-weight: bold;">${bIdx + 1}</span>
                            <input type="text" class="main-theme-title-input" value="${(block.title || '').replace(/"/g, '&quot;')}" style="font-size: 1.15rem; font-weight: bold; border: none; outline: none; background: transparent; width: 300px;" placeholder="Titre de la thématique principale...">
                        </div>
                        <div style="display:flex; gap: 10px;">
                            <input type="text" class="main-theme-ts-input" value="${block.timestamp || '0:00'}" style="width: 70px; text-align: center; border: 1px solid #ccc; border-radius: 6px; padding: 4px;" title="Timecode (MM:SS)">
                            <button class="btn btn-secondary btn-sm" onclick="addSubTheme(${bIdx})" style="background: #f8fafc; color: var(--primary); border: 1px dashed var(--primary);">+ Sous-Thématique</button>
                            <button class="btn btn-secondary btn-sm" onclick="moveMainTheme(${bIdx}, -1)">⬆️</button>
                            <button class="btn btn-secondary btn-sm" onclick="moveMainTheme(${bIdx}, 1)">⬇️</button>
                        </div>
                    </div>
                    <div class="subthemes-container" id="subthemes-container-${bIdx}" style="display:flex; flex-direction:column; gap: 15px;">
                `;

                const subthemes = block.subthemes || [];
                subthemes.forEach((sub, sIdx) => {
                    let moveOptions = blocks.map((b, i) => `<option value="${i}" ${i === bIdx ? 'selected' : ''}>Thème ${i+1}</option>`).join('');
                    
                    html += `
                    <div class="subtheme-card" data-sidx="${sIdx}" style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; background: #f8fafc; position: relative;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <input type="text" class="subtheme-title-input" value="${(sub.title || '').replace(/"/g, '&quot;')}" style="font-weight: bold; font-size: 1rem; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px 10px; width: 60%;" placeholder="Titre du sous-thème">
                            <div style="display: flex; gap: 8px;">
                                <select class="form-select subtheme-move-select" onchange="moveSubthemeToMain(${bIdx}, ${sIdx}, this.value)" style="padding: 4px 8px; font-size: 0.85rem;" title="Envoyer vers une autre thématique principale">
                                    <option value="" disabled>Envoyer vers...</option>
                                    ${moveOptions}
                                </select>
                                <button class="btn btn-secondary btn-sm" onclick="moveSubTheme(${bIdx}, ${sIdx}, -1)">🔼</button>
                                <button class="btn btn-secondary btn-sm" onclick="moveSubTheme(${bIdx}, ${sIdx}, 1)">🔽</button>
                                <button class="btn btn-secondary btn-sm" onclick="deleteSubTheme(${bIdx}, ${sIdx})" style="color: red;">❌</button>
                            </div>
                        </div>
                        <textarea class="subtheme-html-input" style="width: 100%; min-height: 120px; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; font-family: sans-serif; resize: vertical;" placeholder="Contenu de la sous-thématique...">${(sub.htmlContent || '').replace(/"/g, '&quot;')}</textarea>
                    </div>
                    `;
                });

                html += `</div></div>`;
            });

            html += `
                <div style="text-align: center; margin-top: 10px;">
                    <button class="btn btn-secondary" onclick="addMainTheme()" style="width: 100%; border: 2px dashed var(--primary); background: rgba(79,70,229,0.05); padding: 15px; font-weight: bold; color: var(--primary); font-size: 1.1rem;">+ Ajouter une nouvelle Thématique Principale</button>
                </div>
            </div>`;
            return html;
        }

        window.addMainTheme = function() {
            transcriptEditorLesson.thematic_blocks = transcriptEditorLesson.thematic_blocks || [];
            transcriptEditorLesson.thematic_blocks.push({
                title: "Nouvelle Thématique",
                timestamp: "0:00",
                start_seconds: 0,
                subthemes: [{ title: "Nouveau sous-thème", htmlContent: "" }]
            });
            document.getElementById('transcript-editor-content').innerHTML = renderTranscriptEditorHTML(transcriptEditorLesson);
        };

        window.addSubTheme = function(bIdx) {
            transcriptEditorLesson.thematic_blocks[bIdx].subthemes = transcriptEditorLesson.thematic_blocks[bIdx].subthemes || [];
            transcriptEditorLesson.thematic_blocks[bIdx].subthemes.push({ title: "Nouveau sous-thème", htmlContent: "" });
            flushEditorDOMToState();
            document.getElementById('transcript-editor-content').innerHTML = renderTranscriptEditorHTML(transcriptEditorLesson);
        };

        window.deleteSubTheme = function(bIdx, sIdx) {
            if(confirm("Supprimer ce sous-thème ?")) {
                flushEditorDOMToState();
                transcriptEditorLesson.thematic_blocks[bIdx].subthemes.splice(sIdx, 1);
                document.getElementById('transcript-editor-content').innerHTML = renderTranscriptEditorHTML(transcriptEditorLesson);
            }
        };

        window.moveMainTheme = function(bIdx, dir) {
            flushEditorDOMToState();
            const blocks = transcriptEditorLesson.thematic_blocks;
            if (bIdx + dir >= 0 && bIdx + dir < blocks.length) {
                const temp = blocks[bIdx];
                blocks[bIdx] = blocks[bIdx + dir];
                blocks[bIdx + dir] = temp;
                document.getElementById('transcript-editor-content').innerHTML = renderTranscriptEditorHTML(transcriptEditorLesson);
            }
        };

        window.moveSubTheme = function(bIdx, sIdx, dir) {
            flushEditorDOMToState();
            const subthemes = transcriptEditorLesson.thematic_blocks[bIdx].subthemes;
            if (sIdx + dir >= 0 && sIdx + dir < subthemes.length) {
                const temp = subthemes[sIdx];
                subthemes[sIdx] = subthemes[sIdx + dir];
                subthemes[sIdx + dir] = temp;
                document.getElementById('transcript-editor-content').innerHTML = renderTranscriptEditorHTML(transcriptEditorLesson);
            }
        };

        window.moveSubthemeToMain = function(fromBIdx, sIdx, toBIdx) {
            toBIdx = parseInt(toBIdx);
            if(fromBIdx === toBIdx) return;
            flushEditorDOMToState();
            const subtheme = transcriptEditorLesson.thematic_blocks[fromBIdx].subthemes.splice(sIdx, 1)[0];
            transcriptEditorLesson.thematic_blocks[toBIdx].subthemes = transcriptEditorLesson.thematic_blocks[toBIdx].subthemes || [];
            transcriptEditorLesson.thematic_blocks[toBIdx].subthemes.push(subtheme);
            document.getElementById('transcript-editor-content').innerHTML = renderTranscriptEditorHTML(transcriptEditorLesson);
        };

        function flushEditorDOMToState() {
            const blocks = transcriptEditorLesson.thematic_blocks || [];
            document.querySelectorAll('.thematic-block-card').forEach(card => {
                const bIdx = parseInt(card.dataset.bidx);
                if (blocks[bIdx]) {
                    blocks[bIdx].title = card.querySelector('.main-theme-title-input').value;
                    blocks[bIdx].timestamp = card.querySelector('.main-theme-ts-input').value;
                    
                    const tsParts = blocks[bIdx].timestamp.split(':');
                    if(tsParts.length === 2) blocks[bIdx].start_seconds = parseInt(tsParts[0])*60 + parseInt(tsParts[1]);
                    
                    blocks[bIdx].subthemes = [];
                    card.querySelectorAll('.subtheme-card').forEach(subCard => {
                        blocks[bIdx].subthemes.push({
                            title: subCard.querySelector('.subtheme-title-input').value,
                            htmlContent: subCard.querySelector('.subtheme-html-input').value
                        });
                    });
                }
            });
        }
"""

# 2. Replace saveFullTranscript
new_save = """
        async function saveFullTranscript() {
            flushEditorDOMToState();
            const saveBtn = document.getElementById('save-transcript-btn');
            if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = '⏳ Enregistrement...'; }

            try {
                const response = await fetch('/admin/save-transcript', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        subject: transcriptEditorLesson.subject,
                        lessonNum: transcriptEditorLesson.lessonNum,
                        thematic_blocks: transcriptEditorLesson.thematic_blocks
                    })
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    showNotification('✅ Enregistré avec succès !', 'success');
                    await loadDashboardData(true);
                    closeTranscriptDrawer();
                } else {
                    showNotification('❌ Erreur : ' + data.message, 'error');
                }
            } catch (err) {
                console.error(err);
                showNotification('❌ Erreur de connexion', 'error');
            }
            if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = '💾 Enregistrer les modifications'; }
        }
"""


# Regex replacement for renderTranscriptEditorHTML
pattern_render = re.compile(r'function renderTranscriptEditorHTML\(lesson\) \{.*?(?=async function saveFullTranscript)', re.DOTALL)
content = pattern_render.sub(new_render_html + "\n\n", content)

# Regex replacement for saveFullTranscript
pattern_save = re.compile(r'async function saveFullTranscript\(\) \{.*?(?=function closeTranscriptDrawer)', re.DOTALL)
content = pattern_save.sub(new_save + "\n\n", content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("admin.js patched successfully.")
