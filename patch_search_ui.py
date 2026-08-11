import re

def patch_html():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    new_chips = """<div class="filter-chips" id="filter-chips">
                <button class="chip active" data-filter="title_only">📌 العناوين فقط</button>
                <button class="chip" data-filter="all">🔎 الكل (البحث العام)</button>
                <button class="chip" data-filter="fiche">📖 فيشات المراجعة</button>
                <button class="chip" data-filter="trans">📝 التفريغ الحرفي</button>
            </div>"""

    old_chips = re.search(r'<div class="filter-chips" id="filter-chips".*?</div>', html, re.DOTALL)
    if old_chips:
        html = html.replace(old_chips.group(0), new_chips)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML patched")

def patch_js():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # We need to find the HTML generation for the search results
    old_s_card = re.search(r'html \+= `<div class="s-card".*?</div>`;\n\s*\}\);', js, re.DOTALL)
    if old_s_card:
        new_result_card = """html += `<div class="result-card" onclick="openSearchResult('${item.subject}', ${item.lessonNum}, ${b.start_seconds})">
            <div style="padding:14px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px; align-items:flex-start;">
                    <h4 style="margin:0; font-size:14.5px; color:var(--text); line-height:1.4;">${hl(b.title, queries[0])}</h4>
                    <span class="badge badge-${item.subject}" style="flex-shrink:0; margin-right:10px;">${item.subjectLabel} ${item.lessonNum}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:12px; color:var(--primary); font-weight:600; background:var(--primary-light, rgba(79, 70, 229, 0.1)); padding:4px 8px; border-radius:6px;">
                        ⏱ ${formatSeconds(b.start_seconds)}
                    </div>
                </div>
            </div>
        </div>`;
    });"""
        js = js.replace(old_s_card.group(0), new_result_card)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print("JS patched")

if __name__ == '__main__':
    patch_html()
    patch_js()
