import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with io.open('ui_search_results.txt', 'w', encoding='utf-8') as out:
    for i, line in enumerate(lines):
        if 'search-input' in line or 'displayStudents' in line or 'students-grid' in line or 'filters-row' in line or 'view-mode' in line:
            out.write(f"{i+1}: {line.strip()[:100]}\n")
