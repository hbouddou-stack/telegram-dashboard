import re

def add_auto_tab_switching():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Find the interval start
    interval_regex = re.search(r'let currentTime = player\.getCurrentTime\(\);[\s]*const segments = document\.querySelectorAll\(\'\.karaoke-segment\'\);', js)
    
    if not interval_regex:
        print("Could not find interval injection point")
        return

    injection = """let currentTime = player.getCurrentTime();
    
    // --- SMART AUTO TAB SWITCHING ---
    if (thematicData && thematicData[currentTabIndex]) {
        let tabStart = thematicData[currentTabIndex].startTime;
        let tabEnd = thematicData[currentTabIndex].endTime;
        
        if (currentTime >= tabEnd && currentTabIndex < thematicData.length - 1) {
            // Video moved past current tab, find correct tab
            let correctIndex = thematicData.findIndex(t => currentTime >= t.startTime && currentTime < t.endTime);
            if (correctIndex !== -1 && correctIndex !== currentTabIndex) {
                switchThemeTab(correctIndex, false);
                return; // Let next tick handle highlighting
            }
        } else if (currentTime < tabStart && currentTabIndex > 0) {
            // Video scrubbed backwards
            let correctIndex = thematicData.findIndex(t => currentTime >= t.startTime && currentTime < t.endTime);
            if (correctIndex !== -1 && correctIndex !== currentTabIndex) {
                switchThemeTab(correctIndex, false);
                return;
            }
        }
    }
    
    const segments = document.querySelectorAll('.karaoke-segment');"""

    js = js.replace(interval_regex.group(0), injection)
    
    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
        
    print("Added smart auto tab switching")

if __name__ == '__main__':
    add_auto_tab_switching()
