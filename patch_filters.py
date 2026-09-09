import re
import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Payment Filters Layout
old_filters = r'<!-- PAIEMENT \+ SOURCE \+ NIVEAU:.*?<div style="display:flex; gap:8px; margin-bottom:4px;">.*?<!-- Paiement Pill -->.*?</div>\s*<!-- Source select compact -->'
new_filters = """<!-- PAIEMENT STATUS: Pill buttons (FULL WIDTH) -->
            <div style="display:flex; gap:0; margin-bottom:10px; border-radius:12px; overflow:hidden; border:1px solid var(--border);">
                <div class="pill-btn pill-active" id="pay-all" onclick="setPayFilter('all', this)" style="flex:1; text-align:center; padding:11px 6px; font-size:0.88rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">الكل (Tout)</div>
                <div class="pill-btn" id="pay-paid" onclick="setPayFilter('paid', this)" style="flex:1; text-align:center; padding:11px 6px; font-size:0.88rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">مسدد (Payé)</div>
                <div class="pill-btn" id="pay-unpaid" onclick="setPayFilter('unpaid', this)" style="flex:1; text-align:center; padding:11px 6px; font-size:0.88rem; font-weight:700; cursor:pointer;">غير مسدد (Non Payé)</div>
            </div>

            <!-- SOURCE + NIVEAU -->
            <div style="display:flex; gap:8px; margin-bottom:4px;">
                <!-- Source select compact -->"""
html = re.sub(old_filters, new_filters, html, flags=re.DOTALL)


# 2. Add numbering to students list and table
# First, for the table rows:
html = html.replace(
    '<td style="padding:12px;"><strong>${name}</strong></td>',
    '<td style="padding:12px;"><strong><span style="color:var(--text2); font-size:0.75rem; margin-right:4px;">#${i + 1}</span> ${name}</strong></td>'
)

# Then, for the grid/list cards:
html = html.replace(
    "const arName = String(s.first_name || '');",
    "const arName = '<span style=\"color:var(--text2); font-size:0.75rem; margin-left:6px;\">#' + (i + 1) + '</span> ' + String(s.first_name || '');"
)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Applied layout fixes and numberings!")
