import re

def fix_settings_html():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # We have a corrupted HTML where settings-sheet is inside sommaire-sheet
    # Let's extract settings-overlay and settings-sheet completely.

    # Match the entire settings-sheet block
    settings_block_pattern = r"(<!-- Settings Bottom Sheet -->\s*<div class=\"bottom-sheet-overlay\" id=\"settings-overlay\"></div>\s*<div class=\"bottom-sheet\" id=\"settings-sheet\">.*?</div>\s*</div>\s*</div>)"
    
    match = re.search(settings_block_pattern, html, flags=re.DOTALL)
    if match:
        settings_html = match.group(1)
        # Remove it from its current bad location
        html = html.replace(settings_html, "")
        
        # We need to add Spacing toggle into the settings_html
        spacing_toggle = """
            <div class="setting-group">
                <h4 style="margin: 0 0 8px 0; font-size: 17px; color: var(--text);">تباعد الأسطر (Line Spacing)</h4>
                <p style="font-size: 13px; color: var(--text-2); margin-top: 0; margin-bottom: 16px;">زيادة المسافة بين الأسطر لراحة العين.</p>
                
                <label style="display: flex; align-items: center; justify-content: space-between; cursor: pointer; background: var(--surface); padding: 16px; border-radius: 12px; border: 1px solid var(--border-color);">
                    <div style="font-weight: bold; font-size: 15px; color: var(--text);">نص متباعد</div>
                    <label class="switch" style="position: relative; display: inline-block; width: 44px; height: 24px;">
                      <input type="checkbox" id="spacing-toggle" style="opacity: 0; width: 0; height: 0;">
                      <span class="slider round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 24px;"></span>
                    </label>
                </label>
            </div>
        """
        
        if 'id="spacing-toggle"' not in settings_html:
            # Insert spacing toggle before the last </div></div>
            settings_html = settings_html.replace("</div>\n        </div>\n    </div>", "</div>\n" + spacing_toggle + "\n        </div>\n    </div>")

        # Now append it outside, for instance just before <!-- Glossary Popup -->
        html = html.replace("<!-- Glossary Popup -->", settings_html + "\n\n    <!-- Glossary Popup -->")
    else:
        print("Warning: Could not find settings block to extract.")

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    # Also fix ID mismatch in JS if necessary, but in loadSettings I used focus-mode-toggle!
    # Wait, in the HTML it is id="focusModeToggle". I must change JS to use focusModeToggle.
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()
    
    js = js.replace("getElementById('focus-mode-toggle')", "getElementById('focusModeToggle')")
    
    # Increment cache buster
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=34', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=34', html)
    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Settings HTML fixed!")

if __name__ == '__main__':
    fix_settings_html()
