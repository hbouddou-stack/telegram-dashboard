import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

js_injection = '''
        function switchModalTab(tabId) {
            ['general', 'academy', 'telegram', 'funnel'].forEach(t => {
                const mt = document.getElementById('mtab-' + t);
                const mc = document.getElementById('mcontent-' + t);
                if(mt) mt.classList.remove('active');
                if(mc) mc.classList.remove('active');
            });
            const amt = document.getElementById('mtab-' + tabId);
            const amc = document.getElementById('mcontent-' + tabId);
            if(amt) amt.classList.add('active');
            if(amc) amc.classList.add('active');
        }
        
        function setFunnelStep(stepId, dateVal) {
            const icon = document.getElementById('f-icon-' + stepId);
            const dateEl = document.getElementById('f-date-' + stepId);
            if(!icon) return;
            if (dateVal && dateVal !== '0' && dateVal !== 'false') {
                icon.className = 'funnel-icon success';
                icon.innerHTML = '✔';
                dateEl.textContent = String(dateVal).substring(0,16).replace('T', ' ');
            } else {
                icon.className = 'funnel-icon pending';
                icon.innerHTML = '✖';
                dateEl.textContent = 'لم يتم بعد';
            }
        }
'''

# We need to inject these functions in the global scope, let's say right before `async function openStudentCard`
if 'async function openStudentCard' in c:
    c = c.replace('async function openStudentCard', js_injection + '\n        async function openStudentCard')

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("Functions injected")
