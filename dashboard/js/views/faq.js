// faq.js - FAQ Manager v2 - Connecte a SQLite via API

let faqAllEntries = [];
let faqCategories = [];
let faqActiveCategory = null;
let faqActiveSubcategory = null;
let faqEditId = null;

export function initFaqView(container) {
    container.innerHTML = `
        <section class="view active module-view" style="position:relative; background: var(--bg); overflow-y: auto; height: 100vh;">
            <header class="app-header" style="border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 10; background: var(--surface-solid);">
                <div class="header-left">
                    <button class="hamburger-btn" onclick="toggleSidebar()">&#9776;</button>
                    <div class="header-titles">
                        <h1>&#129504; مدير FAQ</h1>
                        <span class="header-subtitle" id="faq-count-label">جاري التحميل...</span>
                    </div>
                </div>
                <div style="display:flex; gap: 8px; align-items:center;">
                    <button onclick="window.openFaqSuggestions()" style="padding: 8px 14px; border-radius:20px; font-size:0.85rem; background:rgba(52,152,219,0.2); color:#3498db; border:1px solid #3498db; cursor:pointer; font-family:Tajawal,sans-serif;">
                        &#128161; اقتراحات AI
                    </button>
                    <button onclick="window.openFaqModal()" style="padding: 8px 15px; border-radius: 20px; font-weight: bold; display: flex; gap: 5px; align-items: center; border: none; background: var(--accent); color: white; cursor: pointer; font-family:Tajawal,sans-serif;">
                        + إضافة سؤال
                    </button>
                </div>
            </header>

            <div style="padding: 15px 20px; background: var(--surface); border-bottom: 1px solid var(--border);">
                <input id="faq-search" type="text" placeholder="&#128269; ابحث في الأسئلة..."
                    style="width:100%; box-sizing:border-box; padding:10px 15px; border-radius:25px; border:1px solid var(--border); background:var(--bg); color:var(--text-1); font-family:Tajawal,sans-serif; font-size:1rem;"
                    oninput="window.faqSearch(this.value)" />
            </div>

            <div id="faq-category-filters" style="display:flex; gap:8px; overflow-x:auto; padding:12px 20px; border-bottom:1px solid var(--border); scrollbar-width:none;">
                <button class="faq-cat-chip active" data-cat="" onclick="window.faqFilterCategory('', this)"
                    style="white-space:nowrap; padding:6px 16px; border-radius:20px; border:1px solid var(--accent); background:var(--accent); color:white; cursor:pointer; font-family:Tajawal,sans-serif; font-size:0.9rem;">
                    الكل
                </button>
            </div>

            <div id="faq-subcategory-filters" style="display:none; gap:8px; overflow-x:auto; padding:8px 20px; border-bottom:1px solid var(--border); background:rgba(0,0,0,0.1); scrollbar-width:none;"></div>

            <div id="faq-stats-bar" style="display:flex; gap:20px; padding:12px 20px; background:rgba(135,54,255,0.05); border-bottom:1px solid var(--border); font-size:0.85rem; color:var(--text-2);">
                <span>&#128218; إجمالي الأسئلة: <strong id="stat-total">&#8212;</strong></span>
                <span>&#128065; إجمالي المشاهدات: <strong id="stat-views">&#8212;</strong></span>
                <span>&#128077; مفيد: <strong id="stat-helpful">&#8212;</strong></span>
            </div>

            <div id="faq-list" style="padding: 20px; max-width: 900px; margin: 0 auto; padding-bottom: 80px;">
                <div style="text-align:center; padding:40px; color:var(--text-2);">جاري تحميل الأسئلة...</div>
            </div>
        </section>

        <div id="faq-modal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.75); z-index:1000; align-items:center; justify-content:center; padding:20px;">
            <div style="background:var(--surface-solid); border-radius:16px; padding:25px; width:100%; max-width:600px; border:1px solid var(--border); max-height:90vh; overflow-y:auto;">
                <h2 id="faq-modal-title" style="margin:0 0 20px 0; color:var(--accent);">+ إضافة سؤال جديد</h2>
                <div style="margin-bottom:15px;">
                    <label style="display:block; margin-bottom:6px; color:var(--text-2); font-size:0.9rem;">القسم *</label>
                    <div style="display:flex; gap:8px;">
                        <input id="faq-input-category" type="text" placeholder="مثال: التقنية، الدفع..."
                            style="flex:1; padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text-1); font-family:Tajawal,sans-serif;" />
                        <select id="faq-cat-select" onchange="document.getElementById('faq-input-category').value=this.value"
                            style="padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text-1); font-family:Tajawal,sans-serif;">
                            <option value="">-- اختر --</option>
                        </select>
                    </div>
                </div>
                <div style="margin-bottom:15px;">
                    <label style="display:block; margin-bottom:6px; color:var(--text-2); font-size:0.9rem;">القسم الفرعي</label>
                    <input id="faq-input-subcategory" type="text" placeholder="اختياري"
                        style="width:100%; box-sizing:border-box; padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text-1); font-family:Tajawal,sans-serif;" />
                </div>
                <div style="margin-bottom:15px;">
                    <label style="display:block; margin-bottom:6px; color:var(--text-2); font-size:0.9rem;">السؤال *</label>
                    <textarea id="faq-input-question" rows="3" placeholder="اكتب السؤال..."
                        style="width:100%; box-sizing:border-box; padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text-1); font-family:Tajawal,sans-serif; resize:vertical;"></textarea>
                </div>
                <div style="margin-bottom:20px;">
                    <label style="display:block; margin-bottom:6px; color:var(--text-2); font-size:0.9rem;">الجواب *</label>
                    <textarea id="faq-input-answer" rows="5" placeholder="اكتب الجواب الكامل..."
                        style="width:100%; box-sizing:border-box; padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text-1); font-family:Tajawal,sans-serif; resize:vertical;"></textarea>
                </div>
                <div style="display:flex; gap:10px; justify-content:flex-end;">
                    <button onclick="window.closeFaqModal()"
                        style="padding:10px 20px; border-radius:8px; border:1px solid var(--border); background:transparent; color:var(--text-2); cursor:pointer; font-family:Tajawal,sans-serif;">
                        إلغاء
                    </button>
                    <button onclick="window.saveFaqEntry()"
                        style="padding:10px 25px; border-radius:8px; border:none; background:var(--accent); color:white; cursor:pointer; font-weight:bold; font-family:Tajawal,sans-serif;">
                        &#128190; حفظ
                    </button>
                </div>
            </div>
        </div>

        <div id="faq-suggestions-modal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.75); z-index:1000; align-items:center; justify-content:center; padding:20px;">
            <div style="background:var(--surface-solid); border-radius:16px; padding:25px; width:100%; max-width:700px; border:1px solid var(--border); max-height:90vh; overflow-y:auto;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                    <h2 style="margin:0; color:#3498db;">&#128161; اقتراحات FAQ من التذاكر</h2>
                    <button onclick="window.closeFaqSuggestions()" style="background:none; border:none; color:var(--text-2); font-size:1.5rem; cursor:pointer;">&#10005;</button>
                </div>
                <p style="color:var(--text-2); font-size:0.9rem; margin-bottom:20px;">
                    أسئلة مستخرجة تلقائياً من التذاكر المتكررة. اقبلها بنقرة واحدة.
                </p>
                <div id="suggestions-list">
                    <div style="text-align:center; padding:30px; color:var(--text-2);">جاري التحميل...</div>
                </div>
            </div>
        </div>
    `;

    loadFaqData();
    setupFaqGlobals();
}

