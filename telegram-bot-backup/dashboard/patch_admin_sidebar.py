import re

file_path = "admin.js"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_render = """
        window.renderAxesSidebar = function() {
            const listEl = document.getElementById('axes-sidebar-list');
            if (!listEl || !currentAxesEditing) return;

            listEl.innerHTML = '';
            if (currentAxesEditing.blocks.length === 0) {
                listEl.innerHTML = '<div style="color: var(--text-secondary); text-align: center; padding: 20px 0; font-size: 0.85rem;">لا توجد محاور. اضغط على الزر أدناه لإضافة محور.</div>';
                return;
            }

            let mainCounter = 0;
            let subCounter = 0;

            currentAxesEditing.blocks.forEach((block, idx) => {
                const isSub = !!block.is_sub_theme;
                let displayNum = "";
                
                if (isSub) {
                    subCounter++;
                    displayNum = `${mainCounter}.${subCounter}`;
                } else {
                    mainCounter++;
                    subCounter = 0;
                    displayNum = `${mainCounter}`;
                }

                const item = document.createElement('div');
                item.className = `axis-item ${idx === activeAxisIdx ? 'active' : ''}`;
                if (isSub) {
                    item.style.cssText = "margin-right: 25px; border-right: 3px solid #10b981; padding-right: 10px; background: rgba(16, 185, 129, 0.05); border-radius: 4px;";
                }
                
                item.setAttribute('data-idx', idx);
                item.onclick = () => {
                    activeAxisIdx = idx;
                    window.renderAxesSidebar();
                    window.loadActiveAxis();
                };

                item.innerHTML = `
                    <span class="axis-item-title">${displayNum}. ${escapeHtml(block.title || 'بدون عنوان')}</span>
                    <div class="axis-actions" onclick="event.stopPropagation();">
                        <button class="axis-action-btn" onclick="window.moveAxisUp(${idx})" title="نقل للأعلى">🔼</button>
                        <button class="axis-action-btn" onclick="window.moveAxisDown(${idx})" title="نقل للأسفل">🔽</button>
                        <button class="axis-action-btn" onclick="window.deleteAxis(${idx})" title="حذف المحور">❌</button>
                    </div>
                `;
                listEl.appendChild(item);
            });
        }
"""

pattern = re.compile(r'window\.renderAxesSidebar = function\(\) \{.*?(?=window\.updateChronoFromInputs = function)', re.DOTALL)
match = pattern.search(content)

if match:
    content = content[:match.start()] + new_render + "\n        " + content[match.end():]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched renderAxesSidebar")
else:
    print("Could not find renderAxesSidebar")
