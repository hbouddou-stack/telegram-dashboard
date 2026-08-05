import sys
import re

with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Since the previous code had exactly this pattern, I will use regex or exact match
search = '''                        // CARD VIEW (HYBRID ACCORDION)
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

                                </div>

                                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: auto; border-top: 1px solid var(--border); padding-top: 12px; gap: 8px;">

                                    <span style="font-size: 0.8rem; color: var(--text-secondary); font-weight: 500;">\\ud83e\\udde9 ${segmentsCount} \\u0641\\u0642\\u0631\\u0629</span>

                                    <button class="btn btn-primary btn-sm" style="padding: 6px 12px; font-size: 0.8rem; height: auto;" onclick="openTranscriptDrawer('${lesson.subject}', ${lesson.lessonNum})">

                                        \\ud83d\\udcdd \\u062a\\u062d\\u0631\\u064a\\u0631 \\u0627\\u0644\\u062a\\u0641\\u0631\\u064a\\u063a

                                    </button>

                                </div>

                            </div>

                        `;'''

replace = '''                        // CARD VIEW (TAGS DESIGN)
                        let axesHtml = '';
                        const blocks = lesson.thematic_blocks || [];
                        if (blocks.length === 0) {
                            axesHtml = '<div style="font-size: 0.85rem; color: var(--text-secondary); font-style: italic; margin-bottom: 15px;">لا توجد محاور مسجلة</div>';
                        } else {
                            axesHtml = '<div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 15px;">';
                            blocks.forEach((b, idx) => {
                                axesHtml += `<span style="background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-secondary); padding: 4px 10px; border-radius: 20px; font-size: 0.78rem; display: flex; align-items: center; gap: 4px;"><strong style="color: var(--primary); font-size: 0.85rem;">${idx + 1}.</strong> <span>${escapeHtml(b.title || 'محور')}</span></span>`;
                            });
                            axesHtml += '</div>';
                        }

                        html += `

                            <div class="settings-card" style="flex-direction: column; align-items: stretch; padding: 20px; min-height: 150px; display: flex; justify-content: space-between; border-top: 4px solid ${subColor}; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); border-radius: 12px; background: var(--surface);">

                                <div>

                                    <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 15px;">

                                        <span class="badge" style="background: ${subColor}22; color: ${subColor}; font-weight: bold; border: 1px solid ${subColor}44; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">${subLabel}</span>
                                        <span class="badge" style="background: var(--surface-hover); color: var(--text-primary); font-weight: bold; border: 1px solid var(--border); padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">\\u0627\\u0644\\u062f\\u0631\\u0633 ${lesson.lessonNum}</span>

                                    </div>

                                    <h3 style="margin: 0 0 12px 0; font-size: 1.15rem; color: var(--text-primary); font-weight: 700;">${lesson.title || `\\u0627\\u0644\\u062f\\u0631\\u0633 ${lesson.lessonNum}`}</h3>

                                    ${axesHtml}

                                </div>

                                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: auto; border-top: 1px solid var(--border); padding-top: 14px; gap: 8px;">

                                    <span style="font-size: 0.85rem; color: var(--text-secondary); font-weight: bold;">📌 ${blocks.length} محاور</span>

                                    <button class="btn btn-primary btn-sm" style="padding: 6px 14px; font-size: 0.85rem; height: auto; border-radius: 8px; font-weight: bold;" onclick="openTranscriptDrawer('${lesson.subject}', ${lesson.lessonNum})">
                                        📝 تحرير
                                    </button>

                                </div>

                            </div>

                        `;'''

js = js.replace(search, replace)

with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
    f.write(js)
