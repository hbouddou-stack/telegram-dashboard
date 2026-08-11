import re

def fix_colors_and_sync_speed():
    # --- UPDATE reader.css ---
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    # Add !important to .btn.active styles to ensure they override anything
    old_active = """.settings-btn-group .btn.active {
    background: var(--primary);
    color: #ffffff;
    border-color: var(--primary);
}"""
    new_active = """.settings-btn-group .btn.active {
    background: var(--primary) !important;
    color: #ffffff !important;
    border-color: var(--primary) !important;
}"""
    css = css.replace(old_active, new_active)

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)

    # --- UPDATE reader.html ---
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Add btn-speed-toggle back to sticky header
    sticky_btn = '<button class="control-btn" id="btn-sticky-toggle" title="Désépingler la vidéo" style="background:var(--surface); color:var(--text); border:1px solid var(--border-color); border-radius:8px; padding:6px 10px; font-size:14px; margin-right: 4px;">📌</button>'
    if 'id="btn-speed-toggle"' not in html:
        speed_btn = '<button class="control-btn" id="btn-speed-toggle" title="Vitesse de lecture" style="background:var(--surface); color:var(--text); border:1px solid var(--border-color); border-radius:8px; padding:6px 10px; font-size:14px; margin-right: 4px; font-weight: bold; width: 45px;">1x</button>\n                            '
        html = html.replace(sticky_btn, speed_btn + sticky_btn)

    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=38', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=38', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # --- UPDATE reader.js ---
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Rewrite Speed logic
    old_speed_logic = """let currentPlaybackRate = 1;
document.addEventListener('DOMContentLoaded', () => {
    const speedBtns = document.querySelectorAll('.speed-select-btn');
    speedBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            currentPlaybackRate = parseFloat(e.target.getAttribute('data-speed'));
            
            // Update active state
            speedBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            if (player && typeof player.setPlaybackRate === 'function') {
                player.setPlaybackRate(currentPlaybackRate);
            }
        });
    });
});"""

    new_speed_logic = """let currentPlaybackRate = 1;
function updateSpeedUI() {
    const quickSpeedBtn = document.getElementById('btn-speed-toggle');
    if (quickSpeedBtn) {
        quickSpeedBtn.textContent = currentPlaybackRate + 'x';
    }
    document.querySelectorAll('.speed-select-btn').forEach(b => {
        if (parseFloat(b.getAttribute('data-speed')) === currentPlaybackRate) {
            b.classList.add('active');
        } else {
            b.classList.remove('active');
        }
    });
}

function setPlaybackSpeed(rate) {
    currentPlaybackRate = rate;
    updateSpeedUI();
    if (player && typeof player.setPlaybackRate === 'function') {
        player.setPlaybackRate(currentPlaybackRate);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const speedBtns = document.querySelectorAll('.speed-select-btn');
    speedBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            setPlaybackSpeed(parseFloat(e.target.getAttribute('data-speed')));
        });
    });
    
    const quickSpeedBtn = document.getElementById('btn-speed-toggle');
    if (quickSpeedBtn) {
        quickSpeedBtn.addEventListener('click', () => {
            let newRate = 1;
            if (currentPlaybackRate === 1) newRate = 1.25;
            else if (currentPlaybackRate === 1.25) newRate = 1.5;
            else if (currentPlaybackRate === 1.5) newRate = 2;
            else if (currentPlaybackRate === 2) newRate = 0.75;
            else newRate = 1;
            setPlaybackSpeed(newRate);
        });
    }
    
    updateSpeedUI();
});"""

    if old_speed_logic in js:
        js = js.replace(old_speed_logic, new_speed_logic)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    print("Colors fixed and speed sync completed")

if __name__ == '__main__':
    fix_colors_and_sync_speed()
