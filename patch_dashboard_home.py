import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add Chart.js to head if not exists
if "chart.js" not in c:
    c = c.replace("</head>", '    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n</head>')

new_overview = """<div id="tab-overview" class="tab-content">
    <div style="max-width: 1200px; margin: 0 auto; animation: fade-in 0.3s ease;">
        <h2 style="margin-bottom: 20px; font-weight: 800; color: var(--text1);">الرئيسية (Vue d'ensemble)</h2>
        
        <!-- KPIs Row -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px;">
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 1rem; color: var(--text2); margin-bottom: 10px;">👥 إجمالي الطلاب (Total)</div>
                <div id="home-kpi-total" style="font-size: 2.5rem; font-weight: 900; color: #3b82f6;">-</div>
            </div>
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 1rem; color: var(--text2); margin-bottom: 10px;">✅ مرتبط بتيليجرام (Liés)</div>
                <div id="home-kpi-linked" style="font-size: 2.5rem; font-weight: 900; color: #10b981;">-</div>
            </div>
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 1rem; color: var(--text2); margin-bottom: 10px;">📱 في المجموعات (Groupes)</div>
                <div id="home-kpi-groups" style="font-size: 2.5rem; font-weight: 900; color: #8b5cf6;">-</div>
            </div>
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 1rem; color: var(--text2); margin-bottom: 10px;">👻 زوار أشباح (Fantômes)</div>
                <div id="home-kpi-ghosts" style="font-size: 2.5rem; font-weight: 900; color: #ef4444;">-</div>
            </div>
        </div>

        <!-- Charts Row -->
        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px;">
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-bottom: 15px; font-size: 1.1rem;">مسار الطالب (Funnel de Digitalisation)</h3>
                <canvas id="funnelChart" style="max-height: 250px;"></canvas>
            </div>
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-bottom: 15px; font-size: 1.1rem;">حسب المستوى (Par Niveau)</h3>
                <canvas id="levelChart" style="max-height: 250px;"></canvas>
            </div>
        </div>

        <!-- Alerts Row -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-bottom: 15px; font-size: 1.1rem;">🚨 التنبيهات (Centre d'Alertes)</h3>
            <div id="home-alerts-container" style="display: flex; flex-direction: column; gap: 10px;">
                <!-- Injected via JS -->
            </div>
        </div>
    </div>
</div>
"""

# Replace old tab-overview with new one
m = re.search(r'<div id="tab-overview" class="tab-content">(.*?)<div id="tab-actions"', c, re.DOTALL)
if m:
    c = c[:m.start()] + new_overview + '<div id="tab-actions"' + c[m.end():]
    
# Inject the JS logic for home dashboard
js_logic = """
let funnelChartInstance = null;
let levelChartInstance = null;

async function loadHomeDashboard() {
    try {
        const res = await fetch('/api/admin/gateway/home_stats');
        const data = await res.json();
        if(data.success) {
            // Update KPIs
            document.getElementById('home-kpi-total').textContent = data.kpis.total;
            document.getElementById('home-kpi-linked').textContent = data.kpis.linked + ' (' + Math.round((data.kpis.linked/data.kpis.total)*100) + '%)';
            document.getElementById('home-kpi-groups').textContent = data.kpis.groups;
            document.getElementById('home-kpi-ghosts').textContent = data.kpis.ghosts;

            // Render Charts
            renderHomeCharts(data.funnel, data.demographics);

            // Render Alerts
            renderHomeAlerts(data.alerts);
        }
    } catch(e) {
        console.error("Erreur Home Dashboard:", e);
    }
}

function renderHomeCharts(funnel, demographics) {
    // Funnel Chart
    const ctxFunnel = document.getElementById('funnelChart').getContext('2d');
    if(funnelChartInstance) funnelChartInstance.destroy();
    funnelChartInstance = new Chart(ctxFunnel, {
        type: 'bar',
        data: {
            labels: ['Importés', 'Contactés (Email/WA)', 'Ont cliqué /start', 'Compte Lié', 'Dans le groupe'],
            datasets: [{
                label: 'Nombre d\\'étudiants',
                data: [funnel.imported, funnel.contacted, funnel.started_bot, funnel.linked, funnel.joined],
                backgroundColor: ['#94a3b8', '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'],
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y', // horizontal bar
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });

    // Level Donut Chart
    const ctxLevel = document.getElementById('levelChart').getContext('2d');
    if(levelChartInstance) levelChartInstance.destroy();
    
    // Process levels (handle null or None)
    const lbls = [];
    const vals = [];
    for(let k in demographics.levels) {
        lbls.push(k === 'None' || k === 'null' ? 'Inconnu' : 'Niveau ' + k);
        vals.push(demographics.levels[k]);
    }

    levelChartInstance = new Chart(ctxLevel, {
        type: 'doughnut',
        data: {
            labels: lbls,
            datasets: [{
                data: vals,
                backgroundColor: ['#ef4444', '#f97316', '#f59e0b', '#84cc16', '#06b6d4', '#6366f1']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: { legend: { position: 'right' } }
        }
    });
}

function renderHomeAlerts(alerts) {
    const container = document.getElementById('home-alerts-container');
    container.innerHTML = '';
    
    if(alerts.uncontacted > 0) {
        container.innerHTML += `
            <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 15px; border-radius: 8px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong style="color: #d97706;">⚠️ ${alerts.uncontacted} élèves importés non contactés</strong>
                    <div style="font-size:0.85rem; color:var(--text2);">Ils n'ont reçu ni email ni WhatsApp.</div>
                </div>
                <button class="btn btn-primary" onclick="switchTab('actions')" style="padding: 6px 12px; font-size:0.85rem;">Aller aux Actions</button>
            </div>
        `;
    }
    
    if(alerts.ghosts_today > 0) {
        container.innerHTML += `
            <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 15px; border-radius: 8px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong style="color: #b91c1c;">🚨 ${alerts.ghosts_today} nouveaux visiteurs fantômes aujourd'hui</strong>
                    <div style="font-size:0.85rem; color:var(--text2);">Ils ont démarré le bot mais n'ont pas de compte.</div>
                </div>
                <button class="btn btn-primary" onclick="switchTab('ghosts')" style="padding: 6px 12px; font-size:0.85rem;">Voir les fantômes</button>
            </div>
        `;
    }

    if(alerts.uncontacted === 0 && alerts.ghosts_today === 0) {
        container.innerHTML = `<div style="color: var(--text2); text-align:center; padding: 20px;">✅ Tout est au vert, aucune alerte.</div>`;
    }
}
"""

if "function loadHomeDashboard()" not in c:
    c = c.replace("async function loadInitialData() {", js_logic + "\nasync function loadInitialData() {\n    loadHomeDashboard();")
    
with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Frontend dashboard home UI injected.")
