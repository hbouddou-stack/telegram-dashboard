import io

with io.open('dashboard/ask.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_pills = """            <!-- Quick Filter Tabs (Pills) -->
            <div id="inbox-filter-pills" style="display:flex; gap:8px; overflow-x:auto; padding-bottom:12px; margin-bottom:15px; scrollbar-width:none;">
                <button class="faq-cat-btn active" id="pill-all" onclick="filterStudentInbox('all', this)">📋 الكل (<span id="cnt-all">0</span>)</button>
                <button class="faq-cat-btn" id="pill-pending" onclick="filterStudentInbox('pending', this)">⏳ قيد الانتظار (<span id="cnt-pending">0</span>)</button>
                <button class="faq-cat-btn" id="pill-resolved" onclick="filterStudentInbox('resolved', this)">🟢 تم الحل (<span id="cnt-resolved">0</span>)</button>
            </div>"""

new_pills = """            <!-- Quick Filter Tabs (Pills) -->
            <div id="inbox-filter-pills" style="display:flex; gap:8px; overflow-x:auto; padding-bottom:12px; margin-bottom:15px; scrollbar-width:none;">
                <button class="faq-cat-btn active" id="pill-all" onclick="filterStudentInbox('all', this)">💬 الإدارة (<span id="cnt-all">0</span>)</button>
                <button class="faq-cat-btn" id="pill-pending" onclick="filterStudentInbox('pending', this)">⏳ قيد الانتظار (<span id="cnt-pending">0</span>)</button>
                <button class="faq-cat-btn" id="pill-ai" onclick="filterStudentInbox('ai', this)">🤖 السجل الذكي (<span id="cnt-ai">0</span>)</button>
            </div>"""

html = html.replace(old_pills, new_pills)

old_render = """            // Count for filter pills
            const resolvedList = studentAllTicketsList.filter(t => t.status === 'resolved' || t.status === 'محلولة');
            const pendingList = studentAllTicketsList.filter(t => !resolvedList.includes(t));
            
            const cntAll = document.getElementById('cnt-all');
            const cntPending = document.getElementById('cnt-pending');
            const cntResolved = document.getElementById('cnt-resolved');
            if (cntAll) cntAll.innerText = studentAllTicketsList.length;
            if (cntPending) cntPending.innerText = pendingList.length;
            if (cntResolved) cntResolved.innerText = resolvedList.length;"""

new_render = """            // Split into AI and Human tickets
            const aiList = studentAllTicketsList.filter(t => t.is_ghost == 1);
            const humanList = studentAllTicketsList.filter(t => t.is_ghost != 1);
            
            // Count for filter pills
            const resolvedList = humanList.filter(t => t.status === 'resolved' || t.status === 'محلولة');
            const pendingList = humanList.filter(t => !resolvedList.includes(t));
            
            const cntAll = document.getElementById('cnt-all');
            const cntPending = document.getElementById('cnt-pending');
            const cntAi = document.getElementById('cnt-ai');
            if (cntAll) cntAll.innerText = humanList.length;
            if (cntPending) cntPending.innerText = pendingList.length;
            if (cntAi) cntAi.innerText = aiList.length;"""

html = html.replace(old_render, new_render)

old_display = """            // Filter according to active pill
            let displayTickets = [...studentAllTicketsList];
            if (activeInboxFilter === 'pending') {
                displayTickets = pendingList;
            } else if (activeInboxFilter === 'resolved') {
                displayTickets = resolvedList;
            }"""

new_display = """            // Filter according to active pill
            let displayTickets = [...humanList];
            if (activeInboxFilter === 'pending') {
                displayTickets = pendingList;
            } else if (activeInboxFilter === 'ai') {
                displayTickets = aiList;
            }"""

html = html.replace(old_display, new_display)

with io.open('dashboard/ask.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Patch complete for inbox filters')
