import re

def fix_karaoke_engine():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # We need to replace the entire KARAOKE ENGINE block
    karaoke_regex = re.search(r'// --- KARAOKE ENGINE ---[\s\S]*?// --- END KARAOKE ENGINE ---', js)
    if not karaoke_regex:
        print("Karaoke engine not found!")
        return

    new_engine = """// --- KARAOKE ENGINE ---
let lastUserScrollTime = 0;
let isProgrammaticScroll = false;

window.addEventListener('scroll', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });
window.addEventListener('touchstart', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });
window.addEventListener('wheel', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });

setInterval(() => {
    if (!player || !player.getPlayerState || player.getPlayerState() !== YT.PlayerState.PLAYING) return;
    
    let currentTime = player.getCurrentTime();
    
    const segments = document.querySelectorAll('.karaoke-segment');
    if (segments.length === 0) return;
    
    let activeStart = -1;
    let nextStart = 999999;
    
    for (let i = 0; i < segments.length; i++) {
        let start = parseFloat(segments[i].getAttribute('data-start'));
        if (isNaN(start)) continue;
        
        if (start <= currentTime) {
            activeStart = start;
        } else {
            nextStart = start;
            break;
        }
    }
    
    let firstActiveSeg = null;
    
    segments.forEach(seg => {
        let start = parseFloat(seg.getAttribute('data-start'));
        if (start === activeStart && currentTime < nextStart) {
            if (!seg.classList.contains('active-karaoke')) {
                seg.classList.add('active-karaoke');
            }
            if (!firstActiveSeg) firstActiveSeg = seg;
        } else {
            seg.classList.remove('active-karaoke');
        }
    });
    
    if (firstActiveSeg) {
        const rect = firstActiveSeg.getBoundingClientRect();
        const viewHeight = window.innerHeight;
        
        // Smart Auto-scroll based on the FIRST element of the active group
        if (rect.top < viewHeight * 0.2 || rect.bottom > viewHeight * 0.8) {
            if (Date.now() - lastUserScrollTime > 3000) {
                isProgrammaticScroll = true;
                firstActiveSeg.scrollIntoView({ behavior: 'smooth', block: 'center' });
                // Reset programmatic flag after smooth scroll is expected to finish
                setTimeout(() => { isProgrammaticScroll = false; }, 800);
            }
        }
    }
}, 300);
// --- END KARAOKE ENGINE ---"""

    js = js.replace(karaoke_regex.group(0), new_engine)
    
    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
    
    print("Fixed Karaoke Engine scroll and grouping.")

if __name__ == '__main__':
    fix_karaoke_engine()
