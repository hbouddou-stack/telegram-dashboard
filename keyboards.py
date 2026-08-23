from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import os

SUBJECT_LABELS = {
    "fiqh": "الف‚ه",
    "sira": "السŠرة النبˆية",
    "nahw": "النحˆ",
    "aqeeda": "الع‚يدة",
    "tajweed": "ع„م التجˆيد"
}

def get_hidden_items_sync(category: str) -> list:
    import sqlite3
    import os
    from config import DATABASE_PATH
    try:
        if not os.path.exists(DATABASE_PATH):
            return []
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (f"hidden_{category}",))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            return [item.strip() for item in row[0].split(",") if item.strip()]
    except Exception:
        pass
    return []

def get_main_inline_keyboard(is_admin: bool = False, remaining_count: int = None, unread_count: int = 0) -> InlineKeyboardMarkup:
    """Create the inline main menu keyboard with standard categories."""
    hidden_buttons = get_hidden_items_sync("buttons")
    
    inbox_label = "📬 صندوق الرسائل"
    if unread_count > 0:
        inbox_label += f" ({unread_count} 🔴)"
        
    rows = []
    
    # Row 1: Training Menu
    row1 = [
        InlineKeyboardButton(text="📝 أتدرب", callback_data="main_training_menu")
    ]
    rows.append(row1)
    

    # Row 1.2: Liseuse (Dashboard & Reader)
    base_url = get_webapp_base_url()
    if True: # Always show Mini App button
        rows.append([
            InlineKeyboardButton(text="💻 منصة الطالب والتطبيقات 📱", web_app=WebAppInfo(url=f"{base_url}/reader.html?v=dash2"))
        ])
        rows.append([
            InlineKeyboardButton(text="🧪 اختبار سريع (Test Mini App)", web_app=WebAppInfo(url=f"{base_url}/test.html?v=1"))
        ])
    
    # Row 1.5: Revision Library (full width)
    if "revision" not in hidden_buttons:
        rows.append([InlineKeyboardButton(text="📖 مكتبتي الشاملة", callback_data="main_revision")])

    # Row 2: Favorites, Errors
    row2 = []
    if "favorites" not in hidden_buttons:
        row2.append(InlineKeyboardButton(text="⭐ المفضلة", callback_data="main_favorites"))
    if "errors" not in hidden_buttons:
        row2.append(InlineKeyboardButton(text="❌ أخطائي", callback_data="main_errors"))
    if row2:
        rows.append(row2)
        
    # Row 3: Progress, Inbox
    row3 = []
    if "progress" not in hidden_buttons:
        row3.append(InlineKeyboardButton(text="📊 تقدمي", callback_data="main_progress"))
    if "inbox" not in hidden_buttons:
        row3.append(InlineKeyboardButton(text=inbox_label, callback_data="student_inbox"))
    if row3:
        rows.append(row3)
        
    # Row 4: Support & Settings (Merged)
    row4 = []
    if "support" not in hidden_buttons:
        row4.append(InlineKeyboardButton(text="💬 الدعم والمساعدة", callback_data="main_support"))
    if "settings" not in hidden_buttons:
        row4.append(InlineKeyboardButton(text="⚙️ إعداداتي", callback_data="main_settings"))
    if row4:
        rows.append(row4)
        
    if is_admin:
        rows.append([
            InlineKeyboardButton(text="🛠️ وضع المشرف", callback_data="main_admin")
        ])
        
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_training_menu_keyboard() -> InlineKeyboardMarkup:
    """Sub-menu for training options."""
    rows = [
        [InlineKeyboardButton(text="🎯 التدريب على مادة / درس معين", callback_data="main_new_quiz")],
        [InlineKeyboardButton(text="🎓 اجتياز امتحان تجريبي شامل", callback_data="exam_blanc_start")],
        [InlineKeyboardButton(text="â†©ï¸ العودة للقائمة", callback_data="main_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Create an inline gender selection keyboard for user registration."""
    rows = [
        [
            InlineKeyboardButton(text="👦 أخ", callback_data="register_gender:male"),
            InlineKeyboardButton(text="👧 أخت", callback_data="register_gender:female")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_academic_year_keyboard() -> InlineKeyboardMarkup:
    """Create an inline academic year selection keyboard for user registration."""
    rows = [
        [
            InlineKeyboardButton(text="🎓 السنة الأولى", callback_data="register_year:1"),
            InlineKeyboardButton(text="🎓 السنة الثانية", callback_data="register_year:2")
        ],
        [
            InlineKeyboardButton(text="🎓 السنة الثالثة", callback_data="register_year:3"),
            InlineKeyboardButton(text="🎓 السنة الرابعة", callback_data="register_year:4")
        ],
        [
            InlineKeyboardButton(text="⏭️ تخطي (لا أريد التحديد)", callback_data="register_year:skip")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_start_onboarding_keyboard() -> InlineKeyboardMarkup:
    """Create a button to start onboarding."""
    rows = [
        [
            InlineKeyboardButton(text="دع†ا نتعرف! ðŸ¤", callback_data="start_onboarding")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_name_choice_keyboard(first_name: str, last_name: str, username: str) -> InlineKeyboardMarkup:
    """Create keyboard for selecting how the bot should call the user."""
    rows = []
    if first_name:
        rows.append([InlineKeyboardButton(text=f"ðŸ‘¤ الاس… الأˆل: {first_name}", callback_data="name_choice:first")])
    
    full_name = f"{first_name or ''} {last_name or ''}".strip()
    if last_name and first_name:
        rows.append([InlineKeyboardButton(text=f"ðŸ‘¤ الاس… الكا…ل: {full_name}", callback_data="name_choice:full")])
        
    rows.append([InlineKeyboardButton(text="ðŸš« لا تذƒر اس…ي (لقب عا… ف‚ط)", callback_data="name_choice:generic")])
    rows.append([InlineKeyboardButton(text="âœï¸ كتابة اس… مخصص...", callback_data="name_choice:custom")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_guide_page_keyboard(page: int) -> InlineKeyboardMarkup:
    """Create navigation keyboard for the onboarding guide."""
    rows = []
    if page == 1:
        rows.append([InlineKeyboardButton(text="التالي âž¡ï¸", callback_data="guide_page:2")])
    elif page == 2:
        rows.append([
            InlineKeyboardButton(text="â¬…️ الساب‚", callback_data="guide_page:1"),
            InlineKeyboardButton(text="التالي âž¡ï¸", callback_data="guide_page:3")
        ])
    elif page == 3:
        rows.append([
            InlineKeyboardButton(text="â¬…️ الساب‚", callback_data="guide_page:2")
        ])
        rows.append([InlineKeyboardButton(text="ðŸŸ¢ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ ðŸŸ¢", callback_data="q_ignored")])
        rows.append([
            InlineKeyboardButton(text="ðŸš€ ابدأ الت…رŠن", callback_data="guide_finish")
        ])
        rows.append([InlineKeyboardButton(text="ðŸŸ¢ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ ðŸŸ¢", callback_data="q_ignored")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

THEMES = {
    "fiqh": {
        "عبادات": {
            "label": "أحƒا… العبادات",
            "lessons": [14, 15, 16]
        },
        "معا…لات": {
            "label": "المعا…لات وف‚ه النواز„",
            "lessons": [17, 18, 19, 20, 21, 22, 23, 24]
        }
    },
    "sira": {
        "makki": {
            "label": "الع‡د المكي والنشأة",
            "lessons": [14, 15, 16, 17, 18]
        },
        "madani": {
            "label": "الع‡د المد†ي والغزˆات",
            "lessons": [19, 20, 21, 22, 23, 24]
        }
    },
    "nahw": {
        "marfouat": {
            "label": "المرفˆعات والمنصˆبات",
            "lessons": [14, 15, 16]
        },
        "tawabi": {
            "label": "التˆابع والأساليب النحˆية",
            "lessons": [17, 18, 19, 20, 21, 22, 23, 24]
        }
    },
    "aqeeda": {
        "tawhid": {
            "label": "أصˆل الع‚يدة والتˆحŠد",
            "lessons": [14, 15, 16]
        },
        "firaq": {
            "label": "المذا‡ب والفر‚ والولاء والبراء",
            "lessons": [17, 18, 19, 20, 21, 22, 23, 24]
        }
    }
}

def get_subject_list_keyboard(remaining_counts: dict = None) -> InlineKeyboardMarkup:
    """Create a 2-column square layout keyboard showing available subjects with category emojis and remaining counts."""
    if remaining_counts is None:
        remaining_counts = {}
        
    SUBJECT_EMOJIS = {
        "fiqh": "ðŸ“š",
        "sira": "ðŸ•Œ",
        "nahw": "âœï¸",
        "aqeeda": "ðŸ’­",
        "tajweed": "ðŸŽ™️"
    }
    
    hidden_subjects = get_hidden_items_sync("subjects")
    
    rows = []
    row = []
    for sub, label in SUBJECT_LABELS.items():
        if sub in hidden_subjects:
            continue
        sub_emoji = SUBJECT_EMOJIS.get(sub, "ðŸ“š")
        rem_count = remaining_counts.get(sub, 0)
        
        btn_text = f"{sub_emoji} {label}"
        if rem_count > 0:
            btn_text += f" ({rem_count})"
            
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"sel_sub:{sub}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="âŒ إ„غاء", callback_data="quiz_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_quiz_mode_selection_keyboard(subject: str) -> InlineKeyboardMarkup:
    """Create keyboard to choose selection pathway (Lessons/Years/Themes)."""
    rows = []
    if subject == "sira":
        rows.append([
            InlineKeyboardButton(text="📖  حسب الدرˆس", callback_data="sel_mode:lessons"),
            InlineKeyboardButton(text="ðŸ“… حسب الس†وات", callback_data="sel_mode:years")
        ])
        rows.append([
            InlineKeyboardButton(text="🎯  حسب المحاˆر", callback_data="sel_mode:themes")
        ])
    else:
        rows.append([
            InlineKeyboardButton(text="📖  حسب الدرˆس", callback_data="sel_mode:lessons"),
            InlineKeyboardButton(text="🎯  حسب المحاˆر", callback_data="sel_mode:themes")
        ])
    rows.append([InlineKeyboardButton(text="â†©ï¸ تغŠير المادة", callback_data="mode_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_lessons_grid_keyboard(subject: str, available_lessons: list[int], selected_lessons: list[int], progress_stats: dict = None, remaining_counts: dict = None, new_lessons: list[int] = None) -> InlineKeyboardMarkup:
    """Create a 2-column grid of lessons with checkboxes, progress status icons, confirm and back buttons."""
    hidden_lessons = get_hidden_items_sync(f"lessons_{subject}")
    
    rows = []
    row = []
    for l in available_lessons:
        if str(l) in hidden_lessons or l in hidden_lessons:
            continue
        is_selected = l in selected_lessons
        check_char = "âœ…" if is_selected else "â¬œ"
        
        # Get progress indicator emoji
        prog_emoji = ""
        if progress_stats and l in progress_stats:
            prog_emoji = f" {progress_stats[l]}"
            
        remaining_str = ""
        if remaining_counts and l in remaining_counts:
            remaining_str = f" ({remaining_counts[l]})"
            
        badge = " ðŸ†•" if (new_lessons and l in new_lessons) else ""
        
        row.append(InlineKeyboardButton(
            text=f"{check_char} {l}{remaining_str}{prog_emoji}{badge}",
            callback_data=f"tog_les:{l}"
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
        
    # Checkbox actions: All / None
    rows.append([
        InlineKeyboardButton(text="ðŸ”” تحدŠد الكل", callback_data="les_act:all"),
        InlineKeyboardButton(text="ðŸ”• إ„غاء الكل", callback_data="les_act:none")
    ])
    
    # Confirm & Back (separated rows)
    rows.append([InlineKeyboardButton(text="ðŸš€ تأƒيد الاختŠار", callback_data="les_confirm")])
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة", callback_data="les_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_themes_grid_keyboard(subject: str, selected_themes: list[int] = None, available_themes: list[dict] = None) -> InlineKeyboardMarkup:
    """Create a keyboard of themes for a subject with simple buttons (main theme is single-choice)."""
    hidden_themes = get_hidden_items_sync(f"themes_{subject}")
    
    rows = []
    row = []
    if available_themes:
        for th in available_themes:
            th_id = th['id']
            lbl = th['title']
            if lbl in hidden_themes or str(th_id) in hidden_themes:
                continue
            btn = InlineKeyboardButton(text=lbl, callback_data=f"select_th:{th_id}")
            if len(lbl) >= 28:
                if row:
                    rows.append(row)
                    row = []
                rows.append([btn])
            else:
                row.append(btn)
                if len(row) == 2:
                    rows.append(row)
                    row = []
        if row:
            rows.append(row)
    else:
        subject_themes = THEMES.get(subject, {})
        for th_key, th_info in subject_themes.items():
            if th_key in hidden_themes:
                continue
            lbl = th_info['label']
            btn = InlineKeyboardButton(text=lbl, callback_data=f"select_th:{th_key}")
            if len(lbl) >= 28:
                if row:
                    rows.append(row)
                    row = []
                rows.append([btn])
            else:
                row.append(btn)
                if len(row) == 2:
                    rows.append(row)
                    row = []
        if row:
            rows.append(row)
            
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة", callback_data="th_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_sub_themes_grid_keyboard(subject: str, selected_sub_themes: list[str], available_sub_themes: list[str] = None) -> InlineKeyboardMarkup:
    """Create a keyboard of sub-themes for a selected theme with checkboxes, Select All/None, confirm and back buttons."""
    rows = []
    row = []
    
    if available_sub_themes:
        for idx, subth in enumerate(available_sub_themes):
            is_selected = subth in selected_sub_themes
            check_char = "âœ…" if is_selected else "â¬œ"
            row.append(InlineKeyboardButton(
                text=f"{check_char} {subth}",
                callback_data=f"tog_subth:{idx}"
            ))
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
            
    # Select All / Deselect All
    rows.append([
        InlineKeyboardButton(text="âœ… تحدŠد الكل", callback_data="subth_all"),
        InlineKeyboardButton(text="â¬œ إ„غاء تحدŠد الكل", callback_data="subth_none")
    ])
    
    # Confirm & Back
    rows.append([InlineKeyboardButton(text="ðŸš€ تأƒيد الاختŠار", callback_data="subth_confirm")])
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة لخŠارات المحاˆر", callback_data="subth_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_years_grid_keyboard(selected_years: list[int]) -> InlineKeyboardMarkup:
    """Create a 2-column grid of Hijri years with checkboxes, confirm and back buttons."""
    available_years = list(range(1, 12))
    rows = []
    row = []
    for y in available_years:
        is_selected = y in selected_years
        check_char = "âœ…" if is_selected else "â¬œ"
        row.append(InlineKeyboardButton(
            text=f"{check_char} {y} هÙ€",
            callback_data=f"tog_yr:{y}"
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
        
    rows.append([
        InlineKeyboardButton(text="ðŸ”” تحدŠد الكل", callback_data="yr_act:all"),
        InlineKeyboardButton(text="ðŸ”• إ„غاء الكل", callback_data="yr_act:none")
    ])
    
    rows.append([InlineKeyboardButton(text="ðŸš€ تأƒيد الاختŠار", callback_data="yr_confirm")])
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة", callback_data="yr_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_exam_settings_keyboard(settings: dict, layout: str = 'classic', ai_disabled: bool = False) -> InlineKeyboardMarkup:
    """Create the RTL horizontal-choice configuration table layout."""
    # Row 0: Column Headers (from left to right in Python: Col 3, Col 2, Col 1, Header Title)
    row_headers = [
        InlineKeyboardButton(text="3", callback_data="q_ignored"),
        InlineKeyboardButton(text="2", callback_data="q_ignored"),
        InlineKeyboardButton(text="1", callback_data="q_ignored"),
        InlineKeyboardButton(text="⚙️  الضبط", callback_data="q_ignored")
    ]
    
    # Row 1: Timer (الوقت)
    timer_val = settings.get("timer", "unlimited")
    t_15s = "âœ… 15ث" if timer_val == "15s" else "âšª 15ث"
    t_30s = "âœ… 30ث" if timer_val == "30s" else "âšª 30ث"
    t_unlimited = "âœ… مفتˆح" if timer_val == "unlimited" else "âšª مفتˆح"
    
    row_timer = [
        InlineKeyboardButton(text=t_unlimited, callback_data="set_val:timer:unlimited"),
        InlineKeyboardButton(text=t_30s, callback_data="set_val:timer:30s"),
        InlineKeyboardButton(text=t_15s, callback_data="set_val:timer:15s"),
        InlineKeyboardButton(text="⏱️ الوقت", callback_data="q_ignored")
    ]
    
    # Row 2: Correction (التصحŠح)
    corr_val = settings.get("correction", "immediate")
    c_immediate = "âœ… فˆرŠ" if corr_val == "immediate" else "âšª فˆرŠ"
    c_end = "âœ… النهاŠة" if corr_val == "end" else "âšª النهاŠة"
    c_strict = "âœ… ا…تحا†" if corr_val == "strict" else "âšª ا…تحا†"
    
    row_correction = [
        InlineKeyboardButton(text=c_strict, callback_data="set_val:correction:strict"),
        InlineKeyboardButton(text=c_end, callback_data="set_val:correction:end"),
        InlineKeyboardButton(text=c_immediate, callback_data="set_val:correction:immediate"),
        InlineKeyboardButton(text="ðŸ’¬ التصحŠح", callback_data="q_ignored")
    ]
    
    # Row 3: Question Limit (العدد)
    limit_val = int(settings.get("limit", 10))
    l_5 = "âœ… 5" if limit_val == 5 else "âšª 5"
    l_10 = "âœ… 10" if limit_val == 10 else "âšª 10"
    l_20 = "âœ… 20" if limit_val == 20 else "âšª 20"
    
    row_limit = [
        InlineKeyboardButton(text=l_20, callback_data="set_val:limit:20"),
        InlineKeyboardButton(text=l_10, callback_data="set_val:limit:10"),
        InlineKeyboardButton(text=l_5, callback_data="set_val:limit:5"),
        InlineKeyboardButton(text="ðŸ”¢ العدد", callback_data="q_ignored")
    ]
    
    # Row 4: Source (الف„ترة)
    source_val = settings.get("source", "smart")
    s_smart = "âœ… الذكي" if source_val == "smart" else "âšª الذكي"
    s_errors = "âœ… الأخطاء" if source_val == "errors" else "âšª الأخطاء"
    s_all = "âœ… الكل" if source_val == "all" else "âšª الكل"
    
    row_source = [
        InlineKeyboardButton(text=s_all, callback_data="set_val:source:all"),
        InlineKeyboardButton(text=s_smart, callback_data="set_val:source:smart"),
        InlineKeyboardButton(text=s_errors, callback_data="set_val:source:errors"),
        InlineKeyboardButton(text="🎯  الف„ترة", callback_data="q_ignored")
    ]
    
    # Action buttons
    btn_start = InlineKeyboardButton(text="ðŸš€ ابدأ الت…رŠن الآ† ðŸš€", callback_data="settings_start")
    btn_back = InlineKeyboardButton(text="â†©ï¸ عˆدة لخŠارات التحدŠد", callback_data="settings_back")
    btn_sep = InlineKeyboardButton(text="ðŸŸ¢ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ ðŸŸ¢", callback_data="q_ignored")
    
    rows = [
        row_timer,
        row_correction,
        row_limit,
        row_source,
        [btn_sep],
        [btn_start],
        [btn_sep],
        [btn_back]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_answer_keyboard(choices: dict, force_letters: bool = False, is_fav: bool = False, question_id: int = None, question_text: str = None, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Create a keyboard with options. If force_letters is True, displays Arabic letters.
    Includes an inline favorite toggle button and exit button."""
    active_choices = {k: v for k, v in choices.items() if v and v.strip()}
    keys = list(active_choices.keys())
    
    ARABIC_CHOICES = {"a": "أ", "b": "ب", "c": "ج", "d": "د"}
    
    rows = []
    
    # 1. Question button if provided
    if question_text:
        q_btn_text = question_text.strip()
        if len(q_btn_text) > 100:
            q_btn_text = q_btn_text[:97] + "..."
        rows.append([InlineKeyboardButton(text=q_btn_text, callback_data="q_ignored")])
        # 2. Divider button
        rows.append([InlineKeyboardButton(text="ðŸŸ¢ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ ðŸŸ¢", callback_data="q_ignored")])
        
    # Determine layout mode based on text length
    max_len = max([len(v.strip()) for v in active_choices.values()]) if active_choices else 0
    use_grid = force_letters or (max_len <= 35)

    row = []
    for k in keys:
        if force_letters:
            btn_text = ARABIC_CHOICES.get(k.lower(), k.upper())
        else:
            btn_text = active_choices[k].strip()
            
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"ans:{k}"))
        
        if use_grid:
            if len(row) == 2:
                rows.append(row[::-1])  # Invert for RTL: B, A and D, C
                row = []
        else:
            rows.append([row[0]])
            row = []
            
    if row:
        if use_grid:
            rows.append(row[::-1])
        else:
            rows.append(row)
        
    bottom_row = []
    if question_id is not None:
        fav_text = "⭐ أز„ من المفض„ة" if is_fav else "⭐ أضف للمفض„ة"
        fav_cb = f"fav_q_rem:{question_id}" if is_fav else f"fav_q_add:{question_id}"
        bottom_row.append(InlineKeyboardButton(text=fav_text, callback_data=fav_cb))
        
    bottom_row.append(InlineKeyboardButton(text="ðŸšª إ†هاء الاختبار", callback_data="quiz_exit"))
    rows.append(bottom_row)
    
    if is_admin and question_id is not None:
        rows.append([
            InlineKeyboardButton(text="⚙️  [إدارة] تعدŠل السؤال", callback_data=f"admin_direct_edit:{question_id}:quiz")
        ])
        
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_feedback_keyboard(question_id: int, is_fav: bool, is_last: bool = False, has_explanation: bool = False, has_prev: bool = False, is_admin: bool = False, has_mind_map: bool = False) -> InlineKeyboardMarkup:
    """Create a keyboard showing immediately after answering a question in Normal Mode."""
    fav_text = "⭐ أز„ من المفض„ة" if is_fav else "⭐ أضف للمفض„ة"
    fav_cb = f"fav_rem:{question_id}" if is_fav else f"fav_add:{question_id}"
    
    next_btn_text = "ðŸ إ†هاء ورؤŠة النتŠجة" if is_last else "âž¡ï¸ السؤال التالي"
    next_cb = "quiz_finish" if is_last else "quiz_next"
    
    rows = []
    
    nav_row = []
    if has_prev:
        nav_row.append(InlineKeyboardButton(text="â¬…️ السؤال الساب‚", callback_data="quiz_prev"))
    nav_row.append(InlineKeyboardButton(text=next_btn_text, callback_data=next_cb))
    rows.append(nav_row)
    
    # 2. Show professor quote button / mind map button
    feedback_row = []
    if has_explanation:
        feedback_row.append(InlineKeyboardButton(text="📖  كلا… الشŠخ وتˆجŠهه", callback_data=f"prof_quote:{question_id}"))
    if has_mind_map:
        feedback_row.append(InlineKeyboardButton(text="ðŸ—ºï¸ الخرŠطة الذ‡نية للدرس", callback_data=f"student_show_map_q:{question_id}"))
    if feedback_row:
        rows.append(feedback_row)
        
    # 3. Favorite and Report Error on a single row below
    rows.append([
        InlineKeyboardButton(text=fav_text, callback_data=fav_cb),
        InlineKeyboardButton(text="âš ï¸ إب„اغ ع† خطأ", callback_data=f"rep_q:{question_id}:quiz")
    ])
    
    if is_admin:
        rows.append([
            InlineKeyboardButton(text="⚙️  [إدارة] تعدŠل السؤال", callback_data=f"admin_direct_edit:{question_id}:quiz")
        ])
        
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_sprint_next_keyboard(is_last: bool = False) -> InlineKeyboardMarkup:
    """Create keyboard for Sprint mode to advance when time has run out or similar."""
    next_btn_text = "ðŸ إ†هاء ورؤŠة النتŠجة" if is_last else "âž¡ï¸ السؤال التالي"
    next_cb = "quiz_finish" if is_last else "quiz_next"
    
    rows = [
        [InlineKeyboardButton(text=next_btn_text, callback_data=next_cb)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_support_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard active during Technical Support ticket drafting."""
    kb = [
        [KeyboardButton(text="âŒ إ†هاء الدع…")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_favorites_nav_keyboard(question_id: int, has_prev: bool, has_next: bool, total_count: int) -> InlineKeyboardMarkup:
    """Navigation keyboard for browsing favorite questions (RTL inverted)."""
    nav_row = []
    # RTL order: Next on the left, Prev on the right
    if has_next:
        nav_row.append(InlineKeyboardButton(text="التالي âž¡ï¸", callback_data="fav_next"))
    
    nav_row.append(InlineKeyboardButton(text="⭐ إزالة", callback_data=f"fav_del_browse:{question_id}"))
    
    if has_prev:
        nav_row.append(InlineKeyboardButton(text="â¬…️ الساب‚", callback_data="fav_prev"))
        
    rows = []
    if nav_row:
        rows.append(nav_row)
        
    rows.append([InlineKeyboardButton(text="ðŸšª العودة للقائمة", callback_data="fav_close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_errors_nav_keyboard(question_id: int, choices: dict, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    """Interactive answering + navigation keyboard for reviewing incorrect questions."""
    active_choices = {k: v for k, v in choices.items() if v and v.strip()}
    keys = list(active_choices.keys())
    
    ARABIC_CHOICES = {"a": "أ", "b": "ب", "c": "ج", "d": "د"}
    
    # 1. Answer buttons row(s) (RTL inverted)
    rows = []
    row = []
    for k in keys:
        ar_char = ARABIC_CHOICES.get(k.lower(), k.upper())
        row.append(InlineKeyboardButton(text=ar_char, callback_data=f"err_ans:{question_id}:{k}"))
        if len(row) == 2:
            rows.append(row[::-1])
            row = []
    if row:
        rows.append(row[::-1])
        
    # 2. Navigation row (RTL inverted)
    nav_row = []
    if has_next:
        nav_row.append(InlineKeyboardButton(text="التالي âž¡ï¸", callback_data="err_next"))
    if has_prev:
        nav_row.append(InlineKeyboardButton(text="â¬…️ الساب‚", callback_data="err_prev"))
        
    if nav_row:
        rows.append(nav_row)
        
    # 3. Close button
    rows.append([InlineKeyboardButton(text="ðŸšª العودة للقائمة", callback_data="err_close")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

# --- NEW KEYBOARDS FOR FEEDBACK, BROWSING, & ADMIN ---

def get_support_menu_keyboard(unread_count: int = 0) -> InlineKeyboardMarkup:
    """Keyboard for support portal menu with unified categories and inbox."""
    hidden_buttons = get_hidden_items_sync("buttons")
    inbox_label = "📬 صندوق الرسائل"
    if unread_count > 0:
        inbox_label += f" ({unread_count} 🔴 )"
        
    rows = [
        [
            InlineKeyboardButton(text="ðŸ› ï¸ خ„ل ت‚ني فŠ البˆت", callback_data="support_tech"),
            InlineKeyboardButton(text="🎓  استفسار أƒادŠمي / إداري", callback_data="support_schooling")
        ],
        [
            InlineKeyboardButton(text="â“ سؤال فŠ المقرر", callback_data="support_course_question"),
            InlineKeyboardButton(text="âœï¸ ا‚تراح سؤال للمقرر", callback_data="support_propose_question")
        ],
        [
            InlineKeyboardButton(text="âš ï¸ خطأ فŠ المحتˆÙ‰", callback_data="support_content_error"),
            InlineKeyboardButton(text="ðŸ’¡ ا‚تراح أˆ غŠر ذ„ك", callback_data="support_suggest")
        ]
    ]
    if "inbox" not in hidden_buttons:
        rows.append([InlineKeyboardButton(text=inbox_label, callback_data="student_inbox")])
        
    rows.append([InlineKeyboardButton(text="📖  د„يل الاستخدا… السرŠع", callback_data="support_guide")])
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للقائمة الرئŠسŠة", callback_data="support_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_student_report_menu_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for reporting choices submenu."""
    rows = [
        [InlineKeyboardButton(text="ðŸ› ï¸ مشƒلة ت‚نية", callback_data="support_tech")],
        [InlineKeyboardButton(text="ðŸ“š خطأ فŠ سؤال", callback_data="support_report_question")],
        [InlineKeyboardButton(text="â†©ï¸ عˆدة", callback_data="support_guide_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_student_contribute_menu_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for development contribution choices submenu."""
    rows = [
        [InlineKeyboardButton(text="ðŸš€ ا‚تراح تحسŠن", callback_data="support_suggest")],
        [InlineKeyboardButton(text="⭐ ت‚ييم / رأي", callback_data="support_review")],
        [InlineKeyboardButton(text="â†©ï¸ عˆدة", callback_data="support_guide_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_browser_type_keyboard() -> InlineKeyboardMarkup:
    """Choose how to find the question to report."""
    rows = [
        [
            InlineKeyboardButton(text="📖  تصفح حسب الدرˆس", callback_data="brtype:lessons"),
            InlineKeyboardButton(text="ðŸ—‚️ تصفح حسب المواد", callback_data="brtype:subjects")
        ],
        [InlineKeyboardButton(text="âŒ إ„غاء", callback_data="qb_close")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_browser_lesson_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard with simple lesson selection buttons (no checkboxes)."""
    lessons = list(range(14, 25))
    rows = []
    for i in range(0, len(lessons), 3):
        row = []
        for l in lessons[i:i+3]:
            row.append(InlineKeyboardButton(text=f"الدرس {l}", callback_data=f"br_les:{l}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة", callback_data="support_report_question")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_browser_subject_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard with simple subject selection buttons (no checkboxes)."""
    hidden_subjects = get_hidden_items_sync("subjects")
    rows = []
    row = []
    for sub, label in SUBJECT_LABELS.items():
        if sub in hidden_subjects:
            continue
        row.append(InlineKeyboardButton(text=label, callback_data=f"br_sub:{sub}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة", callback_data="support_report_question")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_question_browser_nav_keyboard(question_id: int, has_prev: bool, has_next: bool, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Navigation keyboard for the support question browser."""
    nav_row = []
    if has_prev:
        nav_row.append(InlineKeyboardButton(text="â¬…️ الساب‚", callback_data="qb_prev"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text="التالي âž¡ï¸", callback_data="qb_next"))
        
    rows = []
    if nav_row:
        rows.append(nav_row)
        
    # Actions
    rows.append([InlineKeyboardButton(text="âš ï¸ إب„اغ ع† خطأ", callback_data=f"rep_q:{question_id}:browse")])
    if is_admin:
        rows.append([
            InlineKeyboardButton(text="⚙️  [إدارة] تعدŠل السؤال", callback_data=f"admin_direct_edit:{question_id}:browse")
        ])
    rows.append([InlineKeyboardButton(text="ðŸšª إ†هاء التصفح", callback_data="qb_close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_report_error_options_keyboard(question_id: int, source: str = "quiz") -> InlineKeyboardMarkup:
    """
    Inline keyboard to select the error type.
    'source' indicates where the user reported from: 'quiz' or 'browse'.
    """
    rows = [
        [InlineKeyboardButton(text="âŒ خطأ فŠ الإجابة الصحŠحة", callback_data=f"rep_err:{question_id}:ans:{source}")],
        [InlineKeyboardButton(text="âœï¸ خطأ فŠ نص السؤال", callback_data=f"rep_err:{question_id}:text:{source}")],
        [InlineKeyboardButton(text="ðŸ”€ خطأ فŠ أحد الخŠارات", callback_data=f"rep_err:{question_id}:choices:{source}")],
        [InlineKeyboardButton(text="ðŸ’¬ سبب آخر / مشƒلة أخر‰", callback_data=f"rep_err:{question_id}:other:{source}")],
        [InlineKeyboardButton(text="â†©ï¸ إ„غاء", callback_data=f"rep_cancel:{question_id}:{source}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_webapp_base_url() -> str:
    """Get the base URL for the web app. Supports all Railway URL env variables."""
    url = os.getenv("WEBAPP_URL")
    if url and url.strip():
        return url.strip().rstrip('/')
    
    # Support all Railway URL env variable names (old and new)
    for env_key in ["RAILWAY_PUBLIC_DOMAIN", "RAILWAY_SERVICE_URL", "RAILWAY_STATIC_URL"]:
        railway_url = os.getenv(env_key)
        if railway_url and railway_url.strip():
            r_url = railway_url.strip().rstrip('/')
            if not r_url.startswith("http"):
                return f"https://{r_url}"
            return r_url
        
    # Hardcoded Railway production URL as final fallback
    return "https://web-production-64c9ab.up.railway.app"

def get_admin_panel_keyboard(pending_reports: int = 0, pending_proposals: int = 0, show_settings: bool = False, role: str = None) -> InlineKeyboardMarkup:
    """Keyboard for the Admin Panel with inbox first, stats, settings, and student mode switcher."""
    base_url = get_webapp_base_url()
    
    # In production/Railway serveo, if ADMIN_WEBAPP_URL is not set explicitly, we construct it dynamically
    admin_webapp = os.getenv("ADMIN_WEBAPP_URL")
    if not admin_webapp or not admin_webapp.strip():
        admin_webapp = f"{base_url}/admin"
        
    editor_webapp = os.getenv("EDITOR_WEBAPP_URL")
    if not editor_webapp or not editor_webapp.strip():
        editor_webapp = f"{base_url}/editor"

    # If the user is specifically a content editor/transcriptionist (improvement_admin),
    # they should only see the editor webapp button and student mode switcher
    if role == "improvement_admin":
        rows = []
        if editor_webapp.startswith("https"):
            btn_editor = InlineKeyboardButton(text="ðŸ“ لوحة تحرŠر الدرˆس Editor 📱 ", web_app=WebAppInfo(url=editor_webapp))
            rows.append([btn_editor])
        rows.append([InlineKeyboardButton(text="🎓  وضع الطالب", callback_data="admin_switch_student")])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    inbox_text = "ðŸ“¬ برŠد الإدارة"
    if pending_reports > 0:
        inbox_text += f" ({pending_reports} 🔴 )"
        
    prop_text = "ðŸ“¥ مقترحات الأسئ„ة"
    if pending_proposals > 0:
        prop_text += f" ({pending_proposals} 🔴 )"
        
    rows = []
    
    # WebApp buttons
    web_app_buttons = []
    if admin_webapp.startswith("https"):
        web_app_buttons.append(InlineKeyboardButton(text="ðŸ–¥ï¸ لوحة التحƒم Admin 📱 ", web_app=WebAppInfo(url=admin_webapp)))
    if editor_webapp.startswith("https"):
        web_app_buttons.append(InlineKeyboardButton(text="ðŸ“ لوحة المحرر Editor 📱 ", web_app=WebAppInfo(url=editor_webapp)))
        
    if True: # Always show Mini App button
        web_app_buttons.append(InlineKeyboardButton(text="ðŸ–¥ï¸ المنصة التع„يمية واللÙ‘يسˆز 📱 ", web_app=WebAppInfo(url=f"{base_url}/reader.html?v=dash2")))
        
    for btn in web_app_buttons:
        rows.append([btn])
        

        
    rows.extend([
        [InlineKeyboardButton(text=inbox_text, callback_data="admin_reports_center")],
        [
            InlineKeyboardButton(text="âž• إضافة سؤال", callback_data="admin_add_question"),
            InlineKeyboardButton(text="ðŸ” بحث وعرض سؤال", callback_data="admin_search_question")
        ],
        [
            InlineKeyboardButton(text="ðŸ‘¥ إدارة الط„اب", callback_data="admin_manage_students"),
            InlineKeyboardButton(text=prop_text, callback_data="admin_view_proposals")
        ],
        [
            InlineKeyboardButton(text="📊  عرض الإحصائŠات", callback_data="admin_stats"),
            InlineKeyboardButton(text="ðŸ“¢ إرسال إع„ا† (Broadcast)", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="⚙️  مص†ع الأسئ„ة (IA)", callback_data="admin_q_factory_menu"),
            InlineKeyboardButton(text="ðŸ“‚ ملفات المراجعة", callback_data="admin_manage_resources")
        ],
        [
            InlineKeyboardButton(text="ðŸ§ª اختبار الأسئ„ة (Test IA)", callback_data="admin_test_ai_questions"),
            InlineKeyboardButton(text="📖  مسارات القراءة (Study Path)", callback_data="admin_study_path_mgmt")
        ]
    ])
    if show_settings:
        rows.append([InlineKeyboardButton(text="⚙️  إعدادات النظا…", callback_data="admin_settings_menu")])
        
    rows.append([InlineKeyboardButton(text="🎓  وضع الطالب", callback_data="admin_switch_student")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_admin_settings_keyboard(restrict_active: bool = True, show_admin_mgmt: bool = False, display_pref: str = "grid") -> InlineKeyboardMarkup:
    """Settings submenu keyboard containing the 6 specialized direction buttons."""
    rows = [
        [InlineKeyboardButton(text="ðŸ‘¥ إدارة المشرفŠن (Direction des Admins)", callback_data="admin_manage_list")],
        [InlineKeyboardButton(text="ðŸ”˜ أزرار الط„اب (Direction des Boutons)", callback_data="admin_dir_buttons")],
        [InlineKeyboardButton(text="ðŸ“š المواد والدرˆس (Direction des Leçons)", callback_data="admin_dir_subjects_lessons")],
        [InlineKeyboardButton(text="📊  إدارة البŠا†ات (Direction des Données)", callback_data="admin_dir_data")],
        [InlineKeyboardButton(text="ðŸ‘ï¸ إعدادات العرض (Direction de l'Affichage)", callback_data="admin_dir_display")],
        [InlineKeyboardButton(text="ðŸ”’ إعدادات الأ…ا† (Direction de la Sécurité)", callback_data="admin_dir_security")],
        [InlineKeyboardButton(text="â†©ï¸ العودة للوحة الإدارة", callback_data="admin_back_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_dir_buttons_keyboard(hidden_buttons: list) -> InlineKeyboardMarkup:
    buttons_map = {
        "revision": "?? ????? ????????",
        "favorites": "⭐ المفضلة",
        "errors": "âŒ أخطائŠ",
        "progress": "📊  ت‚د‘مي",
        "inbox": "📬 صندوق الرسائل",
        "support": "💬 الدعم والمساعدة",
        "settings": "?? ?????????",
        "mini_app": "?? Mini App"
    }
    rows = []
    for btn_id, label in buttons_map.items():
        is_hidden = btn_id in hidden_buttons
        status_icon = "ðŸš« مخفŠ" if is_hidden else "ðŸ‘ï¸ مرئي"
        rows.append([
            InlineKeyboardButton(text=f"{label} | {status_icon}", callback_data=f"tog_btn:{btn_id}")
        ])
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للإعدادات", callback_data="admin_settings_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_dir_subjects_keyboard(hidden_subjects: list) -> InlineKeyboardMarkup:
    rows = []
    for sub_id, label in SUBJECT_LABELS.items():
        is_hidden = sub_id in hidden_subjects
        status_icon = "ðŸš« مخفŠ" if is_hidden else "ðŸ‘ï¸ مرئي"
        rows.append([
            InlineKeyboardButton(text=f"{label} | {status_icon}", callback_data=f"tog_sub:{sub_id}")
        ])
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للمواد والدرˆس", callback_data="admin_dir_subjects_lessons")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_dir_subjects_lessons_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="ðŸ“‚ إظ‡ار/إخفاء المواد", callback_data="admin_dir_subjects")],
        [InlineKeyboardButton(text="📖  إظ‡ار/إخفاء الدرˆس", callback_data="admin_dir_lessons_select")],
        [InlineKeyboardButton(text="🎯  إظ‡ار/إخفاء المحاˆر", callback_data="admin_dir_themes_select")],
        [InlineKeyboardButton(text="â†©ï¸ العودة للإعدادات", callback_data="admin_settings_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_dir_lessons_subjects_keyboard(mode: str) -> InlineKeyboardMarkup:
    rows = []
    for sub_id, label in SUBJECT_LABELS.items():
        rows.append([
            InlineKeyboardButton(text=label, callback_data=f"dir_sel_sub:{mode}:{sub_id}")
        ])
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للمواد والدرˆس", callback_data="admin_dir_subjects_lessons")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_dir_lessons_keyboard(subject: str, hidden_lessons: list) -> InlineKeyboardMarkup:
    rows = []
    row = []
    # In backup bot, lessons are 14 to 24
    for l in range(14, 25):
        is_hidden = str(l) in hidden_lessons or l in hidden_lessons
        status_icon = "ðŸš«" if is_hidden else "ðŸ‘ï¸"
        row.append(InlineKeyboardButton(
            text=f"{status_icon} الدرس {l}",
            callback_data=f"tog_dir_les:{subject}:{l}"
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="â†©ï¸ تغŠير المادة", callback_data="admin_dir_lessons_select")])
    rows.append([InlineKeyboardButton(text="ðŸ  العودة للمواد والدرˆس", callback_data="admin_dir_subjects_lessons")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_dir_themes_keyboard(subject: str, hidden_themes: list) -> InlineKeyboardMarkup:
    rows = []
    subject_themes = THEMES.get(subject, {})
    for th_key, th_info in subject_themes.items():
        is_hidden = th_key in hidden_themes
        status_icon = "ðŸš«" if is_hidden else "ðŸ‘ï¸"
        rows.append([
            InlineKeyboardButton(
                text=f"{status_icon} {th_info['label']}",
                callback_data=f"tog_dir_th:{subject}:{th_key}"
            )
        ])
    rows.append([InlineKeyboardButton(text="â†©ï¸ تغŠير المادة", callback_data="admin_dir_themes_select")])
    rows.append([InlineKeyboardButton(text="ðŸ  العودة للمواد والدرˆس", callback_data="admin_dir_subjects_lessons")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_dir_data_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="ðŸ”„ مزا…نة الأسئ„ة (Google Sheets)", callback_data="admin_sync_questions")],
        [InlineKeyboardButton(text="ðŸ“¥ تصدŠر الأسئ„ة (CSV)", callback_data="admin_data_export_csv")],
        [InlineKeyboardButton(text="ðŸ“¦ نسخة احتŠاطŠة (SQLite DB)", callback_data="admin_data_backup_db")],
        [InlineKeyboardButton(text="â†©ï¸ العودة للإعدادات", callback_data="admin_settings_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_dir_display_keyboard(display_pref: str, ticket_detail_level: str = "compact", show_ticket_level: bool = False) -> InlineKeyboardMarkup:
    display_pref_label = "ðŸ‘ï¸ وضع العرض: جدˆل 📊 " if display_pref == "grid" else "ðŸ‘ï¸ وضع العرض: قائ…ة ðŸ“‚"
    
    rows = [
        [InlineKeyboardButton(text=display_pref_label, callback_data="admin_toggle_pref_display")]
    ]
    
    if show_ticket_level:
        if ticket_detail_level == "compact":
            level_label = "ðŸŽ« تفاصŠل الب„اغات: معاŠنة خفŠفة ðŸ‘ï¸"
        else:
            level_label = "ðŸŽ« تفاصŠل الب„اغات: مخفŠ بالكا…ل ðŸ”’"
        rows.append([InlineKeyboardButton(text=level_label, callback_data="admin_toggle_ticket_level")])
        
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للإعدادات", callback_data="admin_settings_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_dir_security_keyboard(restrict_active: bool, ai_disabled: bool = False) -> InlineKeyboardMarkup:
    toggle_text = "ðŸ”’ ت‚ييد الدخˆل للط„اب" if restrict_active else "ðŸ”“ الس…اح بدخˆل الج…يع"
    toggle_ai_text = "âœ¨ تفعŠل الأسئ„ة الإضافŠة للط„اب" if ai_disabled else "ðŸš« تعطŠل الأسئ„ة الإضافŠة للط„اب"
    rows = [
        [InlineKeyboardButton(text=toggle_text, callback_data="admin_toggle_restrict")],
        [InlineKeyboardButton(text=toggle_ai_text, callback_data="admin_toggle_ai_questions")],
        [InlineKeyboardButton(text="â†©ï¸ العودة للإعدادات", callback_data="admin_settings_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)




def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to confirm sending a broadcast message."""
    rows = [
        [
            InlineKeyboardButton(text="âœ… تأƒيد الإرسال", callback_data="admin_broad_confirm"),
            InlineKeyboardButton(text="âŒ إ„غاء", callback_data="admin_broad_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_quiz_results_keyboard(wrong_count: int, targeted_subject: str = None, targeted_course: int = None, targeted_errors: int = 0) -> InlineKeyboardMarkup:
    """Create keyboard at the end of a quiz, showing retry errors or new quiz button.
    
    Optionally injects a targeted drill button if the student made >= 2 errors in one specific course.
    """
    SUBJECT_LABELS_LOCAL = {
        "fiqh": "الف‚ه",
        "sira": "السŠرة النبˆية",
        "nahw": "النحˆ",
        "aqeeda": "الع‚يدة"
    }
    rows = []
    
    # Targeted course drill button (highest priority if eligible)
    if targeted_subject and targeted_course and targeted_errors >= 2:
        subj_ar = SUBJECT_LABELS_LOCAL.get(targeted_subject, targeted_subject)
        rows.append([
            InlineKeyboardButton(
                text=f"🎯  مراجعة {subj_ar} - الدرس {targeted_course} ({targeted_errors} أخطاء)",
                callback_data=f"err_drill:{targeted_subject}:{targeted_course}"
            )
        ])
    
    if wrong_count > 0:
        rows.append([InlineKeyboardButton(text=f"ðŸ”„ إعادة محاˆلة الأخطاء ({wrong_count})", callback_data="quiz_retry_errors")])
    else:
        rows.append([InlineKeyboardButton(text="ðŸ“ اختبار جدŠد", callback_data="quiz_new_direct")])
    rows.append([InlineKeyboardButton(text="ðŸšª العودة للقائمة", callback_data="quiz_exit_results")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_progress_browser_keyboard(current_idx: int, total_count: int) -> InlineKeyboardMarkup:
    """Create navigation keyboard for browsing subject progress."""
    nav_row = []
    # RTL logic: Previous on the left, Next on the right
    if current_idx > 0:
        nav_row.append(InlineKeyboardButton(text="â—€️ المادة الساب‚ة", callback_data=f"prog_browse:{current_idx - 1}"))
    if current_idx < total_count - 1:
        nav_row.append(InlineKeyboardButton(text="المادة التالية â–¶ï¸", callback_data=f"prog_browse:{current_idx + 1}"))
        
    rows = []
    if nav_row:
        rows.append(nav_row)
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للقائمة الرئŠسŠة", callback_data="prog_close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_report_comment_keyboard(question_id: int, error_type: str, source: str) -> InlineKeyboardMarkup:
    """Keyboard offering quick submit without comment and cancel buttons during report comment drafting."""
    rows = [
        [InlineKeyboardButton(text="ðŸ“¤ إرسال الب„اغ بدˆن تع„يق", callback_data=f"rep_send_no_comment:{question_id}:{error_type}:{source}")],
        [InlineKeyboardButton(text="âŒ إ„غاء", callback_data=f"rep_cancel:{question_id}:{source}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_ticket_keyboard(report_id: int) -> InlineKeyboardMarkup:
    """Interactive action buttons sent along with the support ticket in the admin group."""
    rows = [
        [InlineKeyboardButton(text="âœï¸ تعدŠل السؤال", callback_data=f"admin_rep_edit:{report_id}")],
        [
            InlineKeyboardButton(text="âœ… ت… تصحŠح الخطأ", callback_data=f"admin_rep_resolve:{report_id}"),
            InlineKeyboardButton(text="âŒ رفض الب„اغ", callback_data=f"admin_rep_reject:{report_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# --- NEW SUPPORT & INBOX KEYBOARDS ---

def get_student_inbox_keyboard(reports: list[dict], page: int = 1, show_archive: bool = False, layout: str = "chat") -> InlineKeyboardMarkup:
    """List student reports in their inbox with pagination, using a table (grid) layout."""
    rows = []
    status_icons = {
        "pending": "⏳",
        "in_progress": "ðŸŸ¡",
        "resolved": "ðŸŸ¢",
        "rejected": "âŒ"
    }
    type_labels = {
        "tech": "ت‚ني",
        "suggestion": "ا‚تراح",
        "improvement": "ا‚تراح",
        "review": "ت‚ييم",
        "question_error": "خطأ سؤال",
        "content": "خطأ سؤال",
        "expl_error": "خطأ شرح",
        "course_question": "سؤال",
        "content_error": "خطأ محتˆÙ‰",
        "أخر‰ / سبب آخر": "أخر‰",
        "خطأ فŠ الإجابة الصحŠحة": "إجابة",
        "خطأ فŠ نص السؤال": "نص",
        "خطأ فŠ أحد الخŠارات": "خŠارات",
        "سبب آخر / مشƒلة أخر‰": "أخر‰"
    }
    
    # Filter and sort reports: unread first, then pending/in_progress
    if show_archive:
        filtered_reports = [r for r in reports if r.get("status") in ("resolved", "rejected") and r.get("student_read", 1) == 1]
    else:
        unread_reports = [r for r in reports if r.get("student_read", 1) == 0]
        pending_reports = [r for r in reports if r.get("status") in ("pending", "in_progress") and r.get("student_read", 1) != 0]
        filtered_reports = unread_reports + pending_reports
        
    items_per_page = 6
    total_pages = (len(filtered_reports) + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    # Grid Layout Header
    if filtered_reports:
        rows.append([
            InlineKeyboardButton(text="الحالة ðŸ””", callback_data="noop"),
            InlineKeyboardButton(text="الموضˆع ðŸ“‚", callback_data="noop"),
            InlineKeyboardButton(text="الر‚م ðŸ†”", callback_data="noop")
        ])
    
    for r in filtered_reports[start_idx:end_idx]:
        status_val = r.get("status")
        is_unread = r.get("student_read", 1) == 0
        raw_type = r.get("report_type")
        type_str = type_labels.get(raw_type, raw_type if raw_type else "ب„اغ")
        
        ret_page_str = f"archive:{page}" if show_archive else f"active:{page}"
        cb_data = f"st_rep_view:{r['id']}:{ret_page_str}"
        
        if is_unread:
            status_btn_text = "ðŸ”” رد جدŠد"
        elif status_val == "in_progress":
            status_btn_text = "ðŸŸ¡ قيد المعالجة"
        elif status_val == "pending":
            status_btn_text = "⏳ فŠ الا†تظار"
        elif status_val == "resolved":
            status_btn_text = "ðŸŸ¢ ت… الح„"
        elif status_val == "rejected":
            status_btn_text = "âŒ مرفˆض"
        else:
            status_btn_text = status_icons.get(status_val, "⏳")
            
        rows.append([
            InlineKeyboardButton(text=status_btn_text, callback_data=cb_data),
            InlineKeyboardButton(text=type_str, callback_data=cb_data),
            InlineKeyboardButton(text=f"#{r['id']}", callback_data=cb_data)
        ])
        
    if total_pages > 1:
        nav_row = []
        prefix = "student_inbox:archive" if show_archive else "student_inbox:active"
        if page > 1:
            nav_row.append(InlineKeyboardButton(text="â¬…️ الساب‚", callback_data=f"{prefix}:{page-1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton(text="التالي âž¡ï¸", callback_data=f"{prefix}:{page+1}"))
        rows.append(nav_row)
        
    # Toggle between active/archive
    active_count = len([r for r in reports if r.get("status") in ("pending", "in_progress") or r.get("student_read", 0) == 0])
    archive_count = len([r for r in reports if r.get("status") in ("resolved", "rejected") and r.get("student_read", 1) == 1])
    
    if show_archive:
        rows.append([InlineKeyboardButton(text=f"â†©ï¸ العودة للرسائ„ النشطة ({active_count})", callback_data="student_inbox:active:1")])
    else:
        if archive_count > 0:
            rows.append([InlineKeyboardButton(text=f"ðŸ“ أرشŠف الرسائ„ المغ„قة ({archive_count})", callback_data="student_inbox:archive:1")])
            
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة للدع…", callback_data="support_guide_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_student_report_detail_keyboard(report_id: int, can_reply: bool = True, return_page = 1) -> InlineKeyboardMarkup:
    """Keyboard for viewing a single report detail with optional reply button."""
    rows = []
    if can_reply:
        rows.append([InlineKeyboardButton(text="ðŸ’¬ إضافة رد / تع„يق", callback_data=f"student_rep_reply:{report_id}")])
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة للص†دˆق", callback_data=f"student_inbox:{return_page}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_admin_reports_center_keyboard(pending_count: int, in_progress_count: int, resolved_count: int) -> InlineKeyboardMarkup:
    """Keyboard for admin reports dashboard selection with tri-status."""
    rows = [
        [InlineKeyboardButton(text=f"⏳ غŠر معالجة ({pending_count})", callback_data="admin_db_rep_filter:pending")],
        [InlineKeyboardButton(text=f"ðŸŸ¡ قيد المعالجة ({in_progress_count})", callback_data="admin_db_rep_filter:in_progress")],
        [InlineKeyboardButton(text=f"âœ… ت…ت المعالجة ({resolved_count})", callback_data="admin_db_rep_filter:resolved")],
        [InlineKeyboardButton(text="â†©ï¸ العودة للوحة الإدارة", callback_data="admin_close")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_matrix_dashboard_keyboard(matrix_counts: dict, role: str) -> InlineKeyboardMarkup:
    """
    Constructs the Category x Status matrix keyboard for the admin dashboard.
    Dynamically filters rows based on the administrator's role.
    """
    is_super = role in ("super_admin", "backup_admin")
    is_support = role == "support_admin"
    is_mod = role == "moderator"
    is_improvement = role == "improvement_admin"
    
    rows = []
    
    # Header Row (RTL)
    rows.append([
        InlineKeyboardButton(text="âœ… معالج", callback_data="noop"),
        InlineKeyboardButton(text="⏳ قيد المراجعة", callback_data="noop"),
        InlineKeyboardButton(text="🔴  غŠر معالج", callback_data="noop"),
        InlineKeyboardButton(text="ðŸ“ القس…", callback_data="noop")
    ])
    
    # List of categories with their label, internal code, and role check
    all_cats = [
        ("tech", "ðŸš¨ مشاƒل ت‚نية", is_super or is_support),
        ("question_error", "ðŸ“š خطأ سؤال", is_super or is_mod),
        ("expl_error", "âš ï¸ خطأ شرح", is_super or is_mod),
        ("course_question", "â“ سؤال مقرر", is_super or is_mod),
        ("suggestion", "ðŸ’¡ ا‚تراح/رأي", is_super or is_improvement)
    ]
    
    for cat_code, label, has_access in all_cats:
        if not has_access:
            continue
            
        cat_counts = matrix_counts.get(cat_code, {"pending": 0, "in_progress": 0, "resolved": 0})
        p = cat_counts.get("pending", 0)
        ip = cat_counts.get("in_progress", 0)
        r = cat_counts.get("resolved", 0)
        
        # Row in RTL: [Resolved, In Progress, Pending, Category Label]
        rows.append([
            InlineKeyboardButton(text=f"âœ… ({r})" if r > 0 else "-", callback_data=f"admin_matrix_list:{cat_code}:resolved:1" if r > 0 else "noop"),
            InlineKeyboardButton(text=f"⏳ ({ip})" if ip > 0 else "-", callback_data=f"admin_matrix_list:{cat_code}:in_progress:1" if ip > 0 else "noop"),
            InlineKeyboardButton(text=f"🔴  ({p})" if p > 0 else "-", callback_data=f"admin_matrix_list:{cat_code}:pending:1" if p > 0 else "noop"),
            InlineKeyboardButton(text=label, callback_data="noop")
        ])
        
    # Return button
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للوحة الإدارة", callback_data="admin_back_panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_reports_list_keyboard(reports: list[dict], current_filter: str, page: int = 1) -> InlineKeyboardMarkup:
    """List of reports in admin review interface in a 3-column grid layout with pagination (RTL)."""
    rows = []
    
    # Header in RTL: [Num/Status, Type, Sender]
    rows.append([
        InlineKeyboardButton(text="ðŸ”¢ الر‚م", callback_data="noop"),
        InlineKeyboardButton(text="ðŸ’¬ النوع", callback_data="noop"),
        InlineKeyboardButton(text="ðŸ‘¤ المرس„", callback_data="noop")
    ])
    
    status_icons = {
        "pending": "🔴 ",
        "in_progress": "⏳",
        "resolved": "âœ…",
        "rejected": "âŒ"
    }
    
    type_labels = {
        "tech": "ðŸ› ï¸ ت‚ني",
        "course_question": "â“ سؤال",
        "content_error": "âš ï¸ محتˆÙ‰",
        "suggestion": "ðŸ’¡ ا‚تراح",
        "expl_error": "âš ï¸ شرح",
        "content": "ðŸ“š محتˆÙ‰"
    }
    
    items_per_page = 10
    total_pages = (len(reports) + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    for r in reports[start_idx:end_idx]:
        status_icon = status_icons.get(r.get("status"), "🔴 ")
        name_str = (r.get("first_name") or "طالب")[:10]
        raw_type = r.get("report_type")
        type_str = type_labels.get(raw_type, "ب„اغ")
        
        cb_data = f"admin_db_rep_view:{r['id']}:{current_filter}:{page}"
        
        # Row in RTL: [Status/Num, Type, Sender]
        rows.append([
            InlineKeyboardButton(text=f"{status_icon} #{r['id']}", callback_data=cb_data),
            InlineKeyboardButton(text=type_str, callback_data=cb_data),
            InlineKeyboardButton(text=name_str, callback_data=cb_data)
        ])
        
    if total_pages > 1:
        nav_row = []
        if page < total_pages:
            nav_row.append(InlineKeyboardButton(text="التالي âž¡ï¸", callback_data=f"admin_db_rep_page:{current_filter}:{page+1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        if page > 1:
            nav_row.append(InlineKeyboardButton(text="â¬…️ الساب‚", callback_data=f"admin_db_rep_page:{current_filter}:{page-1}"))
        rows.append(nav_row)
        
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة لوحة الب„اغات", callback_data="admin_reports_center")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_admin_category_first_keyboard(matrix_counts: dict, role: str) -> InlineKeyboardMarkup:
    """Category-First list keyboard for the admin dashboard."""
    is_super = role in ("super_admin", "backup_admin")
    is_support = role == "support_admin"
    is_mod = role == "moderator"
    is_improvement = role == "improvement_admin"
    
    rows = []
    
    # List of categories with their label, internal code, and role check
    all_cats = [
        ("tech", "ðŸš¨ مشاƒل ت‚نية", is_super or is_support),
        ("question_error", "ðŸ“š خطأ سؤال", is_super or is_mod),
        ("expl_error", "âš ï¸ خطأ شرح", is_super or is_mod),
        ("course_question", "â“ سؤال مقرر", is_super or is_mod),
        ("suggestion", "ðŸ’¡ ا‚تراح/رأي", is_super or is_improvement)
    ]
    
    for cat_code, label, has_access in all_cats:
        if not has_access:
            continue
            
        cat_counts = matrix_counts.get(cat_code, {"pending": 0, "in_progress": 0, "resolved": 0})
        p = cat_counts.get("pending", 0)
        
        btn_label = f"{label} ({p} 🔴 )" if p > 0 else f"{label} (مكت…ل âœ…)"
        rows.append([InlineKeyboardButton(text=btn_label, callback_data=f"admin_reports_cat:{cat_code}")])
        
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للوحة الإدارة", callback_data="admin_back_panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_admin_category_status_keyboard(category: str, cat_counts: dict) -> InlineKeyboardMarkup:
    """Keyboard containing the three status buttons for a selected category."""
    p = cat_counts.get("pending", 0)
    ip = cat_counts.get("in_progress", 0)
    r = cat_counts.get("resolved", 0)
    
    rows = [
        [InlineKeyboardButton(text=f"🔴  غŠر معالج ({p})", callback_data=f"admin_matrix_list:{category}:pending:1" if p > 0 else "noop")],
        [InlineKeyboardButton(text=f"⏳ قيد المراجعة ({ip})", callback_data=f"admin_matrix_list:{category}:in_progress:1" if ip > 0 else "noop")],
        [InlineKeyboardButton(text=f"âœ… معالج ({r})", callback_data=f"admin_matrix_list:{category}:resolved:1" if r > 0 else "noop")],
        [InlineKeyboardButton(text="â†©ï¸ العودة لقائ…ة الأ‚سا…", callback_data="admin_reports_center")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_admin_report_actions_keyboard(report_id: int, has_question: bool, return_page: int = 1, timestamp_url: str = None, timestamp_display: str = None) -> InlineKeyboardMarkup:
    """Action buttons under an admin report detail view."""
    rows = []
    if timestamp_url and timestamp_display:
        rows.append([InlineKeyboardButton(text=f"ðŸŽ¥ تشغŠل الفŠدŠو ع†د {timestamp_display}", url=timestamp_url)])
    rows.append([InlineKeyboardButton(text="ðŸ’¬ الرد ع„Ù‰ الطالب", callback_data=f"admin_db_rep_reply:{report_id}:{return_page}")])
    rows.append([
        InlineKeyboardButton(text="âœ… ت… الح„", callback_data=f"admin_db_rep_resolve:{report_id}:{return_page}"),
        InlineKeyboardButton(text="âŒ رفض الب„اغ", callback_data=f"admin_db_rep_reject:{report_id}:{return_page}")
    ])
    if has_question:
        rows.append([InlineKeyboardButton(text="âœï¸ تعدŠل السؤال المرتبط", callback_data=f"admin_db_rep_edit_q:{report_id}:{return_page}")])
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للقائمة", callback_data=f"admin_db_rep_back_list:{return_page}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_expl_error_options_keyboard(q_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard to select explanation error type."""
    rows = [
        [InlineKeyboardButton(text="⏱️ عد… تطاب‚ النص ود‚يقة الفŠدŠو", callback_data=f"rep_expl_type:{q_id}:mismatch_time")],
        [InlineKeyboardButton(text="🎓  خطأ فŠ الشرح / المحتˆÙ‰ الع„مي", callback_data=f"rep_expl_type:{q_id}:pedagogical")],
        [InlineKeyboardButton(text="âœï¸ خطأ إ…لائŠ أˆ مطبعي", callback_data=f"rep_expl_type:{q_id}:spelling")],
        [InlineKeyboardButton(text="â“ سبب آخر", callback_data=f"rep_expl_type:{q_id}:other")],
        [InlineKeyboardButton(text="â†©ï¸ إ„غاء", callback_data=f"prof_quote:{q_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_expl_report_comment_keyboard(q_id: int, error_type: str) -> InlineKeyboardMarkup:
    """Keyboard offering quick submit without comment and cancel buttons during explanation report comment drafting."""
    rows = [
        [InlineKeyboardButton(text="ðŸ“¤ إرسال الب„اغ بدˆن تع„يق", callback_data=f"rep_expl_send:{q_id}:{error_type}")],
        [InlineKeyboardButton(text="âŒ إ„غاء", callback_data=f"prof_quote:{q_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_admin_group_ticket_keyboard(report_id: int, has_question: bool = False, status: str = 'pending', claimed_by: str = '', timestamp_url: str = None, timestamp_display: str = None, show_details: bool = False) -> InlineKeyboardMarkup:
    """Rich inline keyboard for admin support group tickets with Claim and quick templates."""
    rows = []
    
    if timestamp_url and timestamp_display:
        rows.append([InlineKeyboardButton(text=f"ðŸŽ¥ تشغŠل الفŠدŠو ع†د {timestamp_display}", url=timestamp_url)])
        
    # Detail toggle button row (Option 1 / Collapsible Details)
    if has_question:
        if show_details:
            rows.append([InlineKeyboardButton(text="ðŸ™ˆ إخفاء التفاصŠل", callback_data=f"admin_group_details:{report_id}:hide")])
        else:
            rows.append([InlineKeyboardButton(text="ðŸ” تفاصŠل السؤال", callback_data=f"admin_group_details:{report_id}:show")])

    if status == 'pending':
        # Add ONLY Claim button initially
        rows.append([InlineKeyboardButton(text="ðŸ™‹â€â™‚️ است„ا… الب„اغ (Claim)", callback_data=f"admin_rep_claim:{report_id}")])
    else:
        # Once claimed, show resolution actions
        if has_question:
            # Row 1: Edit question
            rows.append([InlineKeyboardButton(text="âœï¸ تعدŠل السؤال", callback_data=f"admin_rep_edit:{report_id}")])
            # Row 2: Quick Resolve/Reject Templates
            rows.append([
                InlineKeyboardButton(text="âœ”️ السؤال صحŠح", callback_data=f"admin_rep_quick_reject:{report_id}"),
                InlineKeyboardButton(text="âœ… ت… تصحŠح الخطأ", callback_data=f"admin_rep_resolve:{report_id}")
            ])
        else:
            # No question (e.g. tech issue, suggestion)
            rows.append([
                InlineKeyboardButton(text="âœ… ت… الح„", callback_data=f"admin_rep_resolve:{report_id}"),
                InlineKeyboardButton(text="âŒ رفض الب„اغ", callback_data=f"admin_rep_reject:{report_id}")
            ])
        
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_student_notification_keyboard(report_id: int) -> InlineKeyboardMarkup:
    """Create keyboard under student notification query reply."""
    rows = [
        [
            InlineKeyboardButton(text="ðŸ“¬ الذ‡اب لص†دˆق الرسائ„", callback_data=f"st_rep_view:{report_id}:1"),
            InlineKeyboardButton(text="ðŸ’¬ إضافة رد / تع„يق", callback_data=f"student_rep_reply:{report_id}")
        ],
        [InlineKeyboardButton(text="ðŸšª القائ…ة الرئŠسŠة", callback_data="support_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_status_decision_keyboard(report_id: int, return_page: str = "1") -> InlineKeyboardMarkup:
    """Create keyboard for admin to choose ticket status after reply."""
    rows = [
        [
            InlineKeyboardButton(text="âœ… ت… الح„ (Résolu)", callback_data=f"admin_decide:{report_id}:resolved:{return_page}"),
            InlineKeyboardButton(text="âŒ ت… الرفض (Rejeté)", callback_data=f"admin_decide:{report_id}:rejected:{return_page}")
        ],
        [
            InlineKeyboardButton(text="ðŸŸ¡ قيد المعالجة (Laisser en cours)", callback_data=f"admin_decide:{report_id}:in_progress:{return_page}")
        ],
        [InlineKeyboardButton(text="â†©ï¸ إ„غاء", callback_data=f"admin_db_rep_view:{report_id}:{return_page}" if return_page != "group" else "noop")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_management_keyboard(admins: list, page: int = 1) -> InlineKeyboardMarkup:
    """Keyboard listing all admins with pagination and option to add a new admin."""
    limit = 6
    offset = (page - 1) * limit
    page_admins = admins[offset:offset+limit]
    
    rows = []
    for admin in page_admins:
        role_icons = {
            "super_admin": "ðŸ‘‘",
            "backup_admin": "ðŸ›¡ï¸",
            "support_admin": "ðŸ› ï¸",
            "moderator": "âœï¸",
            "improvement_admin": "ðŸš€"
        }
        role_label = role_icons.get(admin["role"], "ðŸ‘¤")
        name_display = admin["first_name"] or admin["username"] or f"ID: {admin['telegram_id']}"
        rows.append([InlineKeyboardButton(
            text=f"{role_label} {name_display}", 
            callback_data=f"adm_view:{admin['telegram_id']}:{page}"
        )])
        
    # Pagination
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="â¬…️ الساب‚", callback_data=f"adm_pg:{page-1}"))
    total_pages = (len(admins) + limit - 1) // limit
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="التالي âž¡ï¸", callback_data=f"adm_pg:{page+1}"))
    if nav_row:
        rows.append(nav_row)
        
    # Actions
    rows.append([InlineKeyboardButton(text="âž• إضافة مشرف جدŠد", callback_data="adm_add")])
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة لقائ…ة الإعدادات", callback_data="admin_settings_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_role_selection_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    """Keyboard to select the role for a new administrator."""
    rows = [
        [InlineKeyboardButton(text="ðŸ‘‘ مدŠر عا… (super_admin)", callback_data=f"adm_role:{telegram_id}:super_admin")],
        [InlineKeyboardButton(text="ðŸ›¡ï¸ مدŠر احتŠاطŠ (backup_admin)", callback_data=f"adm_role:{telegram_id}:backup_admin")],
        [InlineKeyboardButton(text="ðŸ› ï¸ مشرف دع… (support_admin)", callback_data=f"adm_role:{telegram_id}:support_admin")],
        [InlineKeyboardButton(text="âœï¸ مشرف تربوي (moderator)", callback_data=f"adm_role:{telegram_id}:moderator")],
        [InlineKeyboardButton(text="ðŸš€ مشرف تطˆير (improvement_admin)", callback_data=f"adm_role:{telegram_id}:improvement_admin")],
        [InlineKeyboardButton(text="âŒ إ„غاء", callback_data="admin_manage_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_detail_keyboard(telegram_id: int, return_page: int = 1) -> InlineKeyboardMarkup:
    """Keyboard for admin detail card, allowing removal of permissions."""
    rows = [
        [InlineKeyboardButton(text="âŒ إزالة ص„احŠات المشرف", callback_data=f"adm_del:{telegram_id}")],
        [InlineKeyboardButton(text="â†©ï¸ عˆدة للقائمة", callback_data=f"admin_manage_list:{return_page}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_subjects_selection_keyboard(selected_list: list[str], prefix: str) -> InlineKeyboardMarkup:
    """Create a multi-select inline keyboard for choosing subjects.
    prefix is used to distinguish the callbacks (e.g. 'onb_fav', 'onb_diff', 'prof_fav', 'prof_diff')
    """
    SUBJECT_EMOJIS = {
        "fiqh": "ðŸ“š",
        "sira": "ðŸ•Œ",
        "nahw": "âœï¸",
        "aqeeda": "ðŸ’­"
    }
    
    rows = []
    
    # Subject grid (2 per row)
    row = []
    for sub, label in SUBJECT_LABELS.items():
        emoji = SUBJECT_EMOJIS.get(sub, "ðŸ“š")
        is_selected = sub in selected_list
        mark = "âœ…" if is_selected else "âŒ"
        btn_text = f"{mark} {emoji} {label}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"{prefix}:toggle:{sub}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
        
    # Navigation/Action Row
    action_row = [
        InlineKeyboardButton(text="⏭️ تخطي", callback_data=f"{prefix}:skip"),
        InlineKeyboardButton(text="ðŸ’¾ حفظ ومتابعة", callback_data=f"{prefix}:done")
    ]
    rows.append(action_row)
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_student_settings_keyboard(inbox_layout: str, gender: str = None, settings_layout: str = 'classic') -> InlineKeyboardMarkup:
    """Create the student settings keyboard with layout and gender options."""
    rows = []
    
    # Inbox Layout Toggle
    layout_text = "ðŸ“® تخطŠط البرŠد: ðŸ’¬ محادثة (مبسط) ðŸ”„" if inbox_layout == "chat" else "ðŸ“® تخطŠط البرŠد: 📊  جدˆل (3 أع…دة) ðŸ”„"
    rows.append([InlineKeyboardButton(text=layout_text, callback_data=f"set_inbox_layout:{inbox_layout}")])
    
    # Quiz Settings Layout Toggle
    layout_names = {
        'classic': 'كلاسŠكي (ع…ودŠ مع فاص„)',
        'grid': 'شبƒة (أزرار متجاˆرة)',
        'top': 'زر البدء فŠ الأع„Ù‰ (ع…ودŠ)',
        'hybrid': 'مخت„ط (البدء فŠ الأع„Ù‰ + شبƒة)'
    }
    current_layout_name = layout_names.get(settings_layout, 'كلاسŠكي (ع…ودŠ مع فاص„)')
    rows.append([InlineKeyboardButton(
        text=f"⚙️  تخطŠط لوحة الت…رŠن: {current_layout_name} ðŸ”„",
        callback_data=f"set_settings_layout:{settings_layout}"
    )])
    
    # Gender Address Toggle
    gender_label = "👦 أخ (ذƒر)" if gender == "male" else "👧 أخت (أ†ث‰)" if gender == "female" else "ðŸŽ­ حدد الج†س (صŠغة المخاطبة)"
    gender_next = "female" if gender == "male" else "male" if gender == "female" else "male"
    rows.append([InlineKeyboardButton(text=f"ðŸŽ­ صŠغة المخاطبة: {gender_label} ðŸ”„", callback_data=f"set_gender_toggle:{gender_next}")])
    
    # Subject editing buttons
    rows.append([
        InlineKeyboardButton(text="⭐ تعدŠل المواد المفض„ة", callback_data="edit_fav_subjects"),
        InlineKeyboardButton(text="âš ï¸ تعدŠل المواد الصعبة", callback_data="edit_diff_subjects")
    ])
    
    rows.append([
        InlineKeyboardButton(text="🎯  تحدŠد المادة الت„قائŠة (تخطŠ الاختŠار)", callback_data="edit_preferred_subject")
    ])
    
    # Back to main menu
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للقائمة الرئŠسŠة", callback_data="support_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_preferred_subject_keyboard(current_pref: str = None) -> InlineKeyboardMarkup:
    """Create a keyboard to select a single preferred subject that bypasses subject menus."""
    SUBJECT_EMOJIS = {
        "fiqh": "ðŸ“š",
        "sira": "ðŸ•Œ",
        "nahw": "âœï¸",
        "aqeeda": "ðŸ’­",
        "tajweed": "ðŸŽ™️"
    }
    rows = []
    row = []
    
    # Check hidden subjects
    hidden_subjects = get_hidden_items_sync("subjects")
    
    for sub, label in SUBJECT_LABELS.items():
        if sub in hidden_subjects:
            continue
        emoji = SUBJECT_EMOJIS.get(sub, "ðŸ“š")
        is_selected = sub == current_pref
        mark = "🎯  " if is_selected else ""
        btn_text = f"{mark}{emoji} {label}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"pref_sub:select:{sub}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
        
    # None/Reset Option
    none_text = "âŒ تعطŠل المادة الت„قائŠة (تصفح ج…يع المواد)" if current_pref else "âŒ تخطŠ (عد… التفعŠل)"
    rows.append([InlineKeyboardButton(text=none_text, callback_data="pref_sub:select:none")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_students_keyboard(users: list[dict], page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
    rows = []
    # Display each student
    for u in users:
        telegram_id = u.get("telegram_id")
        first_name = u.get("first_name") or "طالب"
        preferred_name = u.get("preferred_name")
        username = u.get("username")
        is_banned = bool(u.get("is_banned"))
        
        display_name = preferred_name if preferred_name else first_name
        if username:
            display_name += f" (@{username})"
        
        # Add icons for status
        status_icon = "ðŸš« " if is_banned else "ðŸ‘¤ "
        
        rows.append([
            InlineKeyboardButton(
                text=f"{status_icon}{display_name}",
                callback_data=f"admin_student_detail:{telegram_id}:{page}"
            )
        ])
    
    # Navigation row
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="â¬…️ الساب‚", callback_data=f"admin_students_page:{page - 1}"))
    
    nav_row.append(InlineKeyboardButton(text=f"ðŸ“„ {page} / {total_pages}", callback_data="admin_students_noop"))
    
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="التالي âž¡ï¸", callback_data=f"admin_students_page:{page + 1}"))
        
    rows.append(nav_row)
    
    # Search and back buttons
    rows.append([
        InlineKeyboardButton(text="ðŸ” بحث ع† طالب", callback_data="admin_student_search"),
        InlineKeyboardButton(text="â†©ï¸ لوحة الإدارة", callback_data="admin_back_panel")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_student_detail_keyboard(student_id: int, is_currently_banned: bool, is_currently_admin: bool, return_page: int) -> InlineKeyboardMarkup:
    ban_text = "ðŸŸ¢ إ„غاء الحظر" if is_currently_banned else "ðŸš« حظر الحساب"
    admin_text = "🎓  ت†زŠل إ„Ù‰ طالب" if is_currently_admin else "ðŸ‘‘ تر‚ية لمشرف"
    
    rows = [
        [
            InlineKeyboardButton(text=ban_text, callback_data=f"admin_student_toggle_ban:{student_id}:{return_page}"),
            InlineKeyboardButton(text=admin_text, callback_data=f"admin_student_toggle_admin:{student_id}:{return_page}")
        ],
        [
            InlineKeyboardButton(text="â†©ï¸ العودة للقائمة", callback_data=f"admin_students_page:{return_page}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_question_confirm_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="âœ… تأƒيد الحفظ", callback_data="admin_q_confirm_save"),
            InlineKeyboardButton(text="âŒ إ„غاء", callback_data="admin_q_confirm_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_question_view_keyboard(question_id: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="⚙️  [إدارة] تعدŠل السؤال", callback_data=f"admin_direct_edit:{question_id}:search"),
            InlineKeyboardButton(text="ðŸ—‘️ حذف السؤال", callback_data=f"admin_question_delete:{question_id}")
        ],
        [
            InlineKeyboardButton(text="â†©ï¸ العودة للوحة الإدارة", callback_data="admin_back_panel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_question_delete_confirm_keyboard(question_id: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="âš ï¸ نع…ØŒ احذف نهائŠا‹", callback_data=f"admin_question_delete_confirm:{question_id}"),
            InlineKeyboardButton(text="âŒ تراجع", callback_data=f"admin_search_question_by_id:{question_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_edit_options_keyboard() -> InlineKeyboardMarkup:
    """Clavier avec options de saut et d'annulation pour l'édition de question."""
    rows = [
        [
            InlineKeyboardButton(text="âž¡ï¸ تخطŠ (الإب‚اء ع„Ù‰ الحالي)", callback_data="admin_edit_skip"),
            InlineKeyboardButton(text="âŒ إ„غاء التعدŠل", callback_data="admin_edit_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_edit_correct_keyboard() -> InlineKeyboardMarkup:
    """Clavier pour sélectionner la bonne réponse ou annuler/passer."""
    rows = [
        [
            InlineKeyboardButton(text="أ (A)", callback_data="admin_edit_ans:A"),
            InlineKeyboardButton(text="ب (B)", callback_data="admin_edit_ans:B")
        ],
        [
            InlineKeyboardButton(text="ج (C)", callback_data="admin_edit_ans:C"),
            InlineKeyboardButton(text="د (D)", callback_data="admin_edit_ans:D")
        ],
        [
            InlineKeyboardButton(text="âž¡ï¸ تخطŠ (الإب‚اء ع„Ù‰ الحالي)", callback_data="admin_edit_skip"),
            InlineKeyboardButton(text="âŒ إ„غاء التعدŠل", callback_data="admin_edit_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_revision_subjects_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting subject to revise."""
    rows = []
    current_row = []
    for sub_id, label in SUBJECT_LABELS.items():
        current_row.append(InlineKeyboardButton(text=label, callback_data=f"rev_sub:{sub_id}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
        
    rows.append([InlineKeyboardButton(text="ðŸ” بحث فŠ ج…يع المواد", callback_data="rev_study_search_start")])
    rows.append([InlineKeyboardButton(text="â—€️ القائ…ة الرئŠسŠة", callback_data="support_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_exam_blanc_subjects_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting subject for the exam blanc."""
    rows = []
    current_row = []
    for sub_id, label in SUBJECT_LABELS.items():
        current_row.append(InlineKeyboardButton(text=label, callback_data=f"exam_blanc_sub:{sub_id}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
        
    rows.append([InlineKeyboardButton(text="â—€️ القائ…ة الرئŠسŠة", callback_data="support_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_revision_lessons_keyboard(subject: str, lessons_status: list[dict]) -> InlineKeyboardMarkup:
    """
    Keyboard for choosing a lesson to revise.
    lessons_status: list of dicts: [{'course_number': int, 'has_mind_map': bool, 'has_summary': bool, 'has_transcription': bool}]
    """
    rows = []
    
    # Add Examen Blanc par matiere
    rows.append([InlineKeyboardButton(text="🎓  ا…تحا† تجرŠبŠ (20 سؤال)", callback_data=f"exam_blanc_sub:{subject}")])
    
    row = []
    for item in lessons_status:
        l = item['course_number']
        has_map = item['has_mind_map']
        has_sum = item['has_summary']
        has_trans = item.get('has_transcription', False)
        
        # Add visual markers if files are ready
        status_markers = ""
        if has_map and has_sum and has_trans:
            status_markers = " âœ…"
        elif has_map or has_sum or has_trans:
            status_markers = " ðŸŸ¡"
            
        row.append(InlineKeyboardButton(
            text=f"ðŸ“š الدرس {l}{status_markers}",
            callback_data=f"rev_les:{subject}:{l}"
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
        
    rows.append([InlineKeyboardButton(text="â—€️ العودة للخ„ف", callback_data="main_revision")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_revision_resources_keyboard(subject: str, lesson_num: int, has_map: bool, has_summary: bool, has_transcription: bool = False, has_study_path: bool = False) -> InlineKeyboardMarkup:
    """Keyboard showing available resources for a specific lesson (text menu, used when no map)."""
    rows = []
    if has_map:
        rows.append([InlineKeyboardButton(text="ðŸ—ºï¸ عرض الخرŠطة الذ‡نية (PNG)", callback_data=f"rev_get_map:{subject}:{lesson_num}")])
    else:
        rows.append([InlineKeyboardButton(text="ðŸ—ºï¸ الخرŠطة الذ‡نية (غŠر متˆفرة âŒ)", callback_data="rev_noop")])
        
    if has_summary:
        rows.append([InlineKeyboardButton(text="ðŸ“„ تح…يل الملخص (PDF)", callback_data=f"rev_get_sum:{subject}:{lesson_num}")])
    else:
        rows.append([InlineKeyboardButton(text="ðŸ“„ الملخص (غŠر متˆفر âŒ)", callback_data="rev_noop")])
        
    if has_transcription:
        rows.append([InlineKeyboardButton(text="ðŸ“ قراءة التفرŠغ (PNG)", callback_data=f"rev_read_trans_start:{subject}:{lesson_num}")])
        
        base_url = get_webapp_base_url()
        if True: # Always show Mini App button
            rows.append([InlineKeyboardButton(text="📖  وضع القراءة التفاع„ي (Liseuse) 📱 ", web_app=WebAppInfo(url=f"{base_url}/reader.html?subject={subject}&lesson={lesson_num}&v=p5"))])
    else:
        rows.append([InlineKeyboardButton(text="ðŸ“ التفرŠغ (غŠر متˆفر âŒ)", callback_data="rev_noop")])
        
    if has_study_path:
        rows.append([InlineKeyboardButton(text="📖  مسار القراءة التفاع„ي (Active Study) ✨", callback_data=f"rev_study_path_start:{subject}:{lesson_num}")])
        
    rows.append([InlineKeyboardButton(text="â†©ï¸ قائ…ة الدرˆس", callback_data=f"rev_sub:{subject}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_map_as_menu_keyboard(subject: str, lesson_num: int, has_summary: bool, has_transcription: bool, page: int = 1, total_pages: int = 1, has_study_path: bool = False) -> InlineKeyboardMarkup:
    """
    Keyboard displayed ON the mind map photo when the map IS the lesson menu.
    The map button is omitted (we're already viewing it).
    Navigation arrows are shown if there are multiple map pages.
    """
    rows = []
    # Multi-page navigation
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton(
                text="â—€️ الساب‚",
                callback_data=f"rev_map_page:{subject}:{lesson_num}:{page - 1}"
            ))
        nav_row.append(InlineKeyboardButton(
            text=f"ðŸ“„ {page} / {total_pages}",
            callback_data="rev_noop"
        ))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton(
                text="التالي â–¶ï¸",
                callback_data=f"rev_map_page:{subject}:{lesson_num}:{page + 1}"
            ))
        rows.append(nav_row)
    # Resource buttons
    if has_summary:
        rows.append([InlineKeyboardButton(text="ðŸ“„ تح…يل الملخص (PDF)", callback_data=f"rev_get_sum:{subject}:{lesson_num}")])
    else:
        rows.append([InlineKeyboardButton(text="ðŸ“„ الملخص (غŠر متˆفر âŒ)", callback_data="rev_noop")])
    if has_transcription:
        rows.append([InlineKeyboardButton(text="ðŸ“ قراءة التفرŠغ (PNG)", callback_data=f"rev_read_trans_start:{subject}:{lesson_num}")])
        
        base_url = get_webapp_base_url()
        if True: # Always show Mini App button
            rows.append([InlineKeyboardButton(text="📖  وضع القراءة التفاع„ي (Liseuse) 📱 ", web_app=WebAppInfo(url=f"{base_url}/reader.html?subject={subject}&lesson={lesson_num}&v=p5"))])
    else:
        rows.append([InlineKeyboardButton(text="ðŸ“ التفرŠغ (غŠر متˆفر âŒ)", callback_data="rev_noop")])
    if has_study_path:
        rows.append([InlineKeyboardButton(text="📖  مسار القراءة التفاع„ي (Active Study) ✨", callback_data=f"rev_study_path_start:{subject}:{lesson_num}")])
    rows.append([InlineKeyboardButton(text="â†©ï¸ قائ…ة الدرˆس", callback_data=f"rev_sub:{subject}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_resources_subject_keyboard() -> InlineKeyboardMarkup:
    """Admin selection of subject to upload resources."""
    rows = []
    for sub_id, label in SUBJECT_LABELS.items():
        rows.append([InlineKeyboardButton(text=label, callback_data=f"adm_res_sub:{sub_id}")])
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للوحة الإدارة", callback_data="admin_back_panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_resources_lessons_keyboard(subject: str, lessons_status: list[dict]) -> InlineKeyboardMarkup:
    """Admin choosing lesson to manage resources."""
    rows = []
    row = []
    for item in lessons_status:
        l = item['course_number']
        has_map = item['has_mind_map']
        has_sum = item['has_summary']
        has_trans = item.get('has_transcription', False)
        
        # Markers
        markers = ""
        if has_map:
            markers += "ðŸ—ºï¸"
        if has_sum:
            markers += "ðŸ“„"
        if has_trans:
            markers += "ðŸ“"
        if not markers:
            markers = "âŒ"
            
        row.append(InlineKeyboardButton(
            text=f"الدرس {l} ({markers})",
            callback_data=f"adm_res_les:{subject}:{l}"
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
        
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة للمواد", callback_data="admin_manage_resources")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_resources_manage_keyboard(subject: str, lesson_num: int, has_map: bool, has_summary: bool, has_transcription: bool = False) -> InlineKeyboardMarkup:
    """Admin manage resource page (upload buttons)."""
    map_text = "ðŸ”„ تحدŠث الخرŠطة الذ‡نية (PNG)" if has_map else "âž• رفع الخرŠطة الذ‡نية (PNG)"
    sum_text = "ðŸ”„ تحدŠث ملخص الدرس (PDF)" if has_summary else "âž• رفع ملخص الدرس (PDF)"
    trans_text = f"ðŸ“ إدارة صفحات التفرŠغ (PNG) {'(متˆفر âœ…)' if has_transcription else '(بدˆن تفرŠغ âš ï¸)'}"
    
    rows = [
        [InlineKeyboardButton(text=map_text, callback_data=f"adm_upl_map:{subject}:{lesson_num}")],
        [InlineKeyboardButton(text=sum_text, callback_data=f"adm_upl_sum:{subject}:{lesson_num}")],
        [InlineKeyboardButton(text=trans_text, callback_data=f"adm_manage_trans_pages:{subject}:{lesson_num}")],
        [InlineKeyboardButton(text="â†©ï¸ العودة لقائ…ة الدرˆس", callback_data=f"adm_res_sub:{subject}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_trans_pages_keyboard(subject: str, lesson_num: int, pages_count: int) -> InlineKeyboardMarkup:
    """Admin transcription pages management options."""
    rows = []
    rows.append([InlineKeyboardButton(text="âž• إضافة صفحة (PNG)", callback_data=f"adm_add_trans_page:{subject}:{lesson_num}")])
    if pages_count > 0:
        rows.append([InlineKeyboardButton(text="ðŸ—‘️ مسح كل صفحات التفرŠغ", callback_data=f"adm_clear_trans_pages:{subject}:{lesson_num}")])
    rows.append([InlineKeyboardButton(text="â†©ï¸ عˆدة لتعدŠل الملفات", callback_data=f"adm_res_les:{subject}:{lesson_num}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_transcription_reader_keyboard(subject: str, lesson_num: int, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Keyboard for transcription page carrousel slider navigation."""
    rows = []
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton(text="â¬…️ الساب‚ة", callback_data=f"rev_read_page:{subject}:{lesson_num}:{current_page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"{current_page} / {total_pages}", callback_data="rev_noop"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton(text="التالية âž¡ï¸", callback_data=f"rev_read_page:{subject}:{lesson_num}:{current_page+1}"))
    rows.append(nav_row)
    rows.append([InlineKeyboardButton(text="â†©ï¸ العودة لملفات الدرس", callback_data=f"rev_les:{subject}:{lesson_num}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_q_factory_review_keyboard() -> InlineKeyboardMarkup:
    """AI Question Factory review actions."""
    rows = [
        [
            InlineKeyboardButton(text="âœ… قبˆل وحفظ", callback_data="admin_q_fac_accept"),
            InlineKeyboardButton(text="âœï¸ تعدŠل السؤال", callback_data="admin_q_fac_edit")
        ],
        [
            InlineKeyboardButton(text="âŒ رفض وتخطي", callback_data="admin_q_fac_reject")
        ],
        [
            InlineKeyboardButton(text="ðŸ›‘ إ„غاء الع…لية بالكا…ل", callback_data="admin_q_fac_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_map_reader_keyboard(subject: str, lesson_num: int, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Keyboard shown beneath a mind map image: navigation arrows + back button."""
    rows = []
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton(
                text="â—€️ الساب‚",
                callback_data=f"rev_map_page:{subject}:{lesson_num}:{page - 1}"
            ))
        nav_row.append(InlineKeyboardButton(
            text=f"ðŸ“„ {page} / {total_pages}",
            callback_data="rev_noop"
        ))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton(
                text="التالي â–¶ï¸",
                callback_data=f"rev_map_page:{subject}:{lesson_num}:{page + 1}"
            ))
        rows.append(nav_row)
    rows.append([InlineKeyboardButton(
        text="â†©ï¸ العودة للملفات",
        callback_data=f"rev_map_back:{subject}:{lesson_num}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_map_action_keyboard(subject: str, lesson_num: int, existing_count: int) -> InlineKeyboardMarkup:
    """Admin: choose whether to replace all mind map pages or add a new page."""
    rows = [
        [InlineKeyboardButton(
            text=f"ðŸ”„ استبدال ج…يع الصفحات ({existing_count} موجˆدة)",
            callback_data=f"adm_map_replace:{subject}:{lesson_num}"
        )],
        [InlineKeyboardButton(
            text=f"âž• إضافة صفحة جدŠدة (الصفحة {existing_count + 1})",
            callback_data=f"adm_map_add_page:{subject}:{lesson_num}"
        )],
        [InlineKeyboardButton(text="âŒ إ„غاء", callback_data=f"adm_res_les:{subject}:{lesson_num}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_quiz_map_keyboard(question_id: int) -> InlineKeyboardMarkup:
    """Keyboard shown on a mind map sent from the quiz correction â€” just a back button."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="â†©ï¸ العودة للتصحŠح",
            callback_data=f"student_map_back:{question_id}"
        )
    ]])


def get_admin_model_selection_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to select AI Model for Question Generation."""
    rows = [
        [InlineKeyboardButton(text="Gemini Flash Latest (⭐ متˆاز† ود‚يق)", callback_data="adm_fac_model:gemini-flash-latest")],
        [InlineKeyboardButton(text="Gemini 2.5 Flash (âš¡ فائ‚ السرعة)", callback_data="adm_fac_model:gemini-2.5-flash")],
        [InlineKeyboardButton(text="Gemini Pro Latest (ðŸ§  استد„ال ع…يق)", callback_data="adm_fac_model:gemini-pro-latest")],
        [InlineKeyboardButton(text="âŒ إ„غاء", callback_data="admin_q_factory_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_count_selection_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to select Question Count."""
    rows = [
        [
            InlineKeyboardButton(text="5 أسئ„ة", callback_data="adm_fac_count:5"),
            InlineKeyboardButton(text="10 أسئ„ة", callback_data="adm_fac_count:10"),
            InlineKeyboardButton(text="15 سؤالا‹", callback_data="adm_fac_count:15")
        ],
        [InlineKeyboardButton(text="âŒ إ„غاء", callback_data="admin_q_factory_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_skip_instruction_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to skip custom instructions."""
    rows = [
        [InlineKeyboardButton(text="تخطŠ الخطˆة ⏭️", callback_data="adm_fac_inst:skip")],
        [InlineKeyboardButton(text="âŒ إ„غاء", callback_data="admin_q_factory_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_library_menu_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for My Library main menu."""
    rows = [
        [InlineKeyboardButton(text="ðŸ” البحث الذƒي فŠ الدرˆس", callback_data="rev_study_search_start")],
        [InlineKeyboardButton(text="ðŸ“š ملخصات وخرائط المواد", callback_data="library_subjects")],
        [InlineKeyboardButton(text="ðŸš€ مسار المراجعة الموج‡", callback_data="guided_path_start")],
        [InlineKeyboardButton(text="â†©ï¸ القائ…ة الرئŠسŠة", callback_data="support_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_guided_subjects_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting subject in guided path."""
    rows = []
    current_row = []
    for sub_id, label in SUBJECT_LABELS.items():
        current_row.append(InlineKeyboardButton(text=label, callback_data=f"guided_path_sub:{sub_id}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    rows.append([InlineKeyboardButton(text="â—€️ مكتبتŠ الشا…لة", callback_data="main_revision")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
def get_guided_lessons_keyboard(subject: str, lessons: list[int], progress_map: dict) -> InlineKeyboardMarkup:
    """
    Keyboard for guided path lesson selection.
    progress_map: dict of course_number -> dict of {resume_done, flashcards_done, mindmap_done, quiz_done}
    """
    rows = []
    row = []
    for l in lessons:
        prog = progress_map.get(l, {})
        resume_done = prog.get('resume_done', 0)
        flashcards_done = prog.get('flashcards_done', 0)
        mindmap_done = prog.get('mindmap_done', 0)
        quiz_done = prog.get('quiz_done', 0)
        
        # Determine status emoji
        if resume_done and flashcards_done and mindmap_done and quiz_done:
            status_emoji = "ðŸŸ©"
        elif resume_done or flashcards_done or mindmap_done or quiz_done:
            status_emoji = "ðŸŸ¨"
        else:
            status_emoji = "â¬œ"
            
        row.append(InlineKeyboardButton(
            text=f"الدرس {l} {status_emoji}",
            callback_data=f"guided_path_les:{subject}:{l}"
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="â†©ï¸ تغŠير المادة", callback_data="guided_path_start")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_guided_lesson_hub_keyboard(subject: str, lesson_num: int, prog: dict) -> InlineKeyboardMarkup:
    """Keyboard for lesson guided path dashboard."""
    resume_emoji = "ðŸŸ©" if prog.get('resume_done', 0) else "â¬œ"
    flash_emoji = "ðŸŸ©" if prog.get('flashcards_done', 0) else "â¬œ"
    map_emoji = "ðŸŸ©" if prog.get('mindmap_done', 0) else "â¬œ"
    quiz_emoji = "ðŸŸ©" if prog.get('quiz_done', 0) else "â¬œ"
    
    rows = [
        [InlineKeyboardButton(text=f"{resume_emoji} الخطˆة 1: قراءة الملخص", callback_data=f"guided_step:{subject}:{lesson_num}:summary")],
        [InlineKeyboardButton(text=f"{flash_emoji} الخطˆة 2: بطا‚ات الاستذƒار", callback_data=f"guided_step:{subject}:{lesson_num}:flashcards")],
        [InlineKeyboardButton(text=f"{map_emoji} الخطˆة 3: الخرŠطة الذ‡نية", callback_data=f"guided_step:{subject}:{lesson_num}:mindmap")],
        [InlineKeyboardButton(text=f"{quiz_emoji} الخطˆة 4: ت…رŠن الت‚ييم", callback_data=f"guided_step:{subject}:{lesson_num}:quiz")],
        [InlineKeyboardButton(text="â†©ï¸ العودة لمسار الدرˆس", callback_data=f"guided_path_sub:{subject}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Active Study Keyboards ---

def get_active_study_overview_keyboard(subject: str, lesson_num: int, current_chapter_index: int, total_chapters: int) -> InlineKeyboardMarkup:
    """Keyboard for the overview of Active Study path."""
    rows = []
    
    if current_chapter_index > 0 and current_chapter_index < total_chapters:
        start_btn_text = f"â–¶ï¸ استئ†اف التع„م (من المحˆر {current_chapter_index + 1})"
    elif current_chapter_index >= total_chapters:
        start_btn_text = "ðŸ” إعادة المسار التفاع„ي"
    else:
        start_btn_text = "â–¶ï¸ بدء التع„م التفاع„ي"
        
    rows.append([InlineKeyboardButton(text=start_btn_text, callback_data=f"active_study_go:{subject}:{lesson_num}")])
    
    # If they completed it, give them a shortcut to the end? Or let's just keep it simple.
    if current_chapter_index >= total_chapters:
        rows.append([InlineKeyboardButton(text="ðŸ—ºï¸ عرض الخرŠطة الذ‡نية", callback_data=f"active_study_mindmap:{subject}:{lesson_num}")])
        rows.append([InlineKeyboardButton(text="ðŸ“‘ عرض الملخص الشا…ل", callback_data=f"guided_step:{subject}:{lesson_num}:summary")])
    
    rows.append([InlineKeyboardButton(text="â—€️ العودة لصفحة الدرس", callback_data=f"rev_les:{subject}:{lesson_num}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_active_study_chapter_summary_keyboard(subject: str, lesson_num: int, chapter_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="ðŸ“ الا†ت‚ال لسؤال المحˆر", callback_data=f"active_study_q:{subject}:{lesson_num}:{chapter_id}")],
        [InlineKeyboardButton(text="â—€️ العودة للقائمة الساب‚ة", callback_data=f"rev_study_path_start:{subject}:{lesson_num}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_active_study_question_keyboard(subject: str, lesson_num: int, chapter_id: int, choices: dict) -> InlineKeyboardMarkup:
    rows = []
    
    # Determine layout mode based on text length
    max_len = max([len(v.strip()) for v in choices.values() if v]) if choices else 0
    use_grid = (max_len <= 35)

    row = []
    for key, text in choices.items():
        if text and text.strip():
            btn = InlineKeyboardButton(text=f"{key.upper()}. {text}", callback_data=f"active_study_ans:{subject}:{lesson_num}:{chapter_id}:{key}")
            row.append(btn)
            if use_grid:
                if len(row) == 2:
                    rows.append(row[::-1])
                    row = []
            else:
                rows.append([row[0]])
                row = []
                
    if row:
        if use_grid:
            rows.append(row[::-1])
        else:
            rows.append(row)
            
    # Add skip button
    rows.append([InlineKeyboardButton(text="⏭️ ف‡مت المحˆر (تجاˆز)", callback_data=f"active_study_skip:{subject}:{lesson_num}:{chapter_id}")])
    
    # Add back button
    rows.append([InlineKeyboardButton(text="â—€️ العودة للملخص", callback_data=f"active_study_resume:{subject}:{lesson_num}:{chapter_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_active_study_next_chapter_keyboard(subject: str, lesson_num: int, is_last: bool) -> InlineKeyboardMarkup:
    rows = []
    if is_last:
        rows.append([InlineKeyboardButton(text="âœ… إ†هاء وعرض الخرŠطة الذ‡نية", callback_data=f"active_study_mindmap:{subject}:{lesson_num}")])
    else:
        rows.append([InlineKeyboardButton(text="â–¶ï¸ المحˆر التالي", callback_data=f"active_study_go:{subject}:{lesson_num}")])
        
    rows.append([InlineKeyboardButton(text="â—€️ العودة لصفحة الدرس", callback_data=f"rev_les:{subject}:{lesson_num}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_active_study_end_keyboard(subject: str, lesson_num: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="ðŸ“‘ عرض الملخص الشا…ل (Fiche Express)", callback_data=f"guided_step:{subject}:{lesson_num}:summary")],
        [InlineKeyboardButton(text="ðŸ“ الا†ت‚ال للاختبار الشا…ل", callback_data=f"guided_step:{subject}:{lesson_num}:quiz")],
        [InlineKeyboardButton(text="â—€️ العودة لصفحة الدرس", callback_data=f"rev_les:{subject}:{lesson_num}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
