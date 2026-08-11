import re

with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace formatExplanationHtml entirely
new_func = '''    formatExplanationHtml(explanation) {
        if (!explanation) return "";
        let text = explanation;
        text = text.replace("📌 <b>ملاحظة الأستاذ</b> :", "📌 <b>ملاحظة الأستاذ :</b>");
        text = text.replace("📌 <b>ملاحظة الأستاذ</b>", "📌 <b>ملاحظة الأستاذ :</b>");
        
        let pedagogicalText = "";
        let profNote = "";
        let sourceText = "";
        
        if (text.includes("💡 <b>الشرح التربوي</b> :")) {
            let parts = text.split("💡 <b>الشرح التربوي</b> :");
            let afterTitle = parts[1] || "";
            if (text.includes("📌 <b>ملاحظة الأستاذ :</b>")) {
                let subparts = afterTitle.split("📌 <b>ملاحظة الأستاذ :</b>");
                pedagogicalText = subparts[0];
                let rest = subparts[1];
                if (text.includes("📚 <b>المصدر :</b>")) {
                    let subsub = rest.split("📚 <b>المصدر :</b>");
                    profNote = subsub[0];
                    sourceText = subsub[1];
                } else {
                    profNote = rest;
                }
            } else if (text.includes("📚 <b>المصدر :</b>")) {
                let subparts = afterTitle.split("📚 <b>المصدر :</b>");
                pedagogicalText = subparts[0];
                sourceText = subparts[1];
            } else {
                pedagogicalText = afterTitle;
            }
        } else {
            let temp = document.createElement('div');
            temp.innerHTML = text;
            pedagogicalText = temp.textContent || "";
        }
        
        let html = "";
        if (pedagogicalText.trim()) {
            html += <div style="margin-bottom:12px; font-size:15px; color:var(--text); line-height:1.6;"><strong>الشرح التربوي:</strong><br></div>;
        }
        if (profNote.trim()) {
            html += <div style="margin-bottom:12px; background:var(--surface-2); padding:12px; border-radius:8px; border-right:3px solid var(--primary); font-size:14.5px;"><span style="font-size:16px;">📌</span> <strong>ملاحظة الأستاذ:</strong><br></div>;
        }
        if (sourceText.trim()) {
            html += <div style="font-size:13px; color:var(--text-3); margin-top:8px;">📚 <strong>المصدر:</strong> </div>;
        }
        if(!html) {
            html = <div style="margin-bottom:12px; font-size:15px;"></div>;
        }
        return html;
    },'''

js = re.sub(r'formatExplanationHtml\(explanation\) \{.*?\},\s*showQuestion\(\) \{', new_func + '\n\n    showQuestion() {', js, flags=re.DOTALL)

with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(js)
