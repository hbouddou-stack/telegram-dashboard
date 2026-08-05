import sys

with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    js = f.read()

search = '''                        // CARD VIEW

                        html += `

                            <div class="settings-card" style="flex-direction: column; align-items: stretch; padding: 20px; min-height: 180px; display: flex; justify-content: space-between; border-top: 4px solid ${subColor}; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); border-radius: 12px; background: var(--surface);">

                                <div>

                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">

                                        <span class="badge" style="background: ${subColor}22; color: ${subColor}; font-weight: bold; border: 1px solid ${subColor}44; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem;">${subLabel}</span>

                                        <span style="font-size: 0.85rem; color: var(--text-secondary); font-weight: 500;">\\u0627\\u0644\\u062f\\u0631\\u0633 ${lesson.lessonNum}</span>

                                    </div>

                                    <h3 style="margin: 0 0 10px 0; font-size: 1.1rem; color: var(--text-primary); font-weight: 600;">${lesson.title || `\\u0627\\u0644\\u062f\\u0631\\u0633 ${lesson.lessonNum}`}</h3>

                                    <p style="margin: 0 0 15px 0; font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">

                                        ${lesson.full_text ? lesson.full_text.substring(0, 150) + '...' : '\\u0644\\u0627 \\u064a\\u0648\\u062c\\u062f \\u0646\\u0635 \\u0644\\u0644\\u062a\\u0641\\u0631\\u064a\\u063a'}

                                    </p>

                                </div>'''

replace = '''                        // CARD VIEW (HYBRID ACCORDION)
                        let axesHtml = '';
                        const blocks = lesson.thematic_blocks || [];
                        if (blocks.length === 0) {
                            axesHtml = '<div style="font-size: 0.85rem; color: var(--text-secondary); font-style: italic; margin-bottom: 15px;">لا توجد محاور مسجلة</div>';
                        } else {
                            const visibleBlocks = blocks.slice(0, 3);
                            const hiddenBlocks = blocks.slice(3);
                            const cardId = 'card-axes-' + lesson.subject + '-' + lesson.lessonNum;
                            
                            axesHtml = '<ul style="margin: 0 0 15px 0; padding-right: 20px; font-size: 0.85rem; color: var(--text-secondary); line-height: 1.6;">';
                            visibleBlocks.forEach((b, idx) => {
                                axesHtml += `<li>${escapeHtml(b.title || 'محور ' + (idx + 1))}</li>`;
                            });
                            
                            if (hiddenBlocks.length > 0) {
                                axesHtml += `
                                    <div id="${cardId}" style="display: none; padding-top: 0px;">
                                        ${hiddenBlocks.map((b, i) => `<li>${escapeHtml(b.title || 'محور ' + (i + 4))}</li>`).join('')}
                                    </div>
                                </ul>
                                <div style="text-align: right; margin-top: -10px; margin-bottom: 15px;">
                                    <button onclick="window.toggleCardAccordion('${cardId}', this, ${hiddenBlocks.length})" style="background: transparent; border: none; color: var(--primary); font-size: 0.8rem; cursor: pointer; font-weight: bold; padding: 0;">+ ${hiddenBlocks.length} محاور أخرى ⬇️</button>
                                </div>
                                `;
                            } else {
                                axesHtml += '</ul>';
                            }
                        }

                        html += `

                            <div class="settings-card" style="flex-direction: column; align-items: stretch; padding: 20px; min-height: 150px; display: flex; justify-content: space-between; border-top: 4px solid ${subColor}; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); border-radius: 12px; background: var(--surface);">

                                <div>

                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">

                                        <span class="badge" style="background: ${subColor}22; color: ${subColor}; font-weight: bold; border: 1px solid ${subColor}44; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem;">${subLabel}</span>

                                    </div>

                                    <h3 style="margin: 0 0 10px 0; font-size: 1.1rem; color: var(--text-primary); font-weight: 600;">${lesson.title || `\\u0627\\u0644\\u062f\\u0631\\u0633 ${lesson.lessonNum}`}</h3>

                                    ${axesHtml}

                                </div>'''

js = js.replace(search, replace)

search_func = '''        window.toggleLessonDetails = function(id) {'''
replace_func = '''        window.toggleCardAccordion = function(cardId, btn, count) {
            const el = document.getElementById(cardId);
            if (el) {
                if (el.style.display === 'none') {
                    el.style.display = 'block';
                    btn.innerHTML = `إخفاء المحاور ⬆️`;
                } else {
                    el.style.display = 'none';
                    btn.innerHTML = `+ ${count} محاور أخرى ⬇️`;
                }
            }
        };

        window.toggleLessonDetails = function(id) {'''

js = js.replace(search_func, replace_func)

with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
    f.write(js)
