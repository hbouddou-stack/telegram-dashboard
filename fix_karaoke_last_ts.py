import re

def fix_karaoke_last_ts():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    old_func = """function injectKaraokeSpans(htmlString) {
            let res = htmlString.replace(/\\[\\[TS:(\\d+(?:\\.\\d+)?)\\]\\]/g, (match, sec) => {
                lastTs = sec;
                return `</span><span class="karaoke-segment" data-start="${sec}">`;
            });
            if (res.startsWith('</span>')) {
                res = res.substring(7);
            } else {
                res = `<span class="karaoke-segment" data-start="${lastTs}">` + res;
            }"""

    new_func = """function injectKaraokeSpans(htmlString) {
            let initialTs = lastTs;
            let res = htmlString.replace(/\\[\\[TS:(\\d+(?:\\.\\d+)?)\\]\\]/g, (match, sec) => {
                lastTs = sec;
                return `</span><span class="karaoke-segment" data-start="${sec}">`;
            });
            if (res.startsWith('</span>')) {
                res = res.substring(7);
            } else {
                res = `<span class="karaoke-segment" data-start="${initialTs}">` + res;
            }"""

    if old_func in js:
        js = js.replace(old_func, new_func)
    else:
        print("Could not find injectKaraokeSpans function!")
        return

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
        
    print("Fixed lastTs bug in injectKaraokeSpans")

if __name__ == '__main__':
    fix_karaoke_last_ts()
