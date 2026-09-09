import io
with io.open('dashboard/admin_gateway.html', 'rb') as f:
    c = f.read()
if b'id="profile-import-text"' in c:
    print('profile-import-text FOUND in local file')
else:
    print('profile-import-text STILL MISSING in local file')
if b'id="profile-level-badge"' in c:
    print('profile-level-badge FOUND in local file')
else:
    print('profile-level-badge STILL MISSING in local file')
