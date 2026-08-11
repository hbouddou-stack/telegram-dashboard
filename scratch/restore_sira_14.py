import json
import sqlite3
import os
import re

backup_files = [
    'telegram-bot-backup/dashboard/transcripts.json.bak',
    'telegram-bot-backup/dashboard/transcripts.json.before_fix',
    'transcripts.json.bak',
    'transcripts.json.before_fix',
    'telegram-bot-backup/_backups/transcripts.json'
]

original_blocks = None

# 1. Search for Sira 14 thematic blocks in backup files
for path in backup_files:
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for l in data:
                if l.get('subject') == 'sira' and str(l.get('lessonNum')) == '14':
                    blocks = l.get('thematic_blocks', [])
                    if blocks and any('start_seconds' in b for b in blocks):
                        print(f"Found original blocks in {path}! Count: {len(blocks)}")
                        original_blocks = blocks
                        break
            if original_blocks:
                break
        except Exception as e:
            print(f"Could not read {path}: {e}")

if not original_blocks:
    print("Could not find Sira 14 blocks in JSON backups. Let's look for backup databases...")
    # Sira 14 has 4 thematic blocks. Let's hardcode the original blocks as fallback if needed.
    # But let's check if we can reconstruct them or fallback to the exact values we saw in our inspect_blocks_keys.txt.
    # In inspect_blocks_keys.txt, we saw:
    # 1. title: "غزوة بدر الكبرى وأحداثها", start_seconds: 34, end_seconds: 666
    # 2. title: "فرض زكاة الفطر والخلاف في زكاة المال", start_seconds: 698, end_seconds: 1028
    # 3. title: "وفاة السيدة رقية وزواج السيدة فاطمة", start_seconds: 1028, end_seconds: 1249
    # 4. title: "إسلام العباس وقبائل يهود المدينة", start_seconds: 1365, end_seconds: 1672
    print("Reconstructing from inspect_blocks_keys.txt data...")
    original_blocks = [
        {
            "title": "غزوة بدر الكبرى وأحداثها",
            "timestamp": "0:34",
            "start_seconds": 34,
            "end_seconds": 666,
            "citation": "الْغَزْوَةُ الْكُبْرَى الَّتِي بِبَدْرِ <i></i>* فِي الصَّوْمِ فِي سَابِعَ عَشْرِ الشَّهْرِ",
            "explanation": "تناول الشيخ تفاصيل غزوة بدر الكبرى، بدءاً من خروج النبي ﷺ لاعتراض قافلة قريش، وتغير الموازين باستنفار قريش لجيشها، وصولاً إلى استشارة النبي ﷺ للأنصار والمهاجرين وتأييدهم له، ونصر الله للمسلمين في يوم الفرقان.",
            "video_link": "https://www.youtube.com/watch?v=kXH2nzldhF8&t=34s",
            "search_text": "غزوة بدر الكبرى وأحداثها الْغَزْوَةُ الْكُبْرَى الَّتِي بِبَدْرِ *** فِي الصَّوْمِ فِي سَابِعَ عَشْرِ الشَّهْرِ تناول الشيخ تفاصيل غزوة بدر الكبرى،..."
        },
        {
            "title": "فرض زكاة الفطر والخلاف في زكاة المال",
            "timestamp": "11:38",
            "start_seconds": 698,
            "end_seconds": 1028,
            "citation": "وَوَجَبَتْ فِيهِ زَكَاةُ الْفِطْرِ <i></i>* مِنْ بَعْدِ بَدْرٍ بِلَيَالٍ عَشْرِ، وَفِي زَكَاةِ الْمَالِ خُلْفٌ فَادْرِ",
            "explanation": "بين الشيخ توقيت فرض زكاة الفطر في نهاية شهر رمضان من السنة الثانية للهجرة، وأشار إلى وجود خلاف علمي في توقيت فرض زكاة المال (ذات النصب)، مؤكداً على أدب الخلاف والإنصاف العلمي.",
            "video_link": "https://www.youtube.com/watch?v=kXH2nzldhF8&t=698s",
            "search_text": "فرض زكاة الفطر والخلاف في زكاة المال وَوَجَبَتْ فِيهِ زَكَاةُ الْفِطْرِ *** مِنْ بَعْدِ بَدْرٍ بِلَيَالٍ عَشْرِ، وَفِي زَكَاةِ الْمَالِ خُلْفٌ فَادْرِ..."
        },
        {
            "title": "وفاة السيدة رقية وزواج السيدة فاطمة",
            "timestamp": "17:08",
            "start_seconds": 1028,
            "end_seconds": 1249,
            "citation": "وَمَاتَتِ ابْنَةُ النَّبِيِّ الْبَرِّ <i></i>* رُقَيَّةٌ قَبْلَ رُجُوعِ السَّفْرِ، زَوْجَةُ عُثْمَانَ وَعُرْسُ الطُّهْرِ فَاطِمَةٌ عَلَى عَلِيِّ الْقَدْرِ",
            "explanation": "تحدث الشيخ عن وفاة السيدة رقية زوجة عثمان بن عفان رضي الله عنهما قبيل عودة النبي ﷺ de بدر، وتبرئته لعثمان de التخلف عن الغزوة، ثم ذكر زواج السيدة فاطمة رضي الله عنها de علي بن أبي طالب.",
            "video_link": "https://www.youtube.com/watch?v=kXH2nzldhF8&t=1028s",
            "search_text": "وفاة السيدة رقية وزواج السيدة فاطمة وَمَاتَتِ ابْنَةُ النَّبِيِّ الْبَرِّ *** رُقَيَّةٌ قَبْلَ رُجُوعِ السَّفْرِ، زَوْجَةُ عُثْمَانَ وَعُرْسُ الطُّهْرِ فَاطِمَةٌ عَلَى عَلِيِّ الْقَدْرِ..."
        },
        {
            "title": "إسلام العباس وقبائل يهود المدينة",
            "timestamp": "22:45",
            "start_seconds": 1365,
            "end_seconds": 1672,
            "citation": "وَأَسْلَمَ الْعَبَّاسُ بَعْدَ الْأَسْرِ ... وَقَيْنُقَاعَ غَزْوُهُمْ فِي الْأَثَرِ",
            "explanation": "شرح الشيخ قصة إسلام العباس بن عبد المطلب بعد أسره في بدر وكونه خرج مكرهاً، ثم افتتح الحديث عن القبائل اليهودية في المدينة (بنو قينقاع، النضير، قريظة) وطريقة تعامل النبي ﷺ معهم وفق الوثيقة النبوية.",
            "video_link": "https://www.youtube.com/watch?v=kXH2nzldhF8&t=1365s",
            "search_text": "إسلام العباس وقبائل يهود المدينة وَأَسْلَمَ الْعَبَّاسُ بَعْدَ الْأَسْرِ ... وَقَيْنُقَاعَ غَزْوُهُمْ فِي الْأَثَرِ..."
        }
    ]

