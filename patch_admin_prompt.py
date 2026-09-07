import io
with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_js = '''let adminName = localStorage.getItem('adminName');
            if(!adminName) {
                adminName = prompt("Quel est votre nom ? (Sera affiché sur la note)");
                if(!adminName) return;
                localStorage.setItem('adminName', adminName);
            }'''
new_js = '''let adminName = localStorage.getItem('adminName');
            if(!adminName) {
                adminName = prompt("Quel est votre nom ? (Sera affiché sur la note)");
                if(!adminName) adminName = "Admin";
                else localStorage.setItem('adminName', adminName);
            }'''
c = c.replace(old_js, new_js)
with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
