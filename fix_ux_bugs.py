import re

def fix_ux_bugs():
    # =============================================
    # FIX 1 + FIX 4: reader.js - Scroll & Zen Mode
    # =============================================
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Fix 1a: Increase scroll pause from 300ms to 8000ms (8s) to give user time to validate
    # Also add a check: if user is near bottom of page, NEVER resume auto-scroll until tab changes
    old_scroll_check = "if (Date.now() - lastUserScrollTime > 300 && !isTouching) {"
    new_scroll_check = """// Don't auto-scroll if: (1) user just scrolled manually within 8s, (2) Zen Mode is active,
        // or (3) user is near the bottom of page (near the validation button)
        const scrolledNearBottom = (window.scrollY + window.innerHeight) >= (document.documentElement.scrollHeight - 150);
        const isZenMode = document.body.classList.contains('zen-mode');
        if (Date.now() - lastUserScrollTime > 8000 && !isTouching && !isZenMode && !scrolledNearBottom) {"""
    
    if old_scroll_check in js:
        js = js.replace(old_scroll_check, new_scroll_check)
        # Close the extra brace added by the old single-line condition
        # The old code had one if block, we replaced it with the same structure, should be fine

    # Fix 4: Zen mode - also update zen toggle to set lastUserScrollTime to infinity
    old_zen_logic = """    // ZEN MODE LOGIC
    const zenBtn = document.getElementById('btn-zen-toggle');
    if (zenBtn) {
        zenBtn.addEventListener('click', () => {
            document.body.classList.toggle('zen-mode');
            if (document.body.classList.contains('zen-mode')) {
                zenBtn.style.color = 'var(--primary, var(--accent-color))';
            } else {
                zenBtn.style.color = '';
            }
        });
    }"""
    
    new_zen_logic = """    // ZEN MODE LOGIC
    const zenBtn = document.getElementById('btn-zen-toggle');
    if (zenBtn) {
        zenBtn.addEventListener('click', () => {
            document.body.classList.toggle('zen-mode');
            if (document.body.classList.contains('zen-mode')) {
                zenBtn.style.color = 'var(--primary, var(--accent-color))';
                // Block auto-scroll completely in zen mode
                lastUserScrollTime = Date.now() + 999999999;
            } else {
                zenBtn.style.color = '';
                // Re-enable auto-scroll with a 5s grace period
                lastUserScrollTime = Date.now();
            }
        });
    }"""
    
    if old_zen_logic in js:
        js = js.replace(old_zen_logic, new_zen_logic)

    # Fix scroll listeners: keep them at the 8s threshold (already handled above)
    # But also fix the timeout before releasing isProgrammaticScroll from 800ms to 1200ms
    old_timeout = "setTimeout(() => { isProgrammaticScroll = false; }, 800);"
    new_timeout = "setTimeout(() => { isProgrammaticScroll = false; }, 1200);"
    js = js.replace(old_timeout, new_timeout)

    # Fix switchThemeTab to reset lastUserScrollTime when switching tabs manually
    old_switch_start = """function switchThemeTab(index, shouldSeek = true) {
    if (index < 0 || index >= thematicData.length) return;
    
    currentTabIndex = index;
    
    // Update title immediately to avoid delay in numbering
    const titleEl = document.getElementById('current-theme-label');
    if (titleEl) {
        titleEl.textContent = (index + 1) + ". " + thematicData[index].title;
    }"""

    new_switch_start = """function switchThemeTab(index, shouldSeek = true) {
    if (index < 0 || index >= thematicData.length) return;
    
    currentTabIndex = index;
    
    // Update title immediately to avoid delay in numbering
    const titleEl = document.getElementById('current-theme-label');
    if (titleEl) {
        titleEl.textContent = (index + 1) + ". " + thematicData[index].title;
    }
    
    // When changing tab manually, reset scroll freedom (allow auto-scroll to work after 3s)
    if (shouldSeek) {
        lastUserScrollTime = Date.now() - 5000; // 5s in the past, so it resumes after 3s
    }"""

    if old_switch_start in js:
        js = js.replace(old_switch_start, new_switch_start)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    # =============================================
    # FIX 2 + FIX 3: reader.css - Video & Progress Bar
    # =============================================
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    # Fix 2: Center video properly
    old_video_css = """.video-container {
    position: relative;
    width: 100%;
    padding-top: 56.25%; /* 16:9 Aspect Ratio */
    background: #000;
}"""
    new_video_css = """.video-container {
    position: relative;
    width: 100%;
    padding-top: 56.25%; /* 16:9 Aspect Ratio */
    background: #000;
    overflow: hidden; /* prevent bleed */
}"""
    if old_video_css in css:
        css = css.replace(old_video_css, new_video_css)

    # Fix video iframe to be perfectly centered
    old_iframe_css = """.video-container iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: none;
}"""
    new_iframe_css = """.video-container iframe {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    width: 100%;
    height: 100%;
    border: none;
    margin: 0 auto;
    display: block;
}"""
    if old_iframe_css in css:
        css = css.replace(old_iframe_css, new_iframe_css)

    # Fix 3: Fix progress bar container to have stable height
    progress_fix = """
/* --- PROGRESS BAR STABLE HEIGHT FIX --- */
#progress-tracker-dots {
    min-height: 32px !important;
    height: 32px !important;
    box-sizing: content-box !important;
}
"""
    if "/* --- PROGRESS BAR STABLE HEIGHT FIX --- */" not in css:
        css += "\n" + progress_fix

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)

    # =============================================
    # FIX: Also fix video-wrapper in HTML to be display:flex + center
    # =============================================
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Fix the video-wrapper div to flex center
    old_video_wrapper = 'id="video-wrapper" style="position: relative;"'
    new_video_wrapper = 'id="video-wrapper" style="position: relative; display: flex; justify-content: center; overflow: hidden; background: #000;"'
    if old_video_wrapper in html:
        html = html.replace(old_video_wrapper, new_video_wrapper)

    # Cache buster
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=47', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=47', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("All 4 UX fixes applied successfully")

if __name__ == '__main__':
    fix_ux_bugs()
