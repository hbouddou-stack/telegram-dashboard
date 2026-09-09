import io, re

with io.open('live_html.html', 'r', encoding='utf-8') as f:
    live = f.read()

# Check: how does the card div get its click handler?
# Search for renderStudentsList or the div creation that calls openStudentCard
patterns = [
    'div.onclick',
    'openStudentCard(s)',
    'onclick="openStudentCard',
    'addEventListener.*openStudentCard',
    'fetchStudents',
    'renderStudentsList',
    'student-card',
    'student-list',
]

for p in patterns:
    idx = live.find(p)
    if idx != -1:
        print(f'FOUND "{p}" at pos {idx}:')
        print(repr(live[idx-30:idx+120]))
        print()
    else:
        print(f'NOT FOUND: "{p}"')
