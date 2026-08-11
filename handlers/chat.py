from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import json
import os
import re
import math
import logging

router = Router()
logger = logging.getLogger(__name__)

# Path to transcripts
TRANSCRIPTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'transcripts.json')

def load_transcripts():
    try:
        with open(TRANSCRIPTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading transcripts: {e}")
        return []

def search_transcript(query: str):
    data = load_transcripts()
    if not data:
        return None
        
    query_lower = query.lower()
    
    # Extract numbers (lesson numbers)
    numbers = re.findall(r'\d+', query)
    target_num = int(numbers[0]) if numbers else None
    
    # Detect subject keywords
    has_sira = any(k in query_lower for k in ['سيرة', 'sira', 'sîra'])
    has_fiqh = any(k in query_lower for k in ['فقه', 'fiqh'])
    has_tawhid = any(k in query_lower for k in ['عقيدة', 'توحيد', 'aqeeda', 'tawhid'])
    
    highest_score = 0
    tied_matches = []
    
    for item in data:
        score = 0
        lesson_num = item.get('lessonNum')
        subject = item.get('subject', '')
        subject_label = item.get('subjectLabel', '')
        
        is_sira = 'سيرة' in subject_label or subject == 'sira'
        is_fiqh = 'فقه' in subject_label or subject == 'fiqh'
        is_tawhid = 'عقيدة' in subject_label or 'توحيد' in subject_label or subject == 'aqeeda'
        
        # Strict number matching
        if target_num is not None:
            if lesson_num == target_num:
                score += 15
            else:
                continue
                
        # Subject matching
        if has_sira and is_sira: score += 20
        if has_fiqh and is_fiqh: score += 20
        if has_tawhid and is_tawhid: score += 20
        
        # Keyword matching in text if no specific subject or number is provided
        if target_num is None and not (has_sira or has_fiqh or has_tawhid):
            if query_lower in str(item.get('lesson', '')).lower(): score += 5
            if query_lower in str(item.get('summary', '')).lower(): score += 2
        
        if score > 0:
            if score > highest_score:
                highest_score = score
                tied_matches = [item]
            elif score == highest_score:
                tied_matches.append(item)
                
    if highest_score == 15 and len(tied_matches) > 1 and target_num is not None:
        subjects = ' أو '.join(set([t.get('subjectLabel', '') for t in tied_matches]))
        return {
            'type': 'ambiguity',
            'message': f"عذراً، لقد وجدت عدة دروس تحمل الرقم {target_num} ({subjects}). هل يمكنك تحديد المادة التي تقصدها؟",
            'target_num': target_num
        }
        
    if tied_matches:
        return {'type': 'match', 'lesson': tied_matches[0]}
        
    return None

def get_slide_kb(subject: str, lesson_num: int):
    base_url = os.getenv("WEB_APP_URL", "https://as2ila-dashboard.railway.app")
    # Redirect to the advanced reader (Liseuse) instead of the PowerPoint
    reader_url = f"{base_url}/reader.html?subject={subject}&lesson={lesson_num}&v=p5"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 افتح القارئ التفاعلي (Liseuse)", web_app=WebAppInfo(url=reader_url))]
    ])
    return kb

@router.message(F.text)
async def handle_free_text(message: Message):
    # Try to search course transcripts
    match_result = search_transcript(message.text)
    
    if match_result:
        if match_result['type'] == 'ambiguity':
            num = match_result['target_num']
            # Send ambiguity message with quick reply buttons for subjects
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📜 السيرة النبوية", callback_data=f"sel_subj_sira_{num}")],
                [InlineKeyboardButton(text="📖 الفقه", callback_data=f"sel_subj_fiqh_{num}")],
                [InlineKeyboardButton(text="🕌 العقيدة والتوحيد", callback_data=f"sel_subj_tawhid_{num}")]
            ])
            await message.reply(match_result['message'], reply_markup=kb)
        else:
            lesson = match_result['lesson']
            kb = get_slide_kb(lesson.get('subject'), lesson.get('lessonNum'))
            title = lesson.get('subjectLabel', '') + " - " + str(lesson.get('lesson', ''))
            await message.reply(f"لقد وجدت الدرس الذي تبحث عنه:\n<b>{title}</b>\n\nاضغط على الزر أدناه لفتح العرض التفاعلي:", reply_markup=kb, parse_mode="HTML")
        return
        
    pass

@router.callback_query(F.data.startswith("sel_subj_"))
async def handle_subject_selection(callback: CallbackQuery):
    data = callback.data
    parts = data.split("_")
    if len(parts) >= 4:
        subj = parts[2]
        try:
            num = int(parts[3])
            
            # Map shorthand to actual subject ID
            subject_id = subj
            subject_label = ""
            if subj == "sira":
                subject_id = "sira"
                subject_label = "السيرة النبوية"
            elif subj == "fiqh":
                subject_id = "fiqh"
                subject_label = "الفقه"
            elif subj == "tawhid":
                subject_id = "aqeeda"
                subject_label = "العقيدة والتوحيد"
                
            kb = get_slide_kb(subject_id, num)
            title = f"{subject_label} - الدرس {num}"
            await callback.message.edit_text(f"لقد اخترت:\n<b>{title}</b>\n\nاضغط على الزر أدناه لفتح العرض التفاعلي:", reply_markup=kb, parse_mode="HTML")
        except ValueError:
            await callback.answer("خطأ في قراءة رقم الدرس", show_alert=True)
    await callback.answer()

