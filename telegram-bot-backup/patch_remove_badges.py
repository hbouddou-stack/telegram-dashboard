import sys

with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    js = f.read()

search = '''                                    <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 15px;">

                                        <span class="badge" style="background: ${subColor}22; color: ${subColor}; font-weight: bold; border: 1px solid ${subColor}44; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">${subLabel}</span>
                                        <span class="badge" style="background: var(--surface-hover); color: var(--text-primary); font-weight: bold; border: 1px solid var(--border); padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">\\u0627\\u0644\\u062f\\u0631\\u0633 ${lesson.lessonNum}</span>

                                    </div>

                                    <h3 style="margin: 0 0 12px 0; font-size: 1.15rem; color: var(--text-primary); font-weight: 700;">${lesson.title || `\\u0627\\u0644\\u062f\\u0631\\u0633 ${lesson.lessonNum}`}</h3>'''

replace = '''                                    <h3 style="margin: 0 0 16px 0; font-size: 1.25rem; color: var(--text-primary); font-weight: 800;">${lesson.title || `\\u0627\\u0644\\u062f\\u0631\\u0633 ${lesson.lessonNum}`}</h3>'''

if search in js:
    js = js.replace(search, replace)
    with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print("Badges removed successfully!")
else:
    print("Could not find the search string to replace.")
