import sys

file_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\dashboard\admin.js'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "<button class=\"miller-item-btn\" title=\"تعديل\"" in line:
        # Inject view button before edit button
        view_btn = "                    <button class=\"miller-item-btn\" title=\"عرض الأسئلة\" onclick=\"event.stopPropagation(); viewNodeQuestions(${item.id}, '${title.replace(/'/g, \"\\\\'\")}')\">👁️</button>\n"
        new_lines.append(view_btn)
    
    new_lines.append(line)

js_functions = '''
async function viewNodeQuestions(nodeId, nodeTitle) {
    document.getElementById('node-questions-title').innerText = "الأسئلة المصنفة في: " + nodeTitle;
    const list = document.getElementById('node-questions-list');
    list.innerHTML = '<div style="text-align:center; padding:20px;">جاري التحميل...</div>';
    document.getElementById('node-questions-modal').style.display = 'flex';
    
    try {
        const response = await fetch('/admin/thematics/node_questions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: state.userId, node_id: nodeId })
        });
        const data = await response.json();
        
        if (data.success) {
            if (!data.questions || data.questions.length === 0) {
                list.innerHTML = '<div style="text-align:center; color: var(--text-secondary); padding: 20px;">لا يوجد أسئلة مصنفة في هذه العقدة</div>';
            } else {
                let html = '';
                data.questions.forEach(q => {
                    const text = q.question ? q.question.substring(0, 150) : 'بدون نص';
                    html += `
                        <div style="background: var(--surface-hover); border: 1px solid var(--border); padding: 10px; border-radius: 8px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <span class="question-id-badge">#${q.id}</span>
                                <span style="font-size: 0.8rem; color: var(--text-secondary);">${q.subject || ''} - درس ${q.course_number || '?'}</span>
                            </div>
                            <div style="font-size: 0.95rem;">${text}</div>
                        </div>
                    `;
                });
                list.innerHTML = html;
            }
        } else {
            list.innerHTML = `<div style="color: red; padding: 20px;">خطأ: ${data.error}</div>`;
        }
    } catch (e) {
        list.innerHTML = `<div style="color: red; padding: 20px;">خطأ في الاتصال</div>`;
    }
}

function closeNodeQuestionsModal() {
    document.getElementById('node-questions-modal').style.display = 'none';
}
'''

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    f.write(js_functions)

print("Patched admin.js successfully")
