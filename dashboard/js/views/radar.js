// radar.js - Vue Radar Live for Admin

let radarInterval = null;

async function fetchRadarData() {
    try {
        const response = await fetch('/api/admin/presence/live');
        if (!response.ok) throw new Error('Failed to fetch radar data');
        const data = await response.json();
        renderRadar(data.active_users, data.total_active);
    } catch (err) {
        console.error('Radar fetch error:', err);
    }
}

function renderRadar(users, total) {
    const container = document.getElementById('panel-radar');
    if (!container) return;

    let html = `
        <div class="glass-panel" style="padding: 24px; animation: slideUp 0.4s ease-out;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                <h2 style="margin:0; font-size: 24px; color: var(--primary-color);">
                    📡 Vue Radar (Live)
                </h2>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #22c55e; box-shadow: 0 0 10px #22c55e; animation: pulse 2s infinite;"></div>
                    <span style="font-weight: 600; font-size: 18px; color: var(--text-color);">${total} en ligne</span>
                </div>
            </div>
            
            <div class="radar-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;">
    `;

    if (users.length === 0) {
        html += `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-color); opacity: 0.7; padding: 32px;">Aucun utilisateur en ligne pour le moment.</div>`;
    } else {
        users.forEach(user => {
            const pageName = user.page.replace('.html', '').replace('/', '');
            let pageIcon = '📄';
            if (pageName.includes('ask')) pageIcon = '🤖';
            else if (pageName.includes('guide')) pageIcon = '📚';
            
            // Format relative time (last seen)
            const secondsAgo = Math.floor((Date.now() - (user.last_seen * 1000)) / 1000);
            let timeStr = secondsAgo < 5 ? 'À l\'instant' : `Il y a ${secondsAgo}s`;

            html += `
                <div class="user-card" style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 12px; transition: transform 0.2s, box-shadow 0.2s;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; color: white;">
                                ${user.name ? user.name.charAt(0).toUpperCase() : '?'}
                            </div>
                            <div>
                                <h4 style="margin: 0; font-size: 16px; font-weight: 600; color: var(--text-color);">${user.name || 'Anonyme'}</h4>
                                <span style="font-size: 12px; color: var(--text-color); opacity: 0.6;">ID: ${user.user_id}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 16px;">${pageIcon}</span>
                            <span style="font-size: 14px; font-weight: 500; color: var(--text-color);">${user.page || 'Page inconnue'}</span>
                        </div>
                        <span style="font-size: 11px; font-weight: 600; color: #22c55e;">${timeStr}</span>
                    </div>
                </div>
            `;
        });
    }

    html += `
            </div>
        </div>
        <style>
            @keyframes pulse {
                0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
                70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }
                100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
            }
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .user-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                border-color: var(--primary-color) !important;
            }
        </style>
    `;

    container.innerHTML = html;
}

window.initRadarView = function() {
    console.log("Initializing Radar View");
    fetchRadarData();
    // Refresh every 5 seconds
    if (radarInterval) clearInterval(radarInterval);
    radarInterval = setInterval(fetchRadarData, 5000);
};

window.cleanupRadarView = function() {
    console.log("Cleaning up Radar View");
    if (radarInterval) {
        clearInterval(radarInterval);
        radarInterval = null;
    }
};
