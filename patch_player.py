import re

def patch_js():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Update openLessonFromList and openSearchResult to set pendingSeekTime BEFORE openLesson
    old_list = re.search(r'function openLessonFromList\(subject, lessonNum, startSec = null\) \{[\s\S]*?switchThemeTab\(idx, false\);\n            \}\n        \}\n    \}\n\}', js)
    if old_list:
        new_list = """function openLessonFromList(subject, lessonNum, startSec = null) {
    const lesson = DB.find(l => l.subject === subject && l.lessonNum === lessonNum);
    if(lesson) {
        if (startSec !== null) pendingSeekTime = startSec;
        openLesson(lesson);
        switchTab('reader');
        if (startSec !== null) {
            const idx = thematicData.findIndex(t => t.startTime <= startSec && t.endTime > startSec);
            if(idx !== -1) {
                switchThemeTab(idx, false);
            }
        }
    }
}"""
        js = js.replace(old_list.group(0), new_list)

    old_search = re.search(r'function openSearchResult\(subject, lessonNum, startTime\) \{[\s\S]*?switchThemeTab\(idx, false\);\n        \}\n    \}\n\}', js)
    if old_search:
        new_search = """function openSearchResult(subject, lessonNum, startTime) {
    const lesson = DB.find(l => l.subject === subject && l.lessonNum === lessonNum);
    if(lesson) {
        if (startTime !== null) pendingSeekTime = startTime;
        openLesson(lesson);
        switchTab('reader');
        
        const idx = thematicData.findIndex(t => t.startTime <= startTime && t.endTime > startTime);
        if(idx !== -1) {
            switchThemeTab(idx, false);
        }
    }
}"""
        js = js.replace(old_search.group(0), new_search)

    # 2. Update initYouTubePlayer
    old_init = re.search(r'function initYouTubePlayer\(videoId\) \{[\s\S]*?\}\s*function renderLessonHeader', js)
    if old_init:
        new_init = """function initYouTubePlayer(videoId) {
    if (player && typeof player.loadVideoById === 'function') {
        let start = pendingSeekTime || 0;
        player.loadVideoById({'videoId': videoId, 'startSeconds': start});
        player.playVideo();
        pendingSeekTime = null;
    } else {
        player = new YT.Player('youtube-player', {
            height: '100%',
            width: '100%',
            videoId: videoId,
            playerVars: {
                'playsinline': 1,
                'rel': 0,
                'controls': 0,
                'modestbranding': 1,
                'showinfo': 0,
                'start': pendingSeekTime || 0
            },
            events: {
                'onReady': (e) => {
                    if (pendingSeekTime !== null) {
                        e.target.seekTo(pendingSeekTime, true);
                        e.target.playVideo();
                        pendingSeekTime = null;
                    } else {
                        e.target.playVideo();
                    }
                }
            }
        });
    }
}
function renderLessonHeader"""
        js = js.replace(old_init.group(0), new_init)

    # 3. Update renderLessonHeader to avoid destroying videoWrapper innerHTML
    old_render = re.search(r'videoWrapper\.innerHTML = \'<div id="youtube-player"><\/div>\';\s*if \(window\.YT && window\.YT\.Player\) \{', js)
    if old_render:
        new_render = """if (!document.getElementById('youtube-player')) {
            videoWrapper.innerHTML = '<div id="youtube-player"></div>';
        }
        if (window.YT && window.YT.Player) {"""
        js = js.replace(old_render.group(0), new_render)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

if __name__ == '__main__':
    patch_js()