# 2. Read current database record for Sira 14
db_path = 'telegram-bot-backup/backup_bot.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT lesson_data FROM course_transcripts WHERE LOWER(subject) = 'sira' AND lesson_num = 14")
row = cursor.fetchone()

if row:
    lesson_data = json.loads(row[0])
    print("Old Sira 14 blocks count in DB:", len(lesson_data.get('thematic_blocks', [])))
    
    # We will preserve the explanations and titles from the current DB if they were modified,
    # but restore the start/end seconds and timestamps.
    # In this case, let's map the current blocks to the original timings.
    # Wait, the current DB has 6 blocks, but the original had 4 blocks.
    # If the user split them into 6 blocks, they probably want 6 blocks!
    # But wait, did they split them into 6 blocks?
    # Let's see: if they split into 6 blocks, they might not have start_seconds.
    # Let's check the video links in the 6 blocks and parse the timestamps from video links!
    # Yes! In our earlier inspect_db_sira_14.txt, the 6 blocks had these video links:
    # 1. ...&t=34s -> 34s
    # 2. ...&t=698s -> 698s
    # 3. ...&t=1028s -> 1028s
    # 4. ...&t=1028s -> 1028s
    # 5. ...&t=1365s -> 1365s
    # If we parse `t=XXX` from the video links, we can reconstruct the start_seconds automatically!
    # Let's reconstruct start_seconds for the current 6 blocks in DB.
    current_blocks = lesson_data.get('thematic_blocks', [])
    updated_blocks = []
    
    for idx, block in enumerate(current_blocks):
        video_url = block.get('video_link', '')
        start_sec = None
        if video_url:
            m = re.search(r'[?&]t=(\d+)s?', video_url)
            if m:
                start_sec = int(m.group(1))
        
        # Fallback to start_seconds if already there
        if start_sec is None:
            start_sec = block.get('start_seconds', 0)
            
        # Reconstruct timestamp
        m_val = start_sec // 60
        s_val = start_sec % 60
        ts_val = f"{m_val}:{s_val:02d}"
        
        updated_blocks.append({
            "title": block.get('title', ''),
            "explanation": block.get('explanation', ''),
            "video_link": video_url,
            "poetry_verses": block.get('poetry_verses', ''),
            "search_text": block.get('search_text', ''),
            "start_seconds": start_sec,
            "timestamp": ts_val,
            "citation": block.get('citation', '')
        })
        
    # Let's sort updated_blocks by start_seconds to be sure
    updated_blocks.sort(key=lambda x: x.get('start_seconds', 0))
    
    # Calculate end_seconds
    for i in range(len(updated_blocks)):
        if i < len(updated_blocks) - 1:
            updated_blocks[i]['end_seconds'] = updated_blocks[i+1]['start_seconds']
        else:
            updated_blocks[i]['end_seconds'] = 99999
            
    lesson_data['thematic_blocks'] = updated_blocks
    
    # Update DB
    cursor.execute("UPDATE course_transcripts SET lesson_data = ? WHERE subject = 'sira' AND lesson_num = 14", (json.dumps(lesson_data, ensure_ascii=False),))
    conn.commit()
    print("Successfully updated Sira 14 in course_transcripts DB table!")
    
    # Re-sync to course_chapters SQL table
    cursor.execute("DELETE FROM course_chapters WHERE subject = 'sira' AND course_number = 14")
    conn.commit()
    
    for idx, b in enumerate(updated_blocks):
        cursor.execute(
            "INSERT OR REPLACE INTO course_chapters (subject, course_number, chapter_index, title, content, youtube_link, timestamp_seconds, poetry_verses) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('sira', 14, idx + 1, b['title'], b['search_text'], b['video_link'], b['start_seconds'], b['poetry_verses'])
        )
    conn.commit()
    print("Successfully re-synced Sira 14 to course_chapters SQL table!")

conn.close()

# 3. Regenerate transcripts.json cache on disk
# Let's run python code that reads all course_transcripts and writes to dashboard/transcripts.json
import asyncio
import sys

# Add path to import config
sys.path.append(os.path.abspath('telegram-bot-backup'))
import main

async def regen_cache():
    await main.update_static_json_cache()
    print("Successfully regenerated static transcripts.json cache!")

asyncio.run(regen_cache())
