import re

def fix_karaoke_scroll():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Update the offset calculation
    old_calc = """            // Calculate sticky headers total height
            const videoWrapper = document.getElementById('video-wrapper');
            const summaryMenu = document.getElementById('sommaire-wrapper');
            let offsetHeight = 0;
            
            if (videoWrapper) {
                const style = window.getComputedStyle(videoWrapper);
                if (style.position === 'sticky' || style.position === 'fixed') {
                    offsetHeight += videoWrapper.offsetHeight;
                }
            }
            if (summaryMenu) {
                const style = window.getComputedStyle(summaryMenu);
                if (style.position === 'sticky' || style.position === 'fixed') {
                    offsetHeight += summaryMenu.offsetHeight;
                }
            }
            
            // Add a padding of 30px so the text is not squeezed against the menu
            const targetOffset = offsetHeight + 30;
            
            let needsScroll = false;
            
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
            }"""

    new_calc = """            // Calculate sticky headers total height
            const stickyContainer = document.getElementById('sticky-header-container');
            let offsetHeight = 0;
            
            if (stickyContainer) {
                const style = window.getComputedStyle(stickyContainer);
                if (style.position === 'sticky' || style.position === 'fixed') {
                    offsetHeight += stickyContainer.offsetHeight;
                }
            }
            
            // Add a padding of 40px so the text is not squeezed against the menu
            const targetOffset = offsetHeight + 40;
            
            let needsScroll = false;
            
            if (readerSettings.scrollMode === 'teleprompter') {
                // Teleprompter: Must always be EXACTLY at targetOffset
                // Increase tolerance to 15px to avoid jitter with large fonts
                if (Math.abs(rect.top - targetOffset) > 15) {
                    needsScroll = true;
                }
            } else {
                // Zone: Only scroll if too high (hidden under header) or too low
                if (rect.top < targetOffset || rect.top > window.innerHeight * 0.70) {
                    needsScroll = true;
                }
            }"""

    if old_calc in js:
        js = js.replace(old_calc, new_calc)
    else:
        print("Warning: old_calc not found")

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    # 2. Update cache buster in reader.html
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=32', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=32', html)
    
    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Execution complete for scroll offset fix")

if __name__ == '__main__':
    fix_karaoke_scroll()
