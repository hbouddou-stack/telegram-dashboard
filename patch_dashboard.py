import re
import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Filter Bar and Replace Funnel Chart Canvas
filter_bar_html = """
        <!-- Dashboard Filters -->
        <div style="display:flex; gap:10px; margin-bottom: 20px; padding:15px; background:var(--surface); border-radius:12px; border:1px solid var(--border); align-items:center;">
            <span style="font-weight:700; color:var(--text2); font-size:0.9rem;">🔎 فلاتر (Filtres) :</span>
            <select id="dash-filter-year" onchange="updateDashboardView()" style="padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none;">
                <option value="all">Toutes les années (الكل)</option>
                <option value="1">1ère Année</option>
                <option value="2">2ème Année</option>
                <option value="3">3ème Année</option>
                <option value="4">4ème Année</option>
            </select>
            <select id="dash-filter-gender" onchange="updateDashboardView()" style="padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none;">
                <option value="all">Tous (الكل)</option>
                <option value="HOMME">Garçons (ذكور)</option>
                <option value="FEMME">Filles (إناث)</option>
            </select>
            <select id="dash-filter-pay" onchange="updateDashboardView()" style="padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none;">
                <option value="all">Tous (الكل)</option>
                <option value="PAID">Payé (مسدد)</option>
                <option value="UNPAID">Non Payé (غير مسدد)</option>
            </select>
        </div>
"""

# Insert filter bar before the Overview Sub-tabs
html = html.replace('<!-- Overview Sub-tabs -->', filter_bar_html + '\n        <!-- Overview Sub-tabs -->')

# Replace Funnel Canvas with HTML Funnel
funnel_old = """<canvas id="funnelChart" style="max-height: 250px;"></canvas>"""
funnel_new = """<div id="html-funnel-container" style="display:flex; flex-direction:column; gap:8px;"></div>"""
html = html.replace(funnel_old, funnel_new)

