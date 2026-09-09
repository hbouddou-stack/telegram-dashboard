import io

with io.open('dashboard/ask.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_sub = """            let aiAnswer = null;
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
            
            await escalateTicket(aiAnswer === null, aiAnswer);"""

new_sub = """            let aiAnswer = null;
            let storyId = null;
            try {
                const ragRes = await fetch(`${BOT_BASE}/api/support/rag_check`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ theme: selectedTheme, subtheme: selectedSubtheme, message: msg })
                });
                const ragData = await ragRes.json();
                if (ragData.found) {
                    aiAnswer = ragData.answer;
                    if (ragData.story_id !== undefined) storyId = ragData.story_id;
                }
            } catch (e) { console.error("RAG Error", e); }
            
            await escalateTicket(aiAnswer === null, aiAnswer, storyId);"""
html = html.replace(old_sub, new_sub)

old_esc = """async function escalateTicket(ragFailed = true, aiReply = null) {"""
new_esc = """async function escalateTicket(ragFailed = true, aiReply = null, storyId = null) {"""
html = html.replace(old_esc, new_esc)

old_fetch = """                        auto_resolved: aiReply !== null,
                        ai_reply: aiReply,
                        file_data: initialFileData,
                        file_name: initialFileName
                    })"""

new_fetch = """                        auto_resolved: aiReply !== null,
                        ai_reply: aiReply,
                        story_id: storyId,
                        file_data: initialFileData,
                        file_name: initialFileName
                    })"""
html = html.replace(old_fetch, new_fetch)

with io.open('dashboard/ask.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Patch frontend for story_id')
