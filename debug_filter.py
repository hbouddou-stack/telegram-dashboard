import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find exact content of filter section to replace
idx_start = html.find('<div id="tab-students" class="tab-content active">')
idx_end = html.find('<!-- COLOR FILTERS -->')
if idx_start == -1 or idx_end == -1:
    print(f"Start: {idx_start}, End: {idx_end}")
    # Try alternative
    idx_end = html.find('<!-- COLOR FILTERS')
    print(f"Alt End: {idx_end}")
else:
    print(f"Found section from {idx_start} to {idx_end}")
    old_section = html[idx_start:idx_end]
    print("---OLD SECTION---")
    print(old_section.encode('utf-8').decode('utf-8'))
