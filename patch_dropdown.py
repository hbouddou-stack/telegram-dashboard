import re
import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

fetch_injection = """
                if(data.success) {
                    allStudents = data.students;
                    
                    // Build dynamic Excel files dropdown
                    const sourceSelect = document.getElementById('source-select');
                    const currentVal = sourceSelect.value;
                    let opts = `<option value="all">📁 كل المصادر</option>
                                <option value="excel">📗 Excel (الكل)</option>
                                <option value="sheet">📊 Sheet</option>
                                <option value="manuel">✍️ يدوي</option>`;
                    
                    const excelFiles = [...new Set(allStudents.filter(s => s.source === 'excel' && s.source_file).map(s => s.source_file))];
                    excelFiles.forEach(f => {
                        opts += `<option value="file:${f}">📄 ${f}</option>`;
                    });
                    sourceSelect.innerHTML = opts;
                    if (opts.includes(`value="${currentVal}"`)) sourceSelect.value = currentVal;
"""

html = re.sub(
    r'if\(\s*data\.success\s*\)\s*\{\s*allStudents\s*=\s*data\.students;',
    fetch_injection,
    html,
    count=1
)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Successfully injected dynamic dropdown!")
