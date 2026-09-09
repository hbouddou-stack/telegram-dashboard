import re
import io

# 1. Update Backend (main.py)
with io.open('main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

# Add Finances SQL to home_stats
if 'finances = {"paid": 0, "unpaid": 0}' not in main_code:
    sql_addition = """
            # Ghosts from today
            async with db.execute("SELECT COUNT(*) as cnt FROM users u LEFT JOIN academy_students s ON s.telegram_id = u.telegram_id WHERE s.telegram_id IS NULL AND u.created_at >= date('now')") as cur:
                ghosts_today = (await cur.fetchone())['cnt']

            # Finances
            async with db.execute("SELECT payment_status, COUNT(*) as cnt FROM academy_students WHERE excluded = 0 OR excluded IS NULL GROUP BY payment_status") as cur:
                payments_raw = await cur.fetchall()
            finances = {"paid": 0, "unpaid": 0}
            for r in payments_raw:
                ps = str(r['payment_status'] or '').upper().strip()
                if ps in ['PAID', 'PAYE', 'مسدد']:
                    finances["paid"] += r['cnt']
                else:
                    finances["unpaid"] += r['cnt']
"""
    main_code = re.sub(
        r'# Ghosts from today.*?ghosts_today = \(await cur.fetchone\(\)\)\[\'cnt\'\]',
        sql_addition.strip(),
        main_code,
        flags=re.DOTALL
    )
    
    main_code = main_code.replace(
        '"demographics": {',
        '"finances": finances,\n                "demographics": {'
    )
    
    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write(main_code)
    print("Backend updated.")

# 2. Update Frontend (admin_gateway.html)
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# New Overview HTML
NEW_OVERVIEW_HTML = """    <div id="tab-overview" class="tab-content">
    <div style="max-width: 1200px; margin: 0 auto; animation: fade-in 0.3s ease;">
        <h2 style="margin-bottom: 20px; font-weight: 800; color: var(--text1);">📊 لوحة القيادة (Tableau de bord)</h2>
        
        <!-- Overview Sub-tabs -->
        <div style="display:flex; gap:0; margin-bottom:20px; border-radius:12px; overflow:hidden; border:1px solid var(--border);">
            <div class="pill-btn pill-active" id="subtab-funnel-btn" onclick="switchOverviewSubtab('funnel')" style="flex:1; text-align:center; padding:10px; font-size:0.85rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">🚀 مسار التحويل</div>
            <div class="pill-btn" id="subtab-finances-btn" onclick="switchOverviewSubtab('finances')" style="flex:1; text-align:center; padding:10px; font-size:0.85rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">💰 المالية</div>
            <div class="pill-btn" id="subtab-demo-btn" onclick="switchOverviewSubtab('demo')" style="flex:1; text-align:center; padding:10px; font-size:0.85rem; font-weight:700; cursor:pointer;">🌍 الديموغرافيا</div>
        </div>

        <!-- SUBTAB 1: Funnel (Entonnoir & Conversion) -->
        <div id="subtab-funnel" class="overview-subtab active">
            <!-- KPIs Row -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 15px; text-align: center;">
                    <div style="font-size: 0.85rem; color: var(--text2); margin-bottom: 5px;">الطلاب (Total)</div>
                    <div id="home-kpi-total" style="font-size: 1.8rem; font-weight: 900; color: #3b82f6;">-</div>
                </div>
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 15px; text-align: center;">
                    <div style="font-size: 0.85rem; color: var(--text2); margin-bottom: 5px;">مرتبط (Liés)</div>
                    <div id="home-kpi-linked" style="font-size: 1.8rem; font-weight: 900; color: #10b981;">-</div>
                </div>
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 15px; text-align: center;">
                    <div style="font-size: 0.85rem; color: var(--text2); margin-bottom: 5px;">بالمجموعات</div>
                    <div id="home-kpi-groups" style="font-size: 1.8rem; font-weight: 900; color: #8b5cf6;">-</div>
                </div>
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 15px; text-align: center;">
                    <div style="font-size: 0.85rem; color: var(--text2); margin-bottom: 5px;">أشباح (Fantômes)</div>
                    <div id="home-kpi-ghosts" style="font-size: 1.8rem; font-weight: 900; color: #ef4444;">-</div>
                </div>
            </div>

            <!-- Funnel Chart -->
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                <h3 style="margin-bottom: 15px; font-size: 1.1rem;">مسار الرقمنة (Entonnoir)</h3>
                <canvas id="funnelChart" style="max-height: 250px;"></canvas>
            </div>
            
            <!-- Alerts Row -->
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-top: 20px;">
                <h3 style="margin-bottom: 15px; font-size: 1.1rem;">تنبيهات (Alertes)</h3>
                <div id="home-alerts-container" style="display: flex; flex-direction: column; gap: 10px;"></div>
            </div>
        </div>

        <!-- SUBTAB 2: Finances -->
        <div id="subtab-finances" class="overview-subtab" style="display:none;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; text-align: center;">
                    <div style="font-size: 0.95rem; color: var(--text2); margin-bottom: 10px;">مسدد (Payés)</div>
                    <div id="finance-kpi-paid" style="font-size: 2.2rem; font-weight: 900; color: #16a34a;">-</div>
                </div>
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; text-align: center;">
                    <div style="font-size: 0.95rem; color: var(--text2); margin-bottom: 10px;">غير مسدد (Non Payés)</div>
                    <div id="finance-kpi-unpaid" style="font-size: 2.2rem; font-weight: 900; color: #ef4444;">-</div>
                </div>
            </div>
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; text-align: center;">
                <h3 style="margin-bottom: 15px; font-size: 1.1rem;">توزيع المدفوعات</h3>
                <div style="max-width: 300px; margin: 0 auto;">
                    <canvas id="financeChart" style="max-height: 250px;"></canvas>
                </div>
            </div>
        </div>

        <!-- SUBTAB 3: Demographics -->
        <div id="subtab-demo" class="overview-subtab" style="display:none;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                    <h3 style="margin-bottom: 15px; font-size: 1.1rem; text-align:center;">المستويات (Niveaux)</h3>
                    <canvas id="levelChart" style="max-height: 250px;"></canvas>
                </div>
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px;">
                    <h3 style="margin-bottom: 15px; font-size: 1.1rem; text-align:center;">الجنس (Genre)</h3>
                    <canvas id="genderChart" style="max-height: 250px;"></canvas>
                </div>
            </div>
        </div>

    </div>
</div>"""

html = re.sub(
    r'<div id="tab-overview" class="tab-content">.*?</div>\n</div>',
    NEW_OVERVIEW_HTML,
    html,
    flags=re.DOTALL
)

# 3. Add JS for overview tabs and updated charts
JS_ADDITION = """
// ===== OVERVIEW DASHBOARD =====
function switchOverviewSubtab(tab) {
    document.querySelectorAll('.overview-subtab').forEach(el => el.style.display = 'none');
    document.querySelectorAll('[id^="subtab-"][id$="-btn"]').forEach(el => el.classList.remove('pill-active'));
    
    document.getElementById('subtab-' + tab).style.display = 'block';
    document.getElementById('subtab-' + tab + '-btn').classList.add('pill-active');
}

let funnelChartInstance = null;
let financeChartInstance = null;
let levelChartInstance = null;
let genderChartInstance = null;

async function loadHomeDashboard() {
    try {
        const res = await fetch('/api/admin/gateway/home_stats');
        const data = await res.json();
        if(data.success) {
            // Update KPIs
            document.getElementById('home-kpi-total').textContent = data.kpis.total;
            document.getElementById('home-kpi-linked').textContent = data.kpis.linked + ' (' + Math.round((data.kpis.linked/(data.kpis.total||1))*100) + '%)';
            document.getElementById('home-kpi-groups').textContent = data.kpis.groups;
            document.getElementById('home-kpi-ghosts').textContent = data.kpis.ghosts;

            // Finance KPIs
            if (data.finances) {
                const totalFin = data.finances.paid + data.finances.unpaid;
                const paidPct = totalFin > 0 ? Math.round((data.finances.paid / totalFin) * 100) : 0;
                document.getElementById('finance-kpi-paid').textContent = data.finances.paid + ' (' + paidPct + '%)';
                document.getElementById('finance-kpi-unpaid').textContent = data.finances.unpaid;
            }

            // Render Charts
            renderHomeChartsV2(data.funnel, data.demographics, data.finances);

            // Render Alerts
            renderHomeAlerts(data.alerts);
        }
    } catch(e) {
        console.error("Erreur Home Dashboard:", e);
    }
}

function renderHomeChartsV2(funnel, demographics, finances) {
    if(!window.Chart) return;
    
    // Funnel Chart
    const ctxFunnel = document.getElementById('funnelChart').getContext('2d');
    if(funnelChartInstance) funnelChartInstance.destroy();
    funnelChartInstance = new Chart(ctxFunnel, {
        type: 'bar',
        data: {
            labels: ['Importés', 'Contactés (SMS)', 'Ont démarré Bot', 'Comptes Liés', 'Rejoint Groupes'],
            datasets: [{
                label: 'Étudiants',
                data: [funnel.imported, funnel.contacted, funnel.started_bot, funnel.linked, funnel.joined],
                backgroundColor: ['#64748b', '#3b82f6', '#0ea5e9', '#10b981', '#8b5cf6'],
                borderRadius: 6
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
    });

    // Finance Pie Chart
    if (finances) {
        const ctxFinance = document.getElementById('financeChart').getContext('2d');
        if(financeChartInstance) financeChartInstance.destroy();
        financeChartInstance = new Chart(ctxFinance, {
            type: 'doughnut',
            data: {
                labels: ['Payés', 'Non Payés'],
                datasets: [{
                    data: [finances.paid, finances.unpaid],
                    backgroundColor: ['#16a34a', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    // Demographics: Level
    const ctxLevel = document.getElementById('levelChart').getContext('2d');
    if(levelChartInstance) levelChartInstance.destroy();
    const lvlLabels = Object.keys(demographics.levels || {}).filter(k => k !== 'None' && k !== '');
    const lvlData = lvlLabels.map(k => demographics.levels[k]);
    levelChartInstance = new Chart(ctxLevel, {
        type: 'pie',
        data: {
            labels: lvlLabels,
            datasets: [{ data: lvlData, backgroundColor: ['#3b82f6','#8b5cf6','#ec4899','#f59e0b','#10b981','#64748b'] }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    // Demographics: Gender
    const ctxGender = document.getElementById('genderChart').getContext('2d');
    if(genderChartInstance) genderChartInstance.destroy();
    let m = (demographics.genders['HOMME'] || 0) + (demographics.genders['homme'] || 0) + (demographics.genders['M'] || 0);
    let f = (demographics.genders['FEMME'] || 0) + (demographics.genders['femme'] || 0) + (demographics.genders['F'] || 0);
    genderChartInstance = new Chart(ctxGender, {
        type: 'doughnut',
        data: {
            labels: ['Garçons', 'Filles'],
            datasets: [{ data: [m, f], backgroundColor: ['#3b82f6', '#ec4899'], borderWidth: 0 }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}
"""

# Replace the old JS functions with the new V2 logic
html = re.sub(r'async function loadHomeDashboard\(\) \{.*?\n\}', '', html, flags=re.DOTALL)
html = re.sub(r'function renderHomeCharts\(.*?\) \{.*?\n\}', '', html, flags=re.DOTALL)

# Inject the new JS right before loadHomeDashboard was supposed to be (or before renderHomeAlerts)
html = html.replace('function renderHomeAlerts(alerts) {', JS_ADDITION + '\nfunction renderHomeAlerts(alerts) {')

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Frontend updated.")
