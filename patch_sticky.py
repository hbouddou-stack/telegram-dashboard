import re

def patch_html():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Move video-container outside of reader-header
    old_section = re.search(r'<section class="reader-header">\s*<div class="video-container" id="video-wrapper">\s*<div id="youtube-player"></div>\s*</div>', html)
    if old_section:
        new_section = """<div class="video-container" id="video-wrapper" style="position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                    <div id="youtube-player"></div>
                </div>
                <section class="reader-header">"""
        html = html.replace(old_section.group(0), new_section)
    else:
        print("Could not find video-container in reader-header.")

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML patched.")

if __name__ == '__main__':
    patch_html()
