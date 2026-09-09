import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'search-input' in line or 'displayStudents' in line or 'students-grid' in line or 'filters-row' in line:
            print(f"{i+1}: {line.strip()[:100]}")
