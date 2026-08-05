import sys

filepath = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\dashboard\admin.js'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []

for i, line in enumerate(lines):
    if '<div class="miller-item ${isSelected ? \'selected\' : \'\'}" onclick="selectCurriculumNode(${level}, ${item.id})" data-id="${item.id}">' in line:
        line = line.replace('<div class="miller-item ${isSelected ? \'selected\' : \'\'}" onclick="selectCurriculumNode(${level}, ${item.id})" data-id="${item.id}">',
                            '<div class="miller-item ${isSelected ? \'selected\' : \'\'}" draggable="true" ondragstart="dragNode(event, ${level}, ${item.id})" ondragover="allowDrop(event)" ondragleave="dragLeaveNode(event)" ondrop="dropNode(event, ${level}, ${item.id})" onclick="selectCurriculumNode(${level}, ${item.id})" data-id="${item.id}">')
    
    new_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

code_to_add = '''
function dragNode(ev, level, nodeId) {
    ev.dataTransfer.setData("nodeId", nodeId);
    ev.dataTransfer.setData("nodeLevel", level);
    ev.dataTransfer.effectAllowed = "move";
}

function dragLeaveNode(ev) {
    ev.currentTarget.classList.remove('drag-over');
}

async function dropNode(ev, level, targetNodeId) {
    const questionId = ev.dataTransfer.getData("questionId");
    if (questionId) {
        // It's a question, let it bubble up, but we remove drag-over
        ev.currentTarget.classList.remove('drag-over');
        return; 
    }
    
    ev.preventDefault();
    ev.stopPropagation();
    ev.currentTarget.classList.remove('drag-over');
    
    const sourceNodeId = ev.dataTransfer.getData("nodeId");
    const sourceLevel = ev.dataTransfer.getData("nodeLevel");
    
    if (!sourceNodeId || sourceLevel != level || sourceNodeId == targetNodeId) return;
    
    try {
        const response = await fetch('/admin/thematics/reorder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                userId: state.userId,
                source_node_id: parseInt(sourceNodeId),
                target_node_id: parseInt(targetNodeId),
                level: parseInt(level)
            })
        });
        
        const data = await response.json();
        if (data.success) {
            loadCurriculum();
            if (!window.silent) showToast("تم تغيير الترتيب بنجاح", "success");
        } else {
            alert("Error: " + data.error);
        }
    } catch (err) {
        console.error("Reorder error:", err);
    }
}
'''

with open(filepath, 'a', encoding='utf-8') as f:
    f.write('\n' + code_to_add)

print('Updated admin.js successfully')
