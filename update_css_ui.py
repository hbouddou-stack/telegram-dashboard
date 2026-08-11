import re

def update_css():
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    # 1. Update text-shadow to text-stroke for bold without width change
    old_active = """.active-karaoke {
    background-color: var(--highlight-bg);
    color: var(--highlight-text);
    border-radius: 4px;
    padding: 0 4px;
    box-shadow: 0 0 0 2px var(--highlight-bg);
    text-shadow: 0 0 0.5px currentColor; /* Gives a bold effect without layout shift */
    transition: background-color 0.3s ease, color 0.3s ease;
}"""

    new_active = """.active-karaoke {
    background-color: var(--highlight-bg);
    color: var(--highlight-text);
    border-radius: 4px;
    padding: 0 4px;
    box-shadow: 0 0 0 2px var(--highlight-bg);
    -webkit-text-stroke: 0.6px currentColor; /* Real bold effect without layout shift! */
    transition: background-color 0.3s ease, color 0.3s ease;
}"""

    if old_active in css:
        css = css.replace(old_active, new_active)
    else:
        print("Warning: Could not find .active-karaoke")

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)
        
    print("Updated reader.css with text-stroke")

if __name__ == '__main__':
    update_css()
