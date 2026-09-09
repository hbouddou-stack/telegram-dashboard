import io

# Compare local vs live
with io.open('live_html.html', 'r', encoding='utf-8') as f:
    live = f.read()
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    local = f.read()

print('Live size:', len(live))
print('Local size:', len(local))

# Check the key fix
needle = "switchModalTab('general');"
live_idx = live.find(needle)
local_idx = local.find(needle)

print('Live - after switchModalTab:')
print(repr(live[live_idx:live_idx+80]))
print()
print('Local - after switchModalTab:')
print(repr(local[local_idx:local_idx+80]))

# Check if the card onclick is correct
if 'openStudentCard' in live:
    idx2 = live.find('openStudentCard')
    print()
    print('Live - onclick context:')
    print(repr(live[idx2-50:idx2+80]))
else:
    print('openStudentCard NOT FOUND IN LIVE HTML!')
