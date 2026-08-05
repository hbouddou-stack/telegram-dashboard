import json
import re

txt_path = r"C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot\lessons\transcripts\sira\sira_14.txt"
json_path = r"C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\dashboard\transcripts.json"

with open(txt_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

def clean_text(text):
    text = re.sub(r'^\d+:\d+\s+', '', text)
    text = re.sub(r'\n\d+:\d+\s+', '\n', text)
    return text.strip()

# We will define the blocks based on start_seconds
# Format: {"title": "", "is_sub_theme": bool, "start_seconds": int, "end_seconds": int}
blocks_def = [
    {"title": "غزوة بدر الكبرى (La Grande Bataille de Badr)", "is_sub_theme": False, "start": 0, "end": 88},
    {"title": "خروج النبي صلى الله عليه وسلم لاعتراض قافلة أبي سفيان", "is_sub_theme": True, "start": 88, "end": 207},
    {"title": "نجاة القافلة وخروج جيش قريش للقضاء على المسلمين", "is_sub_theme": True, "start": 207, "end": 294},
    {"title": "استشارة النبي للصحابة (المهاجرين والأنصار) وموقف سعد بن معاذ", "is_sub_theme": True, "start": 294, "end": 462},
    {"title": "اندلاع المعركة، مقتل صناديد قريش، ويوم الفرقان", "is_sub_theme": True, "start": 462, "end": 609},
    {"title": "الغنائم وسد فاقة المهاجرين", "is_sub_theme": True, "start": 609, "end": 698},
    {"title": "فرض زكاة الفطر", "is_sub_theme": False, "start": 698, "end": 760},
    {"title": "الخلاف في توقيت فرض زكاة المال", "is_sub_theme": False, "start": 760, "end": 857},
    {"title": "منهجية التعامل مع الخلاف العلمي (رسالة لطلبة العلم والعوام)", "is_sub_theme": True, "start": 857, "end": 1019},
    {"title": "وفاة السيدة رقية وزواج السيدة فاطمة", "is_sub_theme": False, "start": 1019, "end": 1068},
    {"title": "مرض ووفاة رقية وتخلف عثمان بن عفان عن بدر لتمريضها", "is_sub_theme": True, "start": 1068, "end": 1266},
    {"title": "زواج السيدة فاطمة من علي بن أبي طالب رضي الله عنهما", "is_sub_theme": True, "start": 1266, "end": 1358},
    {"title": "إسلام العباس بن عبد المطلب", "is_sub_theme": False, "start": 1358, "end": 1498},
    {"title": "يهود المدينة وقبيلة بني قينقاع", "is_sub_theme": False, "start": 1498, "end": 1516},
    {"title": "أصل استيطان القبائل اليهودية الثلاث في يثرب", "is_sub_theme": True, "start": 1516, "end": 1600},
    {"title": "الوثيقة النبوية وإقرار التعددية في مجتمع المدينة", "is_sub_theme": True, "start": 1600, "end": 999999}
]

# Extract full text and segments
segments = []
for line in lines:
    m = re.match(r'^(\d+):(\d+)\s+(.*)', line.strip())
    if m:
        mins, secs, text = m.groups()
        total_secs = int(mins) * 60 + int(secs)
        segments.append({"ts": f"{mins}:{secs.zfill(2)}", "sec": total_secs, "text": text})

full_text = " ".join([s["text"] for s in segments])

thematic_blocks = []
for i, b in enumerate(blocks_def):
    block_segs = [s for s in segments if b["start"] <= s["sec"] < b["end"]]
    raw_text = " ".join([s["text"] for s in block_segs])
    
    # Identify poetry and wrap it
    # We look for common patterns or just wrap the first line if it's the known poem
    reading = raw_text
    # Simple poetry wrapping based on known verses in this text
    poems = [
        "وَالْغَزْوَةُ الْكُبْرَى الَّتِي بِبَدْرِ \*\*\* فِي الصَّوْمِ فِي سَابِعَ عَشْرِ الشَّهْرِ",
        "وَوَجَبَتْ فِيهِ زَكَاةُ الْفِطْرِ \*\*\* مِنْ بَعْدِ بَدْرٍ بِلَيَالٍ عَشْرِ",
        "وَفِي زَكَاةِ الْمَالِ خُلْفٌ فَادْرِ",
        "وَمَاتَتِ ابْنَةُ النَّبِيِّ الْبَرِّ \*\*\* رُقَيَّةٌ قَبْلَ رُجُوعِ السَّفْرِ",
        "زَوْجَةُ عُثْمَانَ وَعُرْسُ الطُّهْرِ \*\*\* فَاطِمَةٌ عَلَى عَلِيِّ الْقَدْرِ",
        "وَأَسْلَمَ الْعَبَّاسُ بَعْدَ الْأَسْرِ",
        "وَقَيْنُقَاعَ غَزْوُهُمْ فِي الْأَثَرِ \*\*\* وَبَعْدُ ضَحَّى يَوْمَ عِيدِ النَّحْرِ"
    ]
    
    for p in poems:
        reading = re.sub(rf'({p})', r'\n[POEME]\1[/POEME]\n', reading)
    
    # Format MM:SS
    m = b["start"] // 60
    s = b["start"] % 60
    timestamp = f"{m}:{str(s).zfill(2)}"
    
    thematic_blocks.append({
        "title": b["title"],
        "timestamp": timestamp,
        "start_seconds": b["start"],
        "end_seconds": b["end"] if b["end"] != 999999 else segments[-1]["sec"] + 10,
        "is_sub_theme": b["is_sub_theme"],
        "search_text": raw_text,
        "reading_text": reading,
        "explanation": "",
        "video_link": "",
        "poetry_verses": ""
    })

# Load JSON
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update Sira 14
updated = False
for item in data:
    if item.get("subject") == "sira" and str(item.get("lessonNum")) == "14":
        item["thematic_blocks"] = thematic_blocks
        if "full_text" not in item or not item["full_text"]:
            item["full_text"] = full_text
        if "segments" not in item or not item["segments"]:
            item["segments"] = segments
        updated = True
        break

if not updated:
    # If not found, we shouldn't really reach here since we verified it exists, but just in case
    print("Sira 14 not found in transcripts.json")

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Successfully injected Sira 14 thematic blocks!")
