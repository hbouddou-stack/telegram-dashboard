import io

# Read old version (utf-16 from git)
with open('old_version.html', 'r', encoding='utf-16') as f:
    old = f.read()

# Extract filterStudents function
idx1 = old.find('function filterStudents()')
idx2 = old.find('\n        let currentCrmFilter', idx1)
filter_func = old[idx1:idx2]
print(f'Extracted filterStudents: {len(filter_func)} chars')

# Read current version
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    current = f.read()

# The patch accidentally removed filterStudents when it replaced the JS block
# We need to insert it back before the duplicate scanner functions
# Find the right insertion point: just before setDupView

insert_marker = 'let dupCurrentView'
if insert_marker in current:
    current = current.replace(insert_marker, filter_func + '\n\n        let dupCurrentView', 1)
    print('filterStudents restored!')
else:
    print('ERROR: insertion marker not found')

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(current)

print('Done')
