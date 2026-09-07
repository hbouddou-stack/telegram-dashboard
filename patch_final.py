import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update List Card: Source Badge & Remove School Level
# Find source logic in renderStudents
old_src_logic = r"// Source\s*const src = String\(s\.source \|\| ' '\);"
new_src_logic = '''// Source
                const srcStr = String(s.source || '').toLowerCase();
                let srcBadge = `<span style="font-size:0.72rem;color:var(--text2);">م. ${s.source || '-'}</span>`;
                if (srcStr.includes('sheet') || srcStr.includes('google')) {
                    srcBadge = `<span style="background:#0f9d58; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:0.72rem;">Sheet</span>`;
                } else if (srcStr.includes('excel')) {
                    srcBadge = `<span style="background:#107c41; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:0.72rem;">Excel</span>`;
                }'''
c = re.sub(old_src_logic, new_src_logic, c)

# Find HTML template for list card
old_list_html = r'''\$\{s\.school_level \? `<span style="font-size:0\.72rem;background:#0088cc;color:white;padding:2px 8px;border-radius:10px;font-weight:bold;">المستوى الدراسي: \$\{s\.school_level\}</span>` : ''\}\s*<span style="font-size:0\.72rem;color:var\(--text2\);">م\. \$\{src\}</span>'''
new_list_html = r'''${srcBadge}'''
c = re.sub(old_list_html, new_list_html, c)


# 2. Fix Labels in General Tab (Translate to Arabic)
# The labels are currently mixed or in French. I will replace the whole div lines using their IDs.

def replace_chip_label(html, chip_id, new_label, emoji=""):
    pattern = r'(<div class="chip" id="' + chip_id + r'".*?>)' + r'.*?' + r'(<span id="' + chip_id + r'-text")'
    replacement = r'\1' + emoji + ' ' + new_label + r' : \2'
    return re.sub(pattern, replacement, html)

c = replace_chip_label(c, "profile-profession", "المهنة", "💼")
c = replace_chip_label(c, "profile-country", "بلد الإقامة", "📍")
c = replace_chip_label(c, "profile-nationality", "الجنسية", "🌍")
c = replace_chip_label(c, "profile-arabiclevel", "مستوى اللغة العربية", "🗣️")

# 3. Move Arabic Level from General to Academy Tab
arabic_level_chip = r'<div class="chip" id="profile-arabiclevel".*?</div>'
match = re.search(arabic_level_chip, c)
if match:
    chip_html = match.group(0)
    # Remove from current location
    c = c.replace(chip_html, '')
    
    # Add to Academy Tab (mcontent-academy)
    academy_target = r'<div id="mcontent-academy" class="mcontent" style="overflow-y:auto; flex:1; padding-right:5px;">'
    new_academy = academy_target + '\n                ' + chip_html
    c = c.replace(academy_target, new_academy)

# Also translate Payment status label just in case it's not translated
c = replace_chip_label(c, "profile-payment", "حالة الدفع", "💳")
c = replace_chip_label(c, "profile-inscription", "تاريخ التسجيل", "📅")


with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("SUCCESS")
