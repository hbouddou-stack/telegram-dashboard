import io, re
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# I will find the exact string to remove
bad_code = """// Re-added missing modal logic
    document.getElementById('logs-overlay').style.display = 'flex';
    if(typeof fetchCrmTimeline === 'function') fetchCrmTimeline(student.student_id, student.telegram_id);
    
    try {
        const res = await fetch('/api/admin/gateway/logs?id=' + student.student_id + '&tid=' + (student.telegram_id || 'null'));
        const data = await res.json();

        if (student.telegram_id) {
            let tgFullName = student.tg_first_name || '';
            if (student.tg_last_name) tgFullName += ' ' + student.tg_last_name;
            document.getElementById('profile-tg-display').textContent = tgFullName.trim() || 'Non défini (Nom caché)';

            document.getElementById('modal-tg-identity').innerHTML = `
                <strong>ID:</strong> ${student.telegram_id}<br>
                <strong>Prénom:</strong> ${student.tg_first_name || '-'}<br>
                <strong>Nom:</strong> ${student.tg_last_name || '-'}${student.telegram_username ? '<br><strong>Pseudo:</strong> @' + student.telegram_username : ''}
            `;
        } else {
            document.getElementById('modal-tg-identity').innerHTML = `<span style="color:var(--text2);">Non lié</span>`;
        }

        document.getElementById('modal-db-identity').innerHTML = `
            <strong>ID:</strong> ${student.student_id || '-'}<br>
            <strong>Nom complet:</strong> ${(student.first_name||'') + ' ' + (student.last_name||'')}<br>
            <strong>Email:</strong> ${student.email || '-'}<br>
            <strong>Genre:</strong> ${student.gender || '-'}
        `;

        if(data.success && data.logs.length > 0) {
            let grouped = groupLogs(data.logs);
            let html = grouped.map(l => renderLogCard(l, false)).join('');
            document.getElementById('logs-body').innerHTML = html;
        } else {
            document.getElementById('logs-body').innerHTML = '<div class="no-items">Aucun historique pour le moment.</div>';
        }
    } catch(e) {
        document.getElementById('logs-body').innerHTML = '<div class="no-items" style="color:var(--danger);">Erreur lors du chargement de l\\'historique.</div>';
    }
}"""

if bad_code in c:
    c = c.replace(bad_code, "")
    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print("REMOVED SUCCESSFULLY")
else:
    print("BAD CODE NOT FOUND VERBATIM. DOING REGEX.")
    # More robust removal
    c = re.sub(r'// Re-added missing modal logic.*?Erreur lors du chargement de l\'historique\.</div>\s*\}\s*\}', '', c, flags=re.DOTALL)
    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print("REMOVED VIA REGEX")
