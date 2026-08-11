import re

def patch_karaoke_css():
    with open('reader.css', 'a', encoding='utf-8') as f:
        f.write("""
/* --- KARAOKE MODE --- */
.karaoke-segment {
    transition: background-color 0.3s ease, color 0.3s ease;
    border-radius: 4px;
    padding: 0 2px;
}

.karaoke-segment.active-karaoke {
    background-color: rgba(79, 70, 229, 0.15); /* var(--primary) with 15% opacity */
    color: var(--primary);
    font-weight: bold;
}

[data-theme='dark'] .karaoke-segment.active-karaoke {
    background-color: rgba(99, 102, 241, 0.25);
    color: #818cf8;
}
""")
        
    print("Patched Karaoke CSS into reader.css")

if __name__ == '__main__':
    patch_karaoke_css()
