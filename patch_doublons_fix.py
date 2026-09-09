import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_js = r"setTimeout\(\(\) => \{\s*const groups = \{\};"

new_js = """setTimeout(() => {
            try {
                const groups = {};"""

text = re.sub(old_js, new_js, text)

old_js2 = r"container\.innerHTML = html;\s*\}, 100\);"

new_js2 = """container.innerHTML = html;
            } catch(err) {
                alert("Erreur lors de l'analyse : " + err.message);
                console.error(err);
                container.innerHTML = 'Erreur...';
            }
            }, 100);"""

text = re.sub(old_js2, new_js2, text)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Added try/catch to duplicate scanner')
