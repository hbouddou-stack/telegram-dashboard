

        // ===== DAILY STATS =====
        function loadDailyStats(days, el) {
            _activatePill('stats-', el);
            const chartArea = document.getElementById('daily-chart-area');
            const tbody = document.getElementById('daily-stats-body');
            if (!chartArea || !tbody) return;

            const now = new Date();
            const rows = [];
            for (let i = days - 1; i >= 0; i--) {
                const d = new Date(now);
                d.setDate(d.getDate() - i);
                const dateStr = d.toISOString().slice(0, 10);
                const dayStudents = allStudents.filter(s => (s.created_at || '').startsWith(dateStr));
                const paidCount = dayStudents.filter(s => {
                    const ps = String(s.payment_status||'').toUpperCase().trim();
                    return ps === 'PAID' || ps === 'PAYE' || ps === 'مسدد';
                }).length;
                rows.push({ date: dateStr, total: dayStudents.length, paid: paidCount, unpaid: dayStudents.length - paidCount });
            }

            const maxVal = Math.max(...rows.map(r => r.total), 1);
            chartArea.innerHTML = rows.map(r => {
                const h = Math.max(4, Math.round((r.total / maxVal) * 120));
                const dateLabel = r.date.slice(5);
                const paidPct = r.total > 0 ? Math.round((r.paid/r.total)*100) : 0;
                return `<div style="display:flex; flex-direction:column; align-items:center; gap:3px; min-width:36px; flex:1;">
                    <span style="font-size:0.65rem; font-weight:800; color:var(--accent2);">${r.total > 0 ? r.total : ''}</span>
                    <div style="width:100%; background:linear-gradient(180deg, var(--accent2), #60a5fa); border-radius:6px 6px 0 0; height:${h}px; position:relative; min-height:4px;" title="${r.date}: ${r.total} inscrits (${paidPct}% payés)">
                        <div style="position:absolute; bottom:0; width:100%; background:#16a34a; border-radius:0 0 6px 6px; height:${Math.round(h * r.paid / Math.max(r.total,1))}px;"></div>
                    </div>
                    <span style="font-size:0.6rem; color:var(--text2); white-space:nowrap;">${dateLabel}</span>
                </div>`;
            }).join('');

            tbody.innerHTML = rows.slice().reverse().map(r => `
                <tr style="border-top:1px solid var(--border);">
                    <td style="padding:9px 12px; font-weight:700;">${r.date}</td>
                    <td style="padding:9px 12px; font-weight:800; color:var(--accent2);">${r.total}</td>
                    <td style="padding:9px 12px; color:#16a34a; font-weight:700;">${r.paid}</td>
                    <td style="padding:9px 12px; color:#ef4444; font-weight:700;">${r.unpaid}</td>
                </tr>
            `).join('');
        }

