import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix switchTab
old_switch = """function switchTab(id) {
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
            // Hide all tab-content sections by removing active class and clearing inline display
            document.querySelectorAll('.tab-content').forEach(el => {
                el.style.display = ''; // Let CSS handle it
                el.classList.remove('active');
            });
            // Show the requested tab
            const tabEl = document.getElementById('tab-' + id);
            if (tabEl) {
                // Only for ghosts tab we might need flex, others use the CSS display:block from .active
                if (id === 'ghosts') {
                    tabEl.style.display = 'flex';
                }
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

c = c.replace(old_switch, new_switch)

# Also fix the inline style of tab-ghosts so it doesn't conflict
ghost_inline = 'id="tab-ghosts" class="tab-content" style="display:none; flex-direction:column; height:100%; overflow:hidden; background:var(--bg);"'
new_ghost_inline = 'id="tab-ghosts" class="tab-content" style="flex-direction:column; height:100%; overflow:hidden; background:var(--bg);"'
c = c.replace(ghost_inline, new_ghost_inline)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("Fixed layout bugs")