async function loadFaqData() {
    try {
        const BASE = window.BOT_API_BASE || '';
        const res = await fetch(`${BASE}/api/faq`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'API error');
        faqAllEntries = data.entries || [];
        faqCategories = data.categories || [];
        const totalViews = faqAllEntries.reduce((s, e) => s + (e.views || 0), 0);
        const totalHelpful = faqAllEntries.reduce((s, e) => s + (e.helpful_votes || 0), 0);
        const statTotal = document.getElementById('stat-total');
        const statViews = document.getElementById('stat-views');
        const statHelpful = document.getElementById('stat-helpful');
        const faqCountLabel = document.getElementById('faq-count-label');
        if (statTotal) statTotal.textContent = faqAllEntries.length;
        if (statViews) statViews.textContent = totalViews.toLocaleString('ar');
        if (statHelpful) statHelpful.textContent = totalHelpful.toLocaleString('ar');
        if (faqCountLabel) faqCountLabel.textContent = `${faqAllEntries.length} سؤال في القاعدة`;
        buildCategoryFilters();
        renderFaqList(faqAllEntries);
        populateCategorySelect();
    } catch (e) {
        const el = document.getElementById('faq-list');
        if (el) el.innerHTML = `<div style="color:#e74c3c; padding:20px; text-align:center;">خطأ في تحميل البيانات: ${e.message}</div>`;
    }
}

