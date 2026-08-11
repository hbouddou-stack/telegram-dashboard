import re

def aggressive_snapback():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Clean up the event listeners
    old_events = """let isTouching = false;
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

    new_events = """let isTouching = false;
window.addEventListener('scroll', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });
window.addEventListener('touchstart', () => { 
    if (!isProgrammaticScroll) {
        isTouching = true;
        lastUserScrollTime = Date.now(); 
    }
}, { passive: true, capture: true });
window.addEventListener('touchend', () => { 
    isTouching = false;
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });
window.addEventListener('wheel', () => { 
    if (!isProgrammaticScroll) lastUserScrollTime = Date.now(); 
}, { passive: true, capture: true });"""

    if old_events in js:
        js = js.replace(old_events, new_events)
    else:
        print("Warning: Could not find old events block")

    # Update the timeout value
    if "if (Date.now() - lastUserScrollTime > 1500)" in js:
        js = js.replace("if (Date.now() - lastUserScrollTime > 1500)", "if (Date.now() - lastUserScrollTime > 500 && !isTouching)")
    else:
        print("Warning: Could not find 1500ms timeout block")
        
    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
        
    print("Updated to aggressive 500ms snapback")

if __name__ == '__main__':
    aggressive_snapback()
