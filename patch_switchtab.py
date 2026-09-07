import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix the switchTab function completely
old_switch = """function switchTab(id) {
            document.querySelectorAll('.nav-item').forEach((b,i) => {
                b.classList.toggle('active', ['overview','students','sos','links','logs','settings'][i] === id);
            });
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            const tabEl = document.getElementById('tab-' + id);
            if (tabEl) tabEl.classList.add('active');
            if(id === 'students') filterStudents();
            if(id === 'sos') fetchSos();
            if(id === 'links') fetchLinks();
            if(id === 'logs') fetchGlobalLogs();
            if(id === 'settings') loadGeneralSettings();
        }"""

new_switch = """function switchTab(id) {
            // Update nav item active states
            document.querySelectorAll('.nav-item').forEach(b => {
                b.classList.remove('active');
            });
            // Mark the matching nav item active
            const navEl = document.getElementById('nav-' + id);
            if(navEl) {
                navEl.classList.add('active');
            } else {
                // Fallback: match by onclick text
                document.querySelectorAll('.nav-item').forEach(b => {
                    if(b.getAttribute('onclick') && b.getAttribute('onclick').includes("'" + id + "'")) {
                        b.classList.add('active');
                    }
                });
            }
            // Hide all tab-content sections
            document.querySelectorAll('.tab-content').forEach(el => {
                el.style.display = 'none';
                el.classList.remove('active');
            });
            // Show the requested tab
            const tabEl = document.getElementById('tab-' + id);
            if (tabEl) {
                tabEl.style.display = 'flex';
                tabEl.classList.add('active');
            }
            // Trigger data loading
            if(id === 'students') filterStudents();
            if(id === 'sos') fetchSos();
            if(id === 'links') fetchLinks();
            if(id === 'logs') fetchGlobalLogs();
            if(id === 'settings') loadGeneralSettings();
            if(id === 'ghosts') loadGhostVisitors();
        }"""

if old_switch in c:
    c = c.replace(old_switch, new_switch)
    print("switchTab replaced successfully")
else:
    print("COULD NOT FIND switchTab - trying fuzzy match")
    import re
    m = re.search(r'function switchTab\(id\) \{.*?\}', c, re.DOTALL)
    if m:
        print("Found via regex:", m.group(0)[:200].encode('utf-8'))
        c = c.replace(m.group(0), new_switch)
        print("Replaced via regex")

# Also make sure the ghost section uses display:flex when active and is hidden by default
# The ghost tab already has display:none in its style, but let's ensure the CSS class works too
# Add IDs to nav items if they don't have them
c = c.replace(
    'onclick="switchTab(\'overview\')"',
    'onclick="switchTab(\'overview\')" id="nav-overview"'
)
c = c.replace(
    'onclick="switchTab(\'students\')"',
    'onclick="switchTab(\'students\')" id="nav-students"'
)
c = c.replace(
    'onclick="switchTab(\'sos\')"',
    'onclick="switchTab(\'sos\')" id="nav-sos"'
)
c = c.replace(
    'onclick="switchTab(\'actions\')"',
    'onclick="switchTab(\'actions\')" id="nav-actions"'
)
c = c.replace(
    'onclick="switchTab(\'logs\')"',
    'onclick="switchTab(\'logs\')" id="nav-logs"'
)
c = c.replace(
    'onclick="switchTab(\'settings\')"',
    'onclick="switchTab(\'settings\')" id="nav-settings"'
)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("Done")
