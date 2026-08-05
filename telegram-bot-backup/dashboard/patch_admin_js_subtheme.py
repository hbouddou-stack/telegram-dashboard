import re

file_path = "admin.js"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_func = """
        window.importSelectionToNewSubTheme = function() {
            const fullTxtArea = document.getElementById('full-transcript-textarea');
            if (!fullTxtArea || !currentAxesEditing) return;
            
            const start = fullTxtArea.selectionStart;
            const end = fullTxtArea.selectionEnd;
            const selectedText = fullTxtArea.value.substring(start, end).trim();
            if (!selectedText) {
                showToast("⚠️ يرجى تحديد جزء من نص التفريغ الكامل أولاً", "warning");
                return;
            }
            
            let title = prompt("Titre de la sous-thématique :", "Nouvelle sous-thématique");
            if (title === null) return; // User cancelled
            
            const newAx = {
                title: title,
                is_sub_theme: true,
                reading_text: selectedText,
                explanation: '',
                video_link: '',
                poetry_verses: '',
                search_text: selectedText
            };
            
            currentAxesEditing.blocks.splice(activeAxisIdx + 1, 0, newAx);
            activeAxisIdx = activeAxisIdx + 1;
            window.renderAxesSidebar();
            window.loadActiveAxis();
            
            showToast("➕ تم إنشاء sous-thématique جديد بالنص المحدد", "success");
        };

        window.importSelectionToNewAxis = function() {
"""

content = content.replace("        window.importSelectionToNewAxis = function() {", new_func)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Patched admin.js with importSelectionToNewSubTheme")
