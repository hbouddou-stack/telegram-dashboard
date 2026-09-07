with open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_html = '''        <!-- COLOR FILTERS -->
        <div style="display: flex; gap: 8px; margin-bottom: 15px; overflow-x: auto; padding-bottom: 5px;">
            <div class="chip chip-color active" onclick="setColorFilter('all', this)" style="border-radius:20px;">?? ????</div>
            <div class="chip chip-color" onclick="setColorFilter('green', this)" style="border-radius:20px; background: rgba(22, 163, 74, 0.1); color: #16a34a; border-color: #16a34a;">?? ?????? ????????</div>
            <div class="chip chip-color" onclick="setColorFilter('red', this)" style="border-radius:20px; background: rgba(239, 68, 68, 0.1); color: #ef4444; border-color: #ef4444;">?? ?? ?????? ???</div>
            <div class="chip chip-color" onclick="setColorFilter('orange', this)" style="border-radius:20px; background: rgba(249, 115, 22, 0.1); color: #f97316; border-color: #f97316;">?? ????? ??? ????</div>
            <div class="chip chip-color" onclick="setColorFilter('black', this)" style="border-radius:20px; background: rgba(17, 17, 17, 0.1); color: #111111; border-color: #111111;">? ?????</div>
        </div>
        <input class="search-box" type="text" id="search-input"'''

content = content.replace('<input class="search-box" type="text" id="search-input"', new_html)

with open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(content)