# 2. Inject new JS for Dashboard View
js_update_dashboard = """
// ===== DASHBOARD DYNAMIC UPDATE =====
function updateDashboardView() {
    if (!allStudents || allStudents.length === 0) return;

    const fYear = document.getElementById('dash-filter-year').value;
    const fGender = document.getElementById('dash-filter-gender').value;
    const fPay = document.getElementById('dash-filter-pay').value;

    // Filter Students
    const subset = allStudents.filter(s => {
        let match = true;
        if (fYear !== 'all' && String(s.year) !== fYear) match = false;
        
        let gen = (s.gender || '').toUpperCase().trim();
        if (gen === 'M') gen = 'HOMME';
        if (gen === 'F') gen = 'FEMME';
        if (fGender !== 'all' && gen !== fGender) match = false;
        
        let pay = (s.payment_status || '').toUpperCase().trim();
        let isPaid = ['PAID', 'PAYE', 'PAYÉ', 'مسدد'].includes(pay);
        if (fPay === 'PAID' && !isPaid) match = false;
        if (fPay === 'UNPAID' && isPaid) match = false;
        
        return match;
    });

    // Compute Metrics
    const total = subset.length;
    const contacted = subset.filter(s => s.email_sent > 0 || s.whatsapp_sent > 0 || s.sms_sent > 0).length;
    const started = subset.filter(s => s.bot_started_at).length;
    const linked = subset.filter(s => s.telegram_id).length;
    const joined = subset.filter(s => s.folder_clicked_at || s.group_joined).length;

    // Finances
    let paid = 0;
    let unpaid = 0;
    subset.forEach(s => {
        let pay = (s.payment_status || '').toUpperCase().trim();
        if (['PAID', 'PAYE', 'PAYÉ', 'مسدد'].includes(pay)) paid++;
        else unpaid++;
    });

    // Update KPI UI
    document.getElementById('home-kpi-total').textContent = total;
    document.getElementById('home-kpi-linked').textContent = linked + (total>0 ? ` (${Math.round(linked/total*100)}%)` : '');
    document.getElementById('home-kpi-groups').textContent = joined;
    
    // Ghost is global, let's keep it from backend or just mark N/A if filtered
    const ghostEl = document.getElementById('home-kpi-ghosts');
    if (fYear !== 'all' || fGender !== 'all' || fPay !== 'all') {
        ghostEl.textContent = 'N/A';
        ghostEl.style.fontSize = '1.5rem';
    } else {
        ghostEl.style.fontSize = '1.8rem';
        // Global ghost count remains what was loaded from home_stats
    }

    document.getElementById('finance-kpi-paid').textContent = paid + (total>0 ? ` (${Math.round(paid/total*100)}%)` : '');
    document.getElementById('finance-kpi-unpaid').textContent = unpaid;

    // Render Pipeline Funnel
    renderHtmlFunnel(total, contacted, started, linked, joined);

    // Render Charts
    renderFilteredCharts(subset, paid, unpaid);
}

function renderHtmlFunnel(total, contacted, started, linked, joined) {
    const container = document.getElementById('html-funnel-container');
    if(!container) return;

    function makeStep(label, count, prevCount, color, icon) {
        const pct = prevCount > 0 ? Math.round((count / prevCount) * 100) : 0;
        const totalPct = total > 0 ? Math.round((count / total) * 100) : 0;
        const drop = 100 - pct;
        
        let dropHtml = '';
        if (prevCount !== null && drop > 0 && count !== total) {
            dropHtml = `<div style="text-align:center; color:#ef4444; font-size:0.75rem; font-weight:bold; margin:-4px 0;">↓ -${drop}% (Perte)</div>`;
        }

        return `
            ${dropHtml}
            <div style="display:flex; justify-content:space-between; align-items:center; background:linear-gradient(90deg, ${color}22 0%, var(--surface) 100%); border:1px solid ${color}; border-radius:12px; padding:12px 20px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.5rem;">${icon}</span>
                    <span style="font-weight:700; color:var(--text1); font-size:1rem;">${label}</span>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.4rem; font-weight:900; color:${color};">${count}</div>
                    <div style="font-size:0.75rem; color:var(--text2);">${totalPct}% du total</div>
                </div>
            </div>
        `;
    }

    container.innerHTML = 
        makeStep("Importés (Base de données)", total, null, "#64748b", "📦") +
        makeStep("A cliqué / Démarré le Bot", started, total, "#0ea5e9", "🤖") +
        makeStep("Comptes Liés (Identifiés)", linked, started, "#10b981", "🔗") +
        makeStep("Ont rejoint les Groupes", joined, linked, "#8b5cf6", "🎓");
}

function renderFilteredCharts(subset, paid, unpaid) {
    if(!window.Chart) return;
    
    // Finance Pie
    const ctxFinance = document.getElementById('financeChart');
    if(ctxFinance) {
        if(financeChartInstance) financeChartInstance.destroy();
        financeChartInstance = new Chart(ctxFinance.getContext('2d'), {
            type: 'doughnut',
            data: { labels: ['Payés', 'Non Payés'], datasets: [{ data: [paid, unpaid], backgroundColor: ['#16a34a', '#ef4444'], borderWidth: 0 }] },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    // Demographics
    let m=0, f=0;
    let levels = {};
    subset.forEach(s => {
        let gen = (s.gender || '').toUpperCase().trim();
        if (gen === 'M' || gen === 'HOMME') m++;
        else if (gen === 'F' || gen === 'FEMME') f++;

        let lvl = s.school_level || 'Non Défini';
        levels[lvl] = (levels[lvl] || 0) + 1;
    });

    const ctxGender = document.getElementById('genderChart');
    if(ctxGender) {
        if(genderChartInstance) genderChartInstance.destroy();
        genderChartInstance = new Chart(ctxGender.getContext('2d'), {
            type: 'doughnut',
            data: { labels: ['Garçons', 'Filles'], datasets: [{ data: [m, f], backgroundColor: ['#3b82f6', '#ec4899'], borderWidth: 0 }] },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    const ctxLevel = document.getElementById('levelChart');
    if(ctxLevel) {
        if(levelChartInstance) levelChartInstance.destroy();
        const lvlLabels = Object.keys(levels).filter(k => k !== 'None' && k !== '');
        levelChartInstance = new Chart(ctxLevel.getContext('2d'), {
            type: 'pie',
            data: { labels: lvlLabels, datasets: [{ data: lvlLabels.map(k=>levels[k]), backgroundColor: ['#3b82f6','#8b5cf6','#ec4899','#f59e0b','#10b981','#64748b'] }] },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
}
"""

# Hook `updateDashboardView()` into `loadHomeDashboard()` (we call it at the end to initialize the UI)
html = html.replace(
    'renderHomeChartsV2(data.funnel, data.demographics, data.finances);',
    'if(typeof updateDashboardView === "function") updateDashboardView();'
)

# And inject the new JS functions just before loadHomeDashboard
html = html.replace('async function loadHomeDashboard()', js_update_dashboard + '\nasync function loadHomeDashboard()')

# Also, remove the old renderHomeChartsV2 since it's no longer used
html = re.sub(r'function renderHomeChartsV2\(.*?\) \{.*?\n\}', '', html, flags=re.DOTALL)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Dashboard Filters and Funnel Redesign Applied!")
