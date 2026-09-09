import io

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
    if(!window.Chart) return; // Prevent crash if chart.js failed to load
    
    // Funnel Chart
    const ctxFunnel = document.getElementById('funnelChart').getContext('2d');
    if(funnelChartInstance) funnelChartInstance.destroy();
    funnelChartInstance = new Chart(ctxFunnel, {
        type: 'bar',
        data: {
            labels: ['Importés', 'Contactés', 'Démarré Bot', 'Compte Lié', 'Dans groupe'],
            datasets: [{
                label: 'Étudiants',
                data: [funnel.imported, funnel.contacted, funnel.started_bot, funnel.linked, funnel.joined],
                backgroundColor: ['#94a3b8', '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'],
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });

    // Level Donut Chart
    const ctxLevel = document.getElementById('levelChart').getContext('2d');
    if(levelChartInstance) levelChartInstance.destroy();
    
    const lbls = [];
    const vals = [];
    for(let k in demographics.levels) {
        lbls.push((k === 'None' || k === 'null' || !k) ? 'Inconnu' : 'Niv ' + k);
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
    if(!container) return;
    container.innerHTML = '';
    
    if(alerts.uncontacted > 0) {
        container.innerHTML += `
            <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 15px; border-radius: 8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div>
                    <strong style="color: #d97706;">⚠️ ${alerts.uncontacted} élèves importés non contactés</strong>
                    <div style="font-size:0.85rem; color:var(--text2);">Ils n'ont reçu ni email ni WhatsApp.</div>
                </div>
                <button class="btn btn-primary" onclick="switchTab('actions')" style="padding: 6px 12px; font-size:0.85rem;">Actions</button>
            </div>
        `;
    }
    
    if(alerts.ghosts_today > 0) {
        container.innerHTML += `
            <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 15px; border-radius: 8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div>
                    <strong style="color: #b91c1c;">🚨 ${alerts.ghosts_today} nouveaux fantômes aujourd'hui</strong>
                    <div style="font-size:0.85rem; color:var(--text2);">Ils ont démarré le bot mais n'ont pas de compte.</div>
                </div>
                <button class="btn btn-primary" onclick="switchTab('ghosts')" style="padding: 6px 12px; font-size:0.85rem;">Fantômes</button>
            </div>
        `;
    }

    if(alerts.uncontacted === 0 && alerts.ghosts_today === 0) {
        container.innerHTML = `<div style="color: var(--text2); text-align:center; padding: 20px;">✅ Tout est au vert, aucune alerte.</div>`;
    }
}
"""

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

if "loadHomeDashboard()" not in c:
    # Let's see what happens on load. Currently there's a window.onload or DOMContentLoaded
    c = c.replace("loadOverviewStats();", "loadOverviewStats();\n            loadHomeDashboard();")
    # also replace the end of the script tag
    c = c.replace("</script>\n</body>", js_logic + "\n</script>\n</body>")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

