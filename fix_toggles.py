import re

def fix_toggles():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Clean up inline styles for switches
    bad_label_start = '<label class="switch" style="position: relative; display: inline-block; width: 44px; height: 24px;">'
    bad_input_focus = '<input type="checkbox" id="focusModeToggle" style="opacity: 0; width: 0; height: 0;">'
    bad_input_spacing = '<input type="checkbox" id="spacing-toggle" style="opacity: 0; width: 0; height: 0;">'
    bad_slider = '<span class="slider round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 24px;"></span>'

    html = html.replace(bad_label_start, '<label class="switch">')
    html = html.replace(bad_input_focus, '<input type="checkbox" id="focusModeToggle">')
    html = html.replace(bad_input_spacing, '<input type="checkbox" id="spacing-toggle">')
    html = html.replace(bad_slider, '<span class="slider"></span>')

    # Just in case there are subtle differences, let's use a regex to clean ANY inline styles on switch, input, slider
    # (Actually replace worked fine if exact match, but let's be sure)
    
    # Increment cache buster
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=35', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=35', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # Update reader.css to use RED/GREEN
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()
        
    # Replace slider background-color
    css = re.sub(r'\.slider\s*\{[^}]*background-color:\s*[^;]+;', lambda m: m.group(0).replace(m.group(0).split('background-color:')[1].split(';')[0].strip(), '#ef4444'), css)
    
    # Ensure input:checked + .slider has green color
    css = re.sub(r'input:checked\s*\+\s*\.slider\s*\{[^}]*background-color:\s*[^;]+;', lambda m: m.group(0).replace(m.group(0).split('background-color:')[1].split(';')[0].strip(), '#10b981 !important'), css)
    
    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)

    print("Toggles fixed")

if __name__ == '__main__':
    fix_toggles()
