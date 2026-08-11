import re

def fix_karaoke_bold():
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    # Replace font-weight: bold with text-shadow in karaoke active segment
    # It might look like:
    # .karaoke-segment.active-karaoke {
    #     background-color: rgba(79, 70, 229, 0.15); /* var(--primary) with 15% opacity */
    #     color: var(--primary);
    #     font-weight: bold;
    # }
    
    css = re.sub(r'font-weight:\s*bold;', '/* font-weight removed to prevent layout shift */\n    text-shadow: 0 0 0.5px var(--primary);', css)

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)
        
    print("Removed font-weight: bold from reader.css")

if __name__ == '__main__':
    fix_karaoke_bold()
