import re

def patch_html():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Remove the button from reader-controls
    html = html.replace('<button class="control-btn" id="btn-sticky-toggle" title="Épingler/Désépingler la vidéo" style="background:#fee2e2; color:#dc2626; border:1px solid #fecaca; margin-right:4px;">📌</button>\n                    ', '')
    html = html.replace('<button class="control-btn" id="btn-sticky-toggle" title="Épingler/Désépingler la vidéo" style="background:#fee2e2; color:#dc2626; border:1px solid #fecaca; margin-right:4px;">📌</button>', '')

    # 2. Add the button to sommaire-trigger-wrapper, aligning it nicely.
    # Currently:
    # <div class="sommaire-trigger-wrapper" id="sommaire-wrapper" style="position: sticky; top: 0; z-index: 101;">
    #               <button id="open-sommaire-btn" class="sommaire-btn">
    
    old_sommaire = re.search(r'<div class="sommaire-trigger-wrapper" id="sommaire-wrapper" style="position: sticky; top: 0; z-index: 101;">\s*<button id="open-sommaire-btn" class="sommaire-btn">', html)
    if old_sommaire:
        new_sommaire = """<div class="sommaire-trigger-wrapper" id="sommaire-wrapper" style="position: sticky; top: 0; z-index: 101; display:flex; justify-content:center; align-items:center; gap:8px;">
                  <button id="open-sommaire-btn" class="sommaire-btn" style="flex:1;">"""
        html = html.replace(old_sommaire.group(0), new_sommaire)
    
    # We also need to add the toggle button after the sommaire button
    old_btn_end = re.search(r'<span class="chevron">▼</span>\s*</button>', html)
    if old_btn_end:
        new_btn_end = """<span class="chevron">▼</span>
                  </button>
                  <button class="control-btn" id="btn-sticky-toggle" title="Désépingler la vidéo" style="background:var(--surface); color:var(--text); border:1.5px solid var(--border-color); border-radius:24px; padding:10px 16px; font-size:16px;">📌</button>"""
        html = html.replace(old_btn_end.group(0), new_btn_end)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML successfully patched.")

if __name__ == '__main__':
    patch_html()
