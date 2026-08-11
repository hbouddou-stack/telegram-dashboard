import re

def update_js():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Add Default Settings State and Initialization
    init_code = """
// --- SETTINGS STATE ---
let readerSettings = {
    scrollMode: 'zone', // 'zone' or 'teleprompter'
    focusMode: false
};

function loadSettings() {
    try {
        let saved = localStorage.getItem('academie_reader_settings');
        if (saved) {
            readerSettings = { ...readerSettings, ...JSON.parse(saved) };
        }
    } catch (e) { console.error(e); }
    
    // Apply UI
    const radios = document.getElementsByName('scrollMode');
    radios.forEach(r => {
        if (r.value === readerSettings.scrollMode) r.checked = true;
        r.addEventListener('change', (e) => {
            readerSettings.scrollMode = e.target.value;
            saveSettings();
        });
    });
    
    const focusToggle = document.getElementById('focusModeToggle');
    if (focusToggle) {
        focusToggle.checked = readerSettings.focusMode;
        focusToggle.addEventListener('change', (e) => {
            readerSettings.focusMode = e.target.checked;
            saveSettings();
            applyFocusMode();
        });
    }
    applyFocusMode();
}

function saveSettings() {
    localStorage.setItem('academie_reader_settings', JSON.stringify(readerSettings));
}

function applyFocusMode() {
    const content = document.getElementById('reader-content');
    if (content) {
        if (readerSettings.focusMode) {
            content.classList.add('focus-mode-active');
        } else {
            content.classList.remove('focus-mode-active');
        }
    }
}

// --- SETTINGS MODAL LOGIC ---
document.addEventListener('DOMContentLoaded', () => {
    const btnSettings = document.getElementById('btn-settings-toggle');
    const settingsSheet = document.getElementById('settings-sheet');
    const settingsOverlay = document.getElementById('settings-overlay');
    const closeSettingsBtn = document.getElementById('close-settings-btn');
    
    function openSettings() {
        settingsSheet.classList.add('active');
        settingsOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    function closeSettings() {
        settingsSheet.classList.remove('active');
        settingsOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    if (btnSettings) btnSettings.addEventListener('click', openSettings);
    if (closeSettingsBtn) closeSettingsBtn.addEventListener('click', closeSettings);
    if (settingsOverlay) settingsOverlay.addEventListener('click', closeSettings);
    
    loadSettings();
});
"""
    # Append initialization at the bottom
    js += init_code

    # 2. Modify Karaoke Engine Scroll Logic
    old_scroll = """            // If the element is too high (hidden under menus) OR too low (bottom of screen)
            if (rect.top < targetOffset || rect.top > window.innerHeight * 0.65) {"""
    
    new_scroll = """            let needsScroll = false;
            
            if (readerSettings.scrollMode === 'teleprompter') {
                // Teleprompter: Must always be EXACTLY at targetOffset (with small 5px tolerance)
                if (Math.abs(rect.top - targetOffset) > 5) {
                    needsScroll = true;
                }
            } else {
                // Zone: Only scroll if too high or too low
                if (rect.top < targetOffset || rect.top > window.innerHeight * 0.65) {
                    needsScroll = true;
                }
            }
            
            if (needsScroll) {"""

    js = js.replace(old_scroll, new_scroll)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
        
    print("Updated reader.js with settings logic")

if __name__ == '__main__':
    update_js()
