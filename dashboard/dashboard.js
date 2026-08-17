let dashboardData = null;
let radarChartInstance = null;

async function loadDashboardData() {
    try {
        const userId = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) 
            ? window.Telegram.WebApp.initDataUnsafe.user.id 
            : 5413180491; // test user

        const res = await fetch('/api/student/dashboard-data', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ userId: userId })
        });
        
        const data = await res.json();
        if (data.success) {
            dashboardData = data;
            renderDashboardStats();
            renderDashboardRadar();
            window.dashUpdateMap();
        }
    } catch(e) {
        console.error("Dashboard error:", e);
    }
}

function renderDashboardStats() {
    if (!dashboardData) return;
    const stats = dashboardData.global_stats;
    document.getElementById('dash-streak').textContent = stats.streak;
    document.getElementById('dash-total-q').textContent = stats.total_answered;
    document.getElementById('dash-success-rate').textContent = stats.success_rate + "%";
}

function renderDashboardRadar() {
    if (!dashboardData || !dashboardData.radar) return;
    const radar = dashboardData.radar;
    
    // Default allowed themes (for radar axes)
    const axes = ["العقيدة", "الفقه", "السيرة", "الآداب", "النحو"];
    const subjectMap = {
        'aqeeda': 'العقيدة', 'aqida': 'العقيدة',
        'fiqh': 'الفقه',
        'sira': 'السيرة',
        'adab': 'الآداب',
        'nahw': 'النحو'
    };
    
    const dataValues = axes.map(a => 0); // default 0%
    
    radar.forEach(r => {
        let arabicName = subjectMap[r.subject.toLowerCase()] || r.subject;
        let idx = axes.indexOf(arabicName);
        if (idx !== -1) {
            dataValues[idx] = r.rate;
        }
    });

    const ctx = document.getElementById('skillRadarChart').getContext('2d');
    
    if (radarChartInstance) {
        radarChartInstance.destroy();
    }
    
    radarChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: axes,
            datasets: [{
                label: 'نسبة النجاح %',
                data: dataValues,
                backgroundColor: 'rgba(59, 130, 246, 0.2)', // var(--primary) with opacity
                borderColor: '#3b82f6',
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#3b82f6',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(0, 0, 0, 0.05)' },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    pointLabels: {
                        font: { size: 14, family: 'Cairo, system-ui' },
                        color: '#64748b'
                    },
                    ticks: {
                        display: false,
                        min: 0,
                        max: 100,
                        stepSize: 20
                    }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

window.dashUpdateMap = function() {
    if (!dashboardData || !dashboardData.map_data) return;
    const subj = document.getElementById('dash-map-subject').value;
    const lessons = dashboardData.map_data[subj];
    const container = document.getElementById('dash-serpentine-map');
    
    if (!lessons || lessons.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:20px; color:var(--text-3);">لا توجد دروس حالياً</div>';
        return;
    }
    
    let html = '';
    let isCurrentFound = false;
    
    for (let i = 0; i < lessons.length; i++) {
        const lesson = lessons[i];
        let stateClass = 'locked';
        let emoji = '🔒';
        
        // If 80% correct, it's completed
        if (lesson.total > 0 && lesson.correct >= lesson.total * 0.8) {
            stateClass = 'completed';
            emoji = '⭐';
        } else if (lesson.total > 0 || !isCurrentFound) {
            // First one not completed is the current one
            stateClass = 'current';
            emoji = '📍';
            isCurrentFound = true;
        }
        
        let action = `onclick="window.startPracticeForLesson('${subj}', ${lesson.course_number})"`;
        if (stateClass === 'locked') {
            action = 'onclick="alert('هذا الدرس مغلق، عليك إتمام ما قبله')"';
        }
        
        html += `
            <div class="map-node ${stateClass}" ${action}>
                ${emoji}
                <div class="map-node-label">الدرس ${lesson.course_number}</div>
            </div>
        `;
    }
    
    container.innerHTML = html;
};

window.startPracticeForLesson = function(subject, courseNumber) {
    if(typeof quizEngine !== 'undefined') {
        quizEngine.fetchQuestionsCustom({ subject: subject, lessonNum: courseNumber, source: 'all' });
        switchTab('practice', document.querySelector('.bottom-nav .nav-btn')); 
    }
};

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});
