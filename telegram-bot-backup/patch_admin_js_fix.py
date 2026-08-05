import re

def fix():
    with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and remove all occurrences of loadAdminThematics
    pattern = r'async function loadAdminThematics\(\) \{[\s\S]*?console\.error\("Error loading thematics:", e\);\s*\}\s*\}'
    content = re.sub(pattern, '', content)

    correct_load = """async function loadAdminThematics() {
    const subject = document.getElementById('curriculum-subject-filter').value;
    const yearEl = document.getElementById('curriculum-year-filter');
    const year = yearEl ? yearEl.value : '';
    
    const container = document.getElementById('miller-columns-container');
    if (container) {
        container.className = 'miller-columns-container'; // reset
    }
    
    try {
        const response = await fetch('/admin/thematics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: state.userId, subject: subject, academic_year: year })
        });
        const data = await response.json();
        if (data.success) {
            curriculumData = data;
            selectedPath = {};
            renderCurriculum();
        } else {
            console.error("Failed to load thematics:", data.error);
        }
    } catch (e) {
        console.error("Error loading thematics:", e);
    }
}
"""

    content = content.replace('function renderCurriculum() {', correct_load + '\nfunction renderCurriculum() {')

    with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix()
