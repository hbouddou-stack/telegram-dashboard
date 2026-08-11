import re

def update_karaoke_timeout():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Update event listeners
    old_events = """window.addEventListener('scroll', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });
window.addEventListener('touchstart', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });
window.addEventListener('wheel', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });"""

    new_events = """let isTouching = false;
window.addEventListener('scroll', () => { 
    if (!isProgrammaticScroll && !isTouching) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });
window.addEventListener('touchstart', () => { 
    if (!isProgrammaticScroll) {
        isTouching = true;
        lastUserScrollTime = Date.now(); 
    }
}, { passive: true, capture: true });
window.addEventListener('touchend', () => { 
    isTouching = false;
    // Set time back so it triggers almost instantly (after 500ms instead of 1500ms)
    if (!isProgrammaticScroll) {
        lastUserScrollTime = Date.now() - 1000; 
    }
}, { passive: true, capture: true });
window.addEventListener('wheel', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });"""

    if old_events in js:
        js = js.replace(old_events, new_events)
    else:
        print("Could not find old event listeners")
        return

    # Update timeout in scroll logic
    old_timeout = "if (Date.now() - lastUserScrollTime > 3000)"
    new_timeout = "if (Date.now() - lastUserScrollTime > 1500)"

    if old_timeout in js:
        js = js.replace(old_timeout, new_timeout)
    else:
        print("Could not find timeout condition")
        return

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
    
    print("Successfully updated timeout and touchend logic")

if __name__ == '__main__':
    update_karaoke_timeout()
