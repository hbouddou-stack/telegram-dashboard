import io, re

with io.open('live_html.html', 'r', encoding='utf-8') as f:
    live = f.read()

# Find the fetchStudents function and how cards are built
idx = live.find('async function fetchStudents')
if idx == -1:
    idx = live.find('function fetchStudents')
    
if idx != -1:
    # Get the next 150 lines
    chunk = live[idx:idx+5000]
    with io.open('fetch_students_func.txt', 'w', encoding='utf-8') as f:
        f.write(chunk)
    print("Saved fetch_students_func.txt")
    print(chunk[:2000])
else:
    print("fetchStudents function NOT FOUND")
    # Try to find where students are loaded
    idx2 = live.find('fetchStudents()')
    print(f'fetchStudents() called at pos {idx2}:')
    print(repr(live[idx2-200:idx2+200]))