function buildCategoryFilters() {
    const filtersEl = document.getElementById('faq-category-filters');
    if (!filtersEl) return;
    const cats = [...new Set(faqCategories.map(c => c.category))];
    const colors = ['#8736ff','#3498db','#2ecc71','#e67e22','#e74c3c','#9b59b6','#1abc9c'];
    let html = `<button class="faq-cat-chip active" data-cat="" onclick="window.faqFilterCategory('', this)"
        style="white-space:nowrap; padding:6px 16px; border-radius:20px; border:1px solid var(--accent); background:var(--accent); color:white; cursor:pointer; font-family:Tajawal,sans-serif; font-size:0.9rem;">
        الكل (${faqAllEntries.length})</button>`;
    cats.forEach((cat, i) => {
        const count = faqAllEntries.filter(e => e.category === cat).length;
        const color = colors[i % colors.length];
        html += `<button class="faq-cat-chip" data-cat="${cat}" onclick="window.faqFilterCategory('${cat.replace(/'/g,"\\'")}', this)"
            style="white-space:nowrap; padding:6px 16px; border-radius:20px; border:1px solid ${color}; background:transparent; color:${color}; cursor:pointer; font-family:Tajawal,sans-serif; font-size:0.9rem; transition:all 0.2s;">
            ${cat} (${count})</button>`;
    });
    filtersEl.innerHTML = html;
}

function buildSubcategoryFilters(category) {
    const subEl = document.getElementById('faq-subcategory-filters');
    if (!subEl) return;
    const subs = [...new Set(faqCategories.filter(c => c.category === category && c.subcategory).map(c => c.subcategory))];
    if (subs.length === 0) { subEl.style.display = 'none'; return; }
    subEl.style.display = 'flex';
    let html = `<button class="faq-subcat-chip active" onclick="window.faqFilterSubcategory('', this)"
        style="white-space:nowrap; padding:4px 12px; border-radius:15px; border:1px solid rgba(255,255,255,0.3); background:rgba(255,255,255,0.1); color:var(--text-2); cursor:pointer; font-family:Tajawal,sans-serif; font-size:0.82rem;">
        الكل</button>`;
    subs.forEach(sub => {
        const count = faqAllEntries.filter(e => e.category === category && e.subcategory === sub).length;
        html += `<button class="faq-subcat-chip" onclick="window.faqFilterSubcategory('${sub.replace(/'/g,"\\'")}', this)"
            style="white-space:nowrap; padding:4px 12px; border-radius:15px; border:1px solid rgba(255,255,255,0.2); background:transparent; color:var(--text-2); cursor:pointer; font-family:Tajawal,sans-serif; font-size:0.82rem;">
            ${sub} (${count})</button>`;
    });
    subEl.innerHTML = html;
}

