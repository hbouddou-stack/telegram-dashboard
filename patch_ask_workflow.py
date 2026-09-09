import io

with io.open('dashboard/ask.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update submitTicket
old_submit = """async function submitTicket() {
            const customTitleInput = document.getElementById('custom-ticket-title');
            if (selectedSubtheme === 'مشكلة أخرى' && customTitleInput) {
                const ct = customTitleInput.value.trim();
                if (!ct) { alert("يرجى كتابة عنوان مختصر للموضوع."); return; }
                selectedSubtheme = ct;
            }
            const msg = document.getElementById('message').value.trim();
            if (!msg) { alert("يرجى كتابة رسالتك بوضوح."); return; }
            const btn = document.getElementById('btn-submit');
            btn.textContent = "جاري البحث...";
            btn.disabled = true;
            try {
                const ragRes = await fetch(`${BOT_BASE}/api/support/rag_check`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ theme: selectedTheme, subtheme: selectedSubtheme, message: msg })
                });
                const ragData = await ragRes.json();
                if (ragData.found) {
                    document.getElementById('rag-answer-text').innerText = ragData.answer;
                    goToStep(4);
                    btn.textContent = "&#128640; إرسال";
                    btn.disabled = false;
                    return;
                }
            } catch (e) { console.error("RAG Error", e); }
            escalateTicket(false);
        }"""

new_submit = """async function submitTicket() {
            const customTitleInput = document.getElementById('custom-ticket-title');
            if (selectedSubtheme === 'مشكلة أخرى' && customTitleInput) {
                const ct = customTitleInput.value.trim();
                if (!ct) { alert("يرجى كتابة عنوان مختصر للموضوع."); return; }
                selectedSubtheme = ct;
            }
            const msg = document.getElementById('message').value.trim();
            if (!msg) { alert("يرجى كتابة رسالتك بوضوح."); return; }
            const btn = document.getElementById('btn-submit');
            btn.textContent = "جاري الإرسال...";
            btn.disabled = true;
            let aiAnswer = null;
            try {
                const ragRes = await fetch(`${BOT_BASE}/api/support/rag_check`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ theme: selectedTheme, subtheme: selectedSubtheme, message: msg })
                });
                const ragData = await ragRes.json();
                if (ragData.found) {
                    aiAnswer = ragData.answer;
                }
            } catch (e) { console.error("RAG Error", e); }
            
            await escalateTicket(aiAnswer === null, aiAnswer);
            btn.textContent = "إرسال";
            btn.disabled = false;
        }"""

html = html.replace(old_submit, new_submit)

# 2. Update escalateTicket
old_esc = """async function escalateTicket(ragFailed = true) {"""
new_esc = """async function escalateTicket(ragFailed = true, aiReply = null) {"""
html = html.replace(old_esc, new_esc)

old_fetch = """try {
                await fetch(`${BOT_BASE}/api/support`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        theme: selectedTheme, 
                        subtheme: selectedSubtheme, 
                        message: msg, 
                        telegram_id: tid, 
                        username, 
                        first_name, 
                        rag_failed: ragFailed,
                        file_data: initialFileData,
                        file_name: initialFileName
                    })
                });
                document.getElementById('support-form').style.display = 'none';
                document.getElementById('success-screen').style.display = 'block';
            } catch"""

new_fetch = """try {
                const res = await fetch(`${BOT_BASE}/api/support`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        theme: selectedTheme, 
                        subtheme: selectedSubtheme, 
                        message: msg, 
                        telegram_id: tid, 
                        username, 
                        first_name, 
                        auto_resolved: aiReply !== null,
                        ai_reply: aiReply,
                        file_data: initialFileData,
                        file_name: initialFileName
                    })
                });
                // Switch to inbox and open this ticket immediately
                document.getElementById('message').value = '';
                goToStep(1); // reset form
                switchTab('inbox');
                await loadStudentTickets();
            } catch"""
html = html.replace(old_fetch, new_fetch)

with io.open('dashboard/ask.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Patch complete for submit/escalate workflow')
