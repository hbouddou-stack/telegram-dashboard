import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

patch_old = "'LINK_INVALID': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '⛔', label: 'رابط غير صالح' },"
patch_new = patch_old + "\n            'INVALID_LINK_ATTEMPT': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '⛔', label: 'محاولة رابط غير صالح' },"

if patch_old in c:
    c = c.replace(patch_old, patch_new)
    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print("PATCH APPLIED")
else:
    print("COULD NOT FIND PATCH_OLD")
