import re

def patch_karaoke_js():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Add Karaoke tracking variables and Interval
    
    karaoke_code = """
// --- KARAOKE ENGINE ---
let lastUserScrollTime = 0;

window.addEventListener('scroll', () => { lastUserScrollTime = Date.now(); }, { passive: true, capture: true });
window.addEventListener('touchstart', () => { lastUserScrollTime = Date.now(); }, { passive: true, capture: true });
window.addEventListener('wheel', () => { lastUserScrollTime = Date.now(); }, { passive: true, capture: true });

setInterval(() => {
    if (!player || !player.getPlayerState || player.getPlayerState() !== YT.PlayerState.PLAYING) return;
    
    let currentTime = player.getCurrentTime();
    
    const segments = document.querySelectorAll('.karaoke-segment');
    if (segments.length === 0) return;
    
    let activeSegment = null;
    let nextStart = 999999;
    
    for (let i = 0; i < segments.length; i++) {
        let start = parseFloat(segments[i].getAttribute('data-start'));
        if (start <= currentTime) {
            activeSegment = segments[i];
            if (i + 1 < segments.length) {
                nextStart = parseFloat(segments[i+1].getAttribute('data-start'));
            } else {
                nextStart = 999999;
            }
        } else {
            break;
        }
    }
    
    let changed = false;
    segments.forEach(seg => {
        if (seg === activeSegment && currentTime < nextStart) {
            if (!seg.classList.contains('active-karaoke')) {
                seg.classList.add('active-karaoke');
                changed = true;
                
                const rect = seg.getBoundingClientRect();
                const viewHeight = window.innerHeight;
                
                // Smart Auto-scroll
                if (rect.top < viewHeight * 0.2 || rect.bottom > viewHeight * 0.8) {
                    if (Date.now() - lastUserScrollTime > 3000) {
                        seg.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            }
        } else {
            seg.classList.remove('active-karaoke');
        }
    });
}, 300);
// --- END KARAOKE ENGINE ---
"""

    if "KARAOKE ENGINE" not in js:
        js = js + "\n" + karaoke_code
        
    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
        
    print("Patched Karaoke Engine into reader.js")

if __name__ == '__main__':
    patch_karaoke_js()
