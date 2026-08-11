import re

def update_css():
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    new_css = """
/* --- FOCUS MODE --- */
#reader-content.focus-mode-active .karaoke-segment {
    opacity: 0.35;
    transition: opacity 0.4s ease;
}

#reader-content.focus-mode-active .karaoke-segment.active-karaoke {
    opacity: 1 !important;
}

/* --- SETTINGS SHEET --- */
/* The switch container */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}
.switch input { 
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-color);
  transition: .4s;
  border-radius: 24px;
}
.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
input:checked + .slider {
  background-color: var(--primary);
}
input:checked + .slider:before {
  transform: translateX(20px);
}
"""
    # Append to CSS
    css += new_css

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)
        
    print("Updated reader.css with focus mode and switch styles")

if __name__ == '__main__':
    update_css()