function renderFaqList(entries) {
    const el = document.getElementById('faq-list');
    if (!el) return;
    if (!entries || entries.length === 0) {
        el.innerHTML = `<div style="text-align:center; padding:60px 20px; color:var(--text-2);">
            <div style="font-size:3rem; margin-bottom:15px;">&#128269;</div>
            <div>لا توجد أسئلة في هذا القسم</div>
            <button onclick="window.openFaqModal()" style="margin-top:20px; padding:10px 25px; border-radius:20px; border:none; background:var(--accent); color:white; cursor:pointer; font-family:Tajawal,sans-serif;">
                + إضافة أول سؤال</button></div>`;
        return;
    }
    const grouped = {};
    entries.forEach(e => { const k = e.category || 'عام'; if (!grouped[k]) grouped[k] = []; grouped[k].push(e); });
    const catColors = {'التقنية':'#8736ff','التسجيل':'#3498db','الدفع':'#2ecc71','المنهج':'#e67e22','الشهادات':'#e74c3c'};
    const defaultColors = ['#8736ff','#3498db','#2ecc71','#e67e22','#e74c3c'];
    let colorIdx = 0;
    let html = '';
    Object.entries(grouped).forEach(([cat, catEntries]) => {
        const color = catColors[cat] || defaultColors[colorIdx++ % defaultColors.length];
        html += `<div style="margin-bottom:30px;">
            <h2 style="color:${color}; margin-bottom:15px; border-bottom:2px solid ${color}33; padding-bottom:8px; display:flex; align-items:center; gap:8px; font-size:1.1rem;">
                <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${color};"></span>
                ${cat}
                <span style="font-size:0.8rem; font-weight:normal; color:var(--text-2); background:${color}22; padding:2px 10px; border-radius:10px;">${catEntries.length} سؤال</span>
            </h2>`;
        catEntries.forEach(entry => {
            const isPinned = entry.is_pinned ? '&#128204; ' : '';
            const needsRevision = entry.not_helpful_votes > 0;
            const revisionBadge = needsRevision ? `<span style="background: rgba(231,76,60,0.1); color: #e74c3c; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; border: 1px solid #e74c3c; margin-right: 10px;">⚠️ À réviser</span>` : '';
            const notHelpfulBadge = needsRevision
                ? `<span style="color:#e74c3c; font-size:0.8rem;" title="يحتاج تحسين">&#9888; ${entry.not_helpful_votes} غير مفيد</span>` : '';
            html += `
            <div style="background:var(--surface-solid); border:1px solid ${needsRevision ? '#e74c3c' : 'var(--border)'}; border-radius:12px; margin-bottom:12px; overflow:hidden; transition:box-shadow 0.2s;"
                onmouseover="this.style.boxShadow='0 4px 20px rgba(135,54,255,0.2)'" onmouseout="this.style.boxShadow='none'">
                <div style="padding:15px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
                        <div style="font-weight:bold; color:var(--text-1); font-size:0.95rem; flex:1;">${isPinned}${entry.question} ${revisionBadge}</div>
                        ${entry.subcategory ? `<span style="font-size:0.75rem; background:rgba(255,255,255,0.1); padding:2px 8px; border-radius:10px; color:var(--text-2); white-space:nowrap;">${entry.subcategory}</span>` : ''}
                    </div>
                    <div style="color:var(--text-2); background:rgba(0,0,0,0.2); padding:10px 12px; border-radius:8px; margin-top:10px; font-size:0.9rem; line-height:1.6;">${entry.answer}</div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px; flex-wrap:wrap; gap:8px;">
                        <div style="display:flex; gap:15px; font-size:0.8rem; color:var(--text-2);">
                            <span>&#128065; ${entry.views || 0}</span>
                            <span style="color:#2ecc71;">&#128077; ${entry.helpful_votes || 0}</span>
                            ${notHelpfulBadge}
                        </div>
                        <div style="display:flex; gap:8px;">
                            <button onclick="window.togglePinFaq(${entry.id}, ${entry.is_pinned ? 0 : 1})"
                                style="padding:5px 10px; border-radius:6px; border:1px solid var(--border); background:transparent; color:${entry.is_pinned ? '#f1c40f' : 'var(--text-2)'}; cursor:pointer; font-size:0.85rem;">
                                &#128204;
                            </button>
                            <button onclick="window.openFaqModal(${entry.id})"
                                style="padding:5px 12px; border-radius:6px; border:1px solid #3498db; background:rgba(52,152,219,0.1); color:#3498db; cursor:pointer; font-size:0.85rem; font-family:Tajawal,sans-serif;">
                                &#9998; تعديل
                            </button>
                            <button onclick="window.deleteFaqEntry(${entry.id})"
                                style="padding:5px 12px; border-radius:6px; border:1px solid #e74c3c; background:rgba(231,76,60,0.1); color:#e74c3c; cursor:pointer; font-size:0.85rem; font-family:Tajawal,sans-serif;">
                                &#128465; حذف
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
        });
        html += `</div>`;
    });
    el.innerHTML = html;
}

function populateCategorySelect() {
    const sel = document.getElementById('faq-cat-select');
    if (!sel) return;
    const cats = [...new Set(faqCategories.map(c => c.category))];
    sel.innerHTML = '<option value="">-- اختر قسماً --</option>' + cats.map(c => `<option value="${c}">${c}</option>`).join('');
}

function setupFaqGlobals() {
    window.faqFilterCategory = (cat, btn) => {
        faqActiveCategory = cat || null;
        faqActiveSubcategory = null;
        document.querySelectorAll('.faq-cat-chip').forEach(b => {
            b.style.background = 'transparent';
            b.style.color = b.getAttribute('data-color') || '#8736ff';
        });
        btn.style.background = btn.style.borderColor || 'var(--accent)';
        btn.style.color = 'white';
        if (cat) { buildSubcategoryFilters(cat); renderFaqList(faqAllEntries.filter(e => e.category === cat)); }
        else { document.getElementById('faq-subcategory-filters').style.display = 'none'; renderFaqList(faqAllEntries); }
    };

    window.faqFilterSubcategory = (sub, btn) => {
        faqActiveSubcategory = sub || null;
        document.querySelectorAll('.faq-subcat-chip').forEach(b => b.style.background = 'transparent');
        btn.style.background = 'rgba(255,255,255,0.2)';
        renderFaqList(faqAllEntries.filter(e =>
            (!faqActiveCategory || e.category === faqActiveCategory) &&
            (!sub || e.subcategory === sub)
        ));
    };

    window.faqSearch = (q) => {
        if (!q.trim()) { renderFaqList(faqAllEntries); return; }
        const lower = q.toLowerCase();
        renderFaqList(faqAllEntries.filter(e => e.question.toLowerCase().includes(lower) || e.answer.toLowerCase().includes(lower)));
    };

    window.openFaqModal = (editId = null) => {
        faqEditId = editId;
        const modal = document.getElementById('faq-modal');
        if (!modal) return;
        modal.style.display = 'flex';
        const titleEl = document.getElementById('faq-modal-title');
        if (titleEl) titleEl.textContent = editId ? 'تعديل السؤال' : '+ إضافة سؤال جديد';
        if (editId) {
            const entry = faqAllEntries.find(e => e.id === editId);
            if (entry) {
                document.getElementById('faq-input-category').value = entry.category || '';
                document.getElementById('faq-input-subcategory').value = entry.subcategory || '';
                document.getElementById('faq-input-question').value = entry.question || '';
                document.getElementById('faq-input-answer').value = entry.answer || '';
            }
        } else {
            document.getElementById('faq-input-category').value = faqActiveCategory || '';
            document.getElementById('faq-input-subcategory').value = faqActiveSubcategory || '';
            document.getElementById('faq-input-question').value = '';
            document.getElementById('faq-input-answer').value = '';
        }
        populateCategorySelect();
    };

    window.closeFaqModal = () => {
        const modal = document.getElementById('faq-modal');
        if (modal) modal.style.display = 'none';
        faqEditId = null;
    };

    window.saveFaqEntry = async () => {
        const category = (document.getElementById('faq-input-category').value || '').trim();
        const subcategory = (document.getElementById('faq-input-subcategory').value || '').trim();
        const question = (document.getElementById('faq-input-question').value || '').trim();
        const answer = (document.getElementById('faq-input-answer').value || '').trim();
        if (!category || !question || !answer) { alert('القسم والسؤال والجواب مطلوبون!'); return; }
        try {
            const BASE = window.BOT_API_BASE || '';
            const url = faqEditId ? `${BASE}/api/faq/${faqEditId}/update` : `${BASE}/api/faq/add`;
            const res = await fetch(url, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({category, subcategory, question, answer}) });
            const data = await res.json();
            if (!data.success) throw new Error(data.error);
            window.closeFaqModal();
            await loadFaqData();
        } catch (e) { alert('خطأ: ' + e.message); }
    };

    window.deleteFaqEntry = async (id) => {
        const entry = faqAllEntries.find(e => e.id === id);
        const preview = entry ? entry.question.substring(0, 40) : '';
        if (!confirm('هل أنت متأكد من حذف هذا السؤال?\n"' + preview + '"')) return;
        try {
            const BASE = window.BOT_API_BASE || '';
            const res = await fetch(`${BASE}/api/faq/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (!data.success) throw new Error(data.error);
            await loadFaqData();
        } catch (e) { alert('خطأ في الحذف: ' + e.message); }
    };

    window.togglePinFaq = async (id, newPinState) => {
        try {
            const BASE = window.BOT_API_BASE || '';
            await fetch(`${BASE}/api/faq/${id}/update`, {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({is_pinned: newPinState})
            });
            await loadFaqData();
        } catch (e) { console.error(e); }
    };

    window.openFaqSuggestions = async () => {
        const modal = document.getElementById('faq-suggestions-modal');
        if (!modal) return;
        modal.style.display = 'flex';
        const listEl = document.getElementById('suggestions-list');
        if (listEl) listEl.innerHTML = '<div style="text-align:center; padding:30px; color:var(--text-2);">جاري التحميل...</div>';
        try {
            const BASE = window.BOT_API_BASE || '';
            const res = await fetch(`${BASE}/api/faq/suggestions`);
            const data = await res.json();
            if (!data.success) throw new Error(data.error);
            const suggestions = data.suggestions || [];
            if (!listEl) return;
            if (suggestions.length === 0) {
                listEl.innerHTML = `<div style="text-align:center; padding:40px; color:var(--text-2);"><div style="font-size:2.5rem; margin-bottom:10px;">&#10003;</div><div>لا توجد اقتراحات جديدة حالياً</div></div>`;
                return;
            }
            listEl.innerHTML = suggestions.map(s => `
                <div id="sug-${s.id}" style="background:rgba(52,152,219,0.1); border:1px solid rgba(52,152,219,0.3); border-radius:12px; padding:15px; margin-bottom:12px;">
                    <div style="font-size:0.8rem; color:#3498db; margin-bottom:8px;">&#128193; ${s.category || 'عام'} &bull; تكرر ${s.occurrence_count} مرة</div>
                    <div style="font-weight:bold; color:var(--text-1); margin-bottom:8px;">${s.suggested_question}</div>
                    <div style="color:var(--text-2); font-size:0.9rem; background:rgba(0,0,0,0.2); padding:10px; border-radius:8px; margin-bottom:10px;">${s.suggested_answer}</div>
                    <div style="display:flex; gap:8px; justify-content:flex-end;">
                        <button onclick="window.rejectFaqSuggestion(${s.id})" style="padding:6px 15px; border-radius:6px; border:1px solid #e74c3c; background:rgba(231,76,60,0.1); color:#e74c3c; cursor:pointer; font-family:Tajawal,sans-serif;">تجاهل</button>
                        <button onclick="window.approveFaqSuggestion(${s.id})" style="padding:6px 15px; border-radius:6px; border:none; background:#2ecc71; color:white; cursor:pointer; font-weight:bold; font-family:Tajawal,sans-serif;">قبول للـ FAQ</button>
                    </div>
                </div>`).join('');
        } catch (e) {
            if (listEl) listEl.innerHTML = `<div style="color:#e74c3c; padding:20px; text-align:center;">${e.message}</div>`;
        }
    };

    window.closeFaqSuggestions = () => {
        const modal = document.getElementById('faq-suggestions-modal');
        if (modal) modal.style.display = 'none';
    };

    window.approveFaqSuggestion = async (id) => {
        try {
            const BASE = window.BOT_API_BASE || '';
            const res = await fetch(`${BASE}/api/faq/suggestions/${id}/approve`, { method: 'POST' });
            const data = await res.json();
            if (!data.success) throw new Error(data.error);
            const card = document.getElementById(`sug-${id}`);
            if (card) { card.style.opacity = '0.5'; card.innerHTML = '<div style="text-align:center; color:#2ecc71; padding:10px;">تمت الإضافة إلى FAQ بنجاح!</div>'; }
            await loadFaqData();
        } catch (e) { alert('خطأ: ' + e.message); }
    };

    window.rejectFaqSuggestion = async (id) => {
        try {
            const BASE = window.BOT_API_BASE || '';
            await fetch(`${BASE}/api/faq/suggestions/${id}/reject`, { method: 'POST' });
            const card = document.getElementById(`sug-${id}`);
            if (card) card.remove();
        } catch (e) { alert('خطأ: ' + e.message); }
    };
}