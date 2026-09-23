import os
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatJoinRequest, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo, FSInputFile
from aiogram.fsm.context import FSMContext
import aiosqlite
from config import DATABASE_PATH, TELEGRAM_ADMIN_IDS
import re
import logging
from database import log_student_action, log_student_action_by_tg

logger = logging.getLogger('bot')
router = Router(name="auth")

def get_webapp_base_url() -> str:
    for k in ["WEBAPP_URL", "BASE_URL", "RAILWAY_PUBLIC_DOMAIN", "RAILWAY_STATIC_URL", "RAILWAY_SERVICE_URL"]:
        val = os.getenv(k)
        if val and val.strip():
            v = val.strip().rstrip('/')
            if not v.startswith("http://") and not v.startswith("https://"):
                v = f"https://{v}"
            return v
    return "https://web-production-58dfa.up.railway.app"

async def send_welcome_with_banner(message: Message, text: str, reply_markup: InlineKeyboardMarkup):
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")

async def resolve_student_folder_link(db, s_dict):
    """
    Détermine le lien de dossier Telegram (1 parmi les 8 dossiers : 4 années x Homme/Femme)
    selon le niveau d'étude et le genre de l'élève.
    """
    gender_raw = (s_dict.get('gender') or 'HOMME').upper()
    is_female = gender_raw in ['FEMME', 'FEMALE', 'F', 'WOMAN', 'WOMEN', 'انثى', 'أنثى']
    gender_key = 'femme' if is_female else 'homme'

    yr_str = str(s_dict.get('year') or '').lower()
    year_num = 1
    if '4' in yr_str or 'رابع' in yr_str:
        year_num = 4
    elif '3' in yr_str or 'ثالث' in yr_str:
        year_num = 3
    elif '2' in yr_str or 'ثاني' in yr_str:
        year_num = 2
    else:
        year_num = 1

    year_arabic = ["الأولى", "الثانية", "الثالثة", "الرابعة"][year_num - 1]
    group_desc = f"السنة {year_arabic} {'نساء' if is_female else 'رجال'}"

    target_key = f"link_{gender_key}_{year_num}"
    folder_link = None
    try:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (target_key,)) as cur:
            row = await cur.fetchone()
            if row and row[0] and row[0].strip():
                folder_link = row[0].strip()
    except Exception as e:
        logger.warning(f"Error fetching setting {target_key}: {e}")

    if not folder_link:
        try:
            async with db.execute("SELECT folder_link FROM group_settings LIMIT 1") as cur:
                grow = await cur.fetchone()
                if grow and grow[0] and grow[0].strip():
                    folder_link = grow[0].strip()
        except Exception:
            pass

    if not folder_link:
        folder_link = "https://t.me/addlist/Yw-eXYtl1BVkYTdk"

    return folder_link, group_desc



@router.message(CommandStart())
@router.message(Command("start"))
@router.message(F.text.startswith("/start"))
async def handle_command_start(message: Message, state: FSMContext, bot: Bot):
    """Accueil intelligent : liaison automatique via magic link + gestion dynamique des boutons."""
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "طالب العلم"
    username = message.from_user.username or ""
    base_url = get_webapp_base_url()
    
    start_arg = ""
    text_parts = (message.text or "").strip().split()
    if len(text_parts) > 1:
        start_arg = text_parts[1].strip()

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # --- TRACKING ALL VISITORS ---
            visitor_source = start_arg if start_arg else 'organic'
            await db.execute("""
                INSERT OR IGNORE INTO bot_visitors (telegram_id, first_name, username, source)
                VALUES (?, ?, ?, ?)
            """, (user_id, first_name, username, visitor_source))
            await db.commit()
            # -----------------------------

            student = None
            is_chameleon_tag = False
            
            # 1. Traitement du Lien Magique depuis Email / WhatsApp
            if start_arg:
                                # Determine source for statistics
                click_source = "Lien Inconnu"
                if start_arg.startswith('e1_'): click_source = 'Email 1'
                elif start_arg.startswith('e2_'): click_source = 'Email 2'
                elif start_arg.startswith('w1_'): click_source = 'WhatsApp 1'
                elif start_arg.startswith('w2_'): click_source = 'WhatsApp 2'
                elif start_arg.startswith('sms_'): click_source = 'SMS'
                elif start_arg.startswith('auth_'): click_source = 'Admin Dashboard'
                
                clean_sid = re.sub(r'^(auth_|src_email_|src_wa_|src_web_|token_|e1_|e2_|w1_|w2_|sms_)', '', start_arg)
                
                # --- CHAMELEON BYPASS & SOURCE TRACKING ---
                import re as regex_mod
                pass_to_normal_flow = False
                source_tag = None
                
                # Check for suffix _e1, _wa1, etc.
                if '_' in clean_sid:
                    parts = clean_sid.split('_')
                    if parts[-1].lower() in ['e1', 'e2', 'wa1', 'wa2', 'sms']:
                        source_tag = parts[-1].upper()
                        clean_sid = '_'.join(parts[:-1])

                is_chameleon_tag = bool(regex_mod.match(r'^(?:[hf][1-5]?|[hf]1?[hf]1?|h1f1|f1h1|homme\d?|femme\d?)$', start_arg, regex_mod.IGNORECASE))
                if is_chameleon_tag:
                    student = None
                    pass_to_normal_flow = True
                else:
                    async with db.execute("SELECT * FROM academy_students WHERE magic_token = ? OR student_id = ? OR LOWER(email) = ?", (clean_sid, clean_sid, clean_sid.lower())) as cur:
                        student = await cur.fetchone()
                    
                if student:
                    s_dict = dict(student)
                    real_sid = s_dict['student_id']
                    existing_tg_id = s_dict.get('telegram_id')
                    
                    # SÉCURITÉ : si le compte est déjà lié à un AUTRE Telegram, on bloque
                    if existing_tg_id and str(existing_tg_id) != str(user_id):
                        await message.answer(
                            f"⚠️ <b>هذا الرابط مرتبط بحساب آخر</b>\n\n"
                            f"هذا الرابط تم استخدامه مسبقاً وربطه بحساب تيليجرام مختلف.\n\n"
                            f"إذا كنت تعتقد أن هناك خطأ، يُرجى التواصل مع إدارة الأكاديمية مباشرةً.",
                            parse_mode="HTML"
                        )
                        await log_student_action(real_sid, 'DUPLICATE_LINK_ATTEMPT', f"محاولة استخدام رابط مسجل لحساب آخر: {start_arg} من Telegram ID {user_id}", telegram_id=user_id, telegram_name=first_name, telegram_username=username)
                        return
                    
                    # Association instantanée du Telegram ID
                    await db.execute("UPDATE academy_students SET telegram_id = ?, telegram_username = ?, bot_started_at = COALESCE(bot_started_at, datetime('now')) WHERE student_id = ?", (user_id, username, real_sid))
                    
                    # Track Marketing Source if present
                    if source_tag:
                        existing_notes = s_dict.get('marketing_notes') or ''
                        if f'[Source: {source_tag}]' not in existing_notes:
                            new_notes = f"{existing_notes} [Source: {source_tag}]".strip()
                            await db.execute("UPDATE academy_students SET marketing_notes = ? WHERE student_id = ?", (new_notes, real_sid))
                            
                    await db.commit()
                    
                    # Récupération du lien officiel du dossier parmi les 8 dossiers configurés
                    folder_link, group_desc = await resolve_student_folder_link(db, s_dict)
                    student_first = s_dict.get('first_name') or first_name
                    has_joined = s_dict.get('group_joined') == 1
                    
                    import urllib.parse as _up
                    q_name = _up.quote(first_name or "")
                    q_user = _up.quote(username or "")

                    if has_joined:
                        # DÉJÀ REJOINT : PAS DE BOUTON DOSSIER
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="📚 دليل الطالب والأسئلة الشائعة والمكتبة", web_app=WebAppInfo(url=f"{base_url}/ask.html?telegram_id={user_id}&tg_name={q_name}&tg_user={q_user}&student_id={real_sid}&v=rag_v2"))],
                            [InlineKeyboardButton(text="🔗 منصة تأكيد البيانات والحساب", web_app=WebAppInfo(url=f"{base_url}/link.html?telegram_id={user_id}&tg_name={q_name}&tg_user={q_user}&student_id={real_sid}&v=magic_v51_active"))]
                        ])
                        magic_welcome = (
                            f"🎉 <b>أهلاً وسهلاً بك يا {student_first}! نبارك لك انضمامك لأكاديمية الباجي</b> 🎓\n\n"
                            f"✅ <b>حسابك مفعل وأنت عضو في مجموعات الدراسة الرسمية:</b>\n"
                            f"• مجموعتك الدراسية: <b>{group_desc}</b>\n\n"
                            f"👇 يمكنك الدخول للمكتبة أو طرح استفساراتك عبر الأزرار أدناه:"
                        )
                    else:
                        # EN ATTENTE DE REJOINDRE : BOUTON DOSSIER PRÉSENT
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="📁 إضافة مجلد الأكاديمية كاملاً إلى تليجرام", url=folder_link)],
                            [InlineKeyboardButton(text="🔗 منصة ربط الحساب وتأكيد البيانات", web_app=WebAppInfo(url=f"{base_url}/link.html?telegram_id={user_id}&tg_name={q_name}&tg_user={q_user}&student_id={real_sid}&v=magic_v51"))],
                            [InlineKeyboardButton(text="💬 مركز الدعم والأسئلة الشائعة والمكتبة", web_app=WebAppInfo(url=f"{base_url}/ask.html?telegram_id={user_id}&tg_name={q_name}&tg_user={q_user}&student_id={real_sid}&v=rag_v2"))]
                        ])
                        magic_welcome = (
                            f"🎉 <b>أهلاً وسهلاً بك يا {student_first}! نبارك لك انضمامك لأكاديمية الباجي</b> 🎓\n\n"
                            f"✅ <b>تم تفعيل وربط حسابك الدراسي بنجاح!</b>\n"
                            f"• رقم الطالب: <code>{real_sid}</code>\n"
                            f"• مجموعتك الدراسية: <b>{group_desc}</b>\n\n"
                            f"👇 <b>اضغط على الزر أدناه لإضافة مجلد قنوات ومجموعات دراستك بنقرة واحدة:</b>"
                        )
                    
                    await send_welcome_with_banner(message, magic_welcome, kb)
                    await log_student_action(real_sid, 'MAGIC_LINK_SUCCESS', f"تم الربط التلقائي بنقرة واحدة من الإيميل ({start_arg})", telegram_id=user_id, telegram_name=first_name, telegram_username=username)
                    return
                
                elif not pass_to_normal_flow:

                
                    # LIEN INVALIDE : numéro non trouvé en base → message d'erreur clair
                    await message.answer(
                        f"❌ <b>رابط غير صالح أو منتهي الصلاحية</b>\n\n"
                        f"الرابط الذي استخدمته لا يطابق أي حساب مسجل في أكاديمية الباجي.\n\n"
                        f"يُرجى التواصل مع إدارة الأكاديمية للحصول على الرابط الصحيح.",
                        parse_mode="HTML"
                    )
                    await log_student_action(0, 'INVALID_LINK_ATTEMPT', f"محاولة رابط غير صالح: {start_arg}", telegram_id=user_id, telegram_name=first_name, telegram_username=username)
                    try:
                        from config import TELEGRAM_SUPPORT_GROUP_ID
                        await message.bot.send_message(
                            TELEGRAM_SUPPORT_GROUP_ID,
                            f"🚨 <b>تنبيه أمني: محاولة دخول غير مصرح بها</b>\n\n"
                            f"الرابط المستخدم: <code>{start_arg}</code>\n"
                            f"الشخص: {first_name} (@{username})\n"
                            f"ID: <code>{user_id}</code>",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print("Alert error:", e)
                    return

            # 2. Vérification par Telegram ID si déjà lié (ignoré si lien caméléon/onboarding)
            if not is_chameleon_tag:
                async with db.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (user_id,)) as cur:
                    student = await cur.fetchone()
            else:
                student = None

        if student:
            s_dict = dict(student)
            real_name = s_dict.get('first_name') or first_name
            # Résolution dynamique parmi les 8 dossiers
            async with aiosqlite.connect(DATABASE_PATH) as _db_links:
                _db_links.row_factory = aiosqlite.Row
                folder_link, group_desc = await resolve_student_folder_link(_db_links, s_dict)
            has_joined = s_dict.get('group_joined') == 1
            
            if has_joined:
                # ÉLÈVE AYANT DÉJÀ REJOINT : LE BOUTON DU DOSSIER DISPARAÎT !
                welcome_text = (
                    f"أهلاً بك مجدداً يا <b>{real_name}</b> في أكاديمية الباجي! 🎓\n\n"
                    f"✅ <b>حسابك مفعل وأنت عضو رسمي في مجموعات الدراسة:</b>\n"
                    f"• مجموعتك الدراسية: <b>{group_desc}</b>\n\n"
                    f"👇 يمكنك متابعة الدروس أو استخدام المنصة أو التواصل مع الدعم عبر الأزرار أدناه:"
                )
                import urllib.parse as _up
                q_name = _up.quote(first_name or "")
                q_user = _up.quote(username or "")
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📚 دليل الطالب والأسئلة الشائعة والمكتبة", web_app=WebAppInfo(url=f"{base_url}/ask.html?telegram_id={user_id}&tg_name={q_name}&tg_user={q_user}&student_id={s_dict['student_id']}&v=rag_v2"))],
                    [InlineKeyboardButton(text="🔗 منصة تأكيد البيانات والحساب", web_app=WebAppInfo(url=f"{base_url}/link.html?telegram_id={user_id}&tg_name={q_name}&tg_user={q_user}&student_id={s_dict['student_id']}&v=linked_active"))]
                ])
            else:
                # ÉLÈVE N'AYANT PAS ENCORE REJOINT : BOUTON DU DOSSIER PRÉSENT
                welcome_text = (
                    f"أهلاً بك يا <b>{real_name}</b> في أكاديمية الباجي! 🎓\n\n"
                    f"✅ حسابك مربوط وجاهز لتأكيد الدخول.\n"
                    f"• مجموعتك المقررة: <b>{group_desc}</b>\n\n"
                    f"👇 <b>اضغط على الزر أدناه لإضافة مجلد الأكاديمية والانضمام فوراً للمجموعات:</b>"
                )
                import urllib.parse as _up
                q_name = _up.quote(first_name or "")
                q_user = _up.quote(username or "")
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📁 إضافة مجلد الأكاديمية كاملاً إلى تليجرام", url=folder_link)],
                    [InlineKeyboardButton(text="🔗 منصة ربط الحساب وتأكيد البيانات", web_app=WebAppInfo(url=f"{base_url}/link.html?telegram_id={user_id}&tg_name={q_name}&tg_user={q_user}&student_id={s_dict['student_id']}&v=pending_folder"))],
                    [InlineKeyboardButton(text="💬 مركز الدعم والاستفسارات", web_app=WebAppInfo(url=f"{base_url}/ask.html?telegram_id={user_id}&tg_name={q_name}&tg_user={q_user}&student_id={s_dict['student_id']}&v=rag_v2"))]
                ])
        else:
            # Smart Blocking Logic for Unknown Organic Users
            if not start_arg:
                # Organic. Check if they have a history of a valid source in bot_visitors
                async with db.execute("SELECT source FROM bot_visitors WHERE telegram_id = ?", (user_id,)) as cur:
                    row = await cur.fetchone()
                    original_source = row[0] if row else 'organic'
                
                # If they never used a link, block them!
                if original_source == 'organic':
                    await message.answer(
                        "❌ <b>التسجيل عبر دعوة فقط (Inscription sur invitation uniquement)</b>\n\n"
                        "عذراً، يجب عليك استخدام الرابط المخصص الذي تم إرساله إليك للوصول إلى هذه الخدمة.\n"
                        "Désolé, vous devez utiliser le lien spécifique qui vous a été envoyé pour accéder à ce service.",
                        parse_mode="HTML"
                    )
                    return

            welcome_text = (
                f"مرحباً بك يا <b>{first_name}</b> في أكاديمية الباجي! 🎓\n\n"
                f"هذا البوت هو بوابتك الرسمية لتفعيل عضويتك والانضمام للمجموعات الدراسية المقررة.\n\n"
                f"👇 <b>أنت على بُعد خطوة واحدة:</b> اضغط على الزر أدناه لربط حسابك أو التواصل مع الدعم:"
            )
            import time as _time
            _ts = int(_time.time())
            import urllib.parse as _up
            q_name = _up.quote(first_name or "")
            q_user = _up.quote(username or "")
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 منصة ربط الحساب وتفعيل الاشتراك", web_app=WebAppInfo(url=f"{base_url}/link.html?source={start_arg}&telegram_id={user_id}&tg_name={q_name}&tg_user={q_user}&v=start&_t={_ts}"))]
            ])


        await send_welcome_with_banner(message, welcome_text, kb)
        source_label = f" [رابط: {start_arg}]" if start_arg else ""
        st_label = f"طالب مسجل: {student['first_name']}" if student else "زائر جديد"
        await log_student_action(student['student_id'] if student else 0, 'BOT_START', f"بدء البوت عبر الرابط ({st_label}){source_label}", telegram_id=user_id, telegram_name=first_name, telegram_username=username)

    except Exception as e:
        logger.error(f"[START] Error: {e}")
        import urllib.parse as _up
        q_name = _up.quote(first_name or "")
        q_user = _up.quote(username or "")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 منصة ربط الحساب", web_app=WebAppInfo(url=f"{base_url}/link.html?telegram_id={user_id}&tg_name={q_name}&tg_user={q_user}"))]
        ])
        await message.answer("مرحباً بك في أكاديمية الباجي! اضغط على الزر أدناه لتفعيل حسابك:", reply_markup=kb)

@router.message(Command("png"))
@router.message(Command("schema"))
@router.message(Command("diagrams"))
async def cmd_png(message: Message):
    """عرض وإرسال المخطط الهندسي كصورة PNG مباشرة في المحادثة."""
    base_url = get_webapp_base_url()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 فتح المخطط التفاعلي عالي الدقة (HD Zoom)", web_app=WebAppInfo(url=f"{base_url}/diagrams/customer_journey_5_cases.html"))],
        [InlineKeyboardButton(text="🔐 فتح لوحة الإدارة (Gateway Admin)", web_app=WebAppInfo(url=f"{base_url}/admin_gateway.html?v=live_admin_v62"))]
    ])
    
    caption_text = (
        "📊 <b>مخطط رحلة الطلاب ومنظومة الأمان الذكية (أكاديمية الباجي)</b> 🎓\n\n"
        "1️⃣ <b>عمر الإدريسي (رجل):</b> دافع فوري ➔ تفعيل مباشر لمجموعة الرجال 🧔\n"
        "2️⃣ <b>خديجة العمراني (امرأة):</b> تفعيل مباشر لمجموعة النساء 🧕\n"
        "3️⃣ <b>فهد المنصوري (متطفل):</b> رابط محول ➔ البوت يرفض دخوله فوراً 🛑\n"
        "4️⃣ <b>طارق الجعفري (دفع متأخر 48h):</b> تفعيل فوري عند رفع الإكسيل المحدث ⚡\n"
        "5️⃣ <b>أسماء بنجلون (ريلانس واتساب H+24):</b> تفعيل بضغطة واحدة 💬"
    )
    
    png_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "diagrams", "customer_journey_5_cases.png")
    if os.path.exists(png_path):
        try:
            photo = FSInputFile(png_path)
            await message.answer_photo(photo=photo, caption=caption_text, reply_markup=kb, parse_mode="HTML")
            return
        except Exception as e:
            logger.error(f"[PNG_SEND_ERROR] {e}")
            
    await message.answer(caption_text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("template"))
@router.message(Command("excel"))
@router.message(Command("modele"))
async def cmd_send_template(message: Message):
    """إرسال ملف إكسيل النموذجي مباشرة في محادثة تليجرام."""
    template_file = os.path.join(os.path.dirname(__file__), "..", "dashboard", "albadr_students_template.csv")
    if os.path.exists(template_file):
        doc = FSInputFile(template_file, filename="albadr_students_template.csv")
        await message.answer_document(
            document=doc,
            caption=(
                "📥 <b>نموذج تسجيل الطلاب المعتمد (أكاديمية الباجي)</b> 🎓\n\n"
                "• يمكنك فتح هذا الملف في Excel وتعديل البيانات أو إضافة الطلاب.\n"
                "• بعد حفظ الملف، يمكنك رفعه مباشرة عبر لوحة التحكم /federer."
            ),
            parse_mode="HTML"
        )
    else:
        await message.answer("⚠️ تعذر العثور على ملف النموذج.")

@router.callback_query(F.data == "btn_send_excel_template")
async def cb_send_excel_template(callback: CallbackQuery):
    await callback.answer("⏳ جاري إرسال النموذج...")
    template_file = os.path.join(os.path.dirname(__file__), "..", "dashboard", "albadr_students_template.csv")
    if os.path.exists(template_file):
        doc = FSInputFile(template_file, filename="albadr_students_template.csv")
        await callback.message.answer_document(
            document=doc,
            caption="📥 <b>نموذج تسجيل الطلاب المعتمد (Excel/CSV)</b> 🎓",
            parse_mode="HTML"
        )

@router.message(Command("federer"))
async def cmd_federer(message: Message):
    """Menu complet pour les administrateurs et accès à toutes les applications."""
    user_id = message.from_user.id
    base_url = get_webapp_base_url()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 إدارة الطلاب والـ CRM (Gateway)", web_app=WebAppInfo(url=f"{base_url}/admin_gateway.html?v=live_admin_v62"))],
        [InlineKeyboardButton(text="🧠 الإدارة الشاملة (الأسئلة والفيديوهات والمقررات)", web_app=WebAppInfo(url=f"{base_url}/admin.html?v=master_admin"))],
        [InlineKeyboardButton(text="🤖 لوحة التحكم بالدعم والـ FAQ (Support CRM)", web_app=WebAppInfo(url=f"{base_url}/support.html?v=support"))],
        [InlineKeyboardButton(text="📖 منصة الطالب: الدروس والاختبارات (القارئ الذكي)", web_app=WebAppInfo(url=f"{base_url}/reader.html?v=reader"))],
        [InlineKeyboardButton(text="💬 منصة الطالب: الدعم والـ FAQ (ask.html)", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=rag_v2"))],
        [InlineKeyboardButton(text="🔗 منصة الطالب: الربط وتأكيد الحساب (link.html)", web_app=WebAppInfo(url=f"{base_url}/link.html?v=link2"))],
        [InlineKeyboardButton(text="📥 تحميل نموذج الإكسيل لإضافة طلاب", callback_data="btn_send_excel_template")]
    ])
    await message.answer("🤫 <b>لوحة الوصول الكامل والتطبيقات (Menu Federer) :</b>", reply_markup=kb, parse_mode="HTML")

@router.chat_join_request()
async def handle_join_request(update: ChatJoinRequest, bot: Bot):
    user_id = update.from_user.id
    chat_id = update.chat.id
    chat_title = update.chat.title or "مجموعات الأكاديمية"
    tg_first_name = update.from_user.first_name or "طالب العلم"
    username = update.from_user.username or ""
    base_url = get_webapp_base_url()
    support_url = f"{base_url}/ask.html"

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (user_id,)) as cursor:
                student = await cursor.fetchone()

        if student:
            student_dict = dict(student)
            payment_status = (student_dict.get('payment_status') or 'PAID').upper()
            gender = (student_dict.get('gender') or 'HOMME').upper()
            real_first_name = student_dict.get('first_name') or tg_first_name
            
            is_men_group = any(k in chat_title for k in ['رجال', 'إخوة', 'ذكور', 'Men', 'Hommes'])
            is_women_group = any(k in chat_title for k in ['نساء', 'أخوات', 'إناث', 'Women', 'Femmes'])
            wrong_gender = (is_men_group and gender == 'FEMME') or (is_women_group and gender == 'HOMME')

            if payment_status in ['PAID', 'PAYE', 'YES', 'OUI', 'VALIDE', 'ACTIVE', 'COMPLETED'] and not wrong_gender:
                try:
                    await update.approve()
                    
                    # Update group_joined = 1
                    async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                        await db_conn.execute("UPDATE academy_students SET group_joined = 1, joined_at = datetime('now') WHERE telegram_id = ?", (user_id,))
                        await db_conn.commit()
                        
                    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📚 دليل الطالب والأسئلة الشائعة", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=rag_v2"))],
                        [InlineKeyboardButton(text="💬 مركز الدعم والاستفسارات", web_app=WebAppInfo(url=support_url))]
                    ])
                    welcome_text = (
                        f"🎉 <b>أهلاً بك يا {real_first_name}!</b>\n\n"
                        f"✅ تمت الموافقة على انضمامك بنجاح إلى: <b>{chat_title}</b>.\n\n"
                        f"نتمنى لك رحلة تعليمية مباركة ونافعة في أكاديمية الباجي! 📚"
                    )
                    await bot.send_message(user_id, welcome_text, reply_markup=confirm_kb, parse_mode="HTML")
                    await log_student_action(student_dict['student_id'], 'JOIN_REQUEST_APPROVED', f"تمت الموافقة على الدخول إلى {chat_title}", telegram_id=user_id, telegram_name=tg_first_name, telegram_username=username)
                except Exception as e:
                    logger.error(f"[JOIN_REQUEST] Failed to approve: {e}")
                return
            elif wrong_gender:
                group_destination = "مجموعة الأخوات (نساء) 🧕" if gender == 'FEMME' else "مجموعة الإخوة (رجال) 🧔"
                msg_text = (
                    f"👋 مرحباً بك يا {real_first_name},\n\n"
                    f"تنبيه: هذه المجموعة مخصصة لـ ({'الرجال' if is_men_group else 'النساء'}).\n"
                    f"وفقاً لبيانات تسجيلك، مجموعتك المخصصة هي: <b>{group_destination}</b>.\n"
                    f"يرجى استخدام رابط مجموعتك المناسبة."
                )
                try:
                    await update.decline()
                    await bot.send_message(user_id, msg_text, parse_mode="HTML")
                except Exception:
                    pass
                await log_student_action(student_dict['student_id'], 'JOIN_REQUEST_WRONG_GENDER', f"رُفض الانضمام إلى {chat_title} بسبب الجنس", telegram_id=user_id, telegram_name=tg_first_name, telegram_username=username)
                return

        else:
            # ❌ Pas dans la base → refus AVANT d'entrer dans le groupe
            try:
                await update.decline()
                await bot.send_message(
                    user_id,
                    f"⛔ <b>تعذّر الانضمام إلى {chat_title}</b>\n\n"
                    f"لم يتم التعرف على حسابك في قاعدة بيانات أكاديمية الباجي.\n"
                    f"يُرجى التواصل مع الإدارة إذا كنت تعتقد أن هناك خطأ.",
                    parse_mode="HTML"
                )
            except Exception:
                pass
            await log_student_action(0, 'JOIN_REQUEST_DECLINED', f"رُفض طلب انضمام حساب غير مسجل إلى {chat_title}", telegram_id=user_id, telegram_name=tg_first_name, telegram_username=username)

    except Exception as e:
        logger.error(f"[JOIN_REQUEST] Error: {e}")


@router.chat_member()
async def handle_chat_member_update(update: ChatMemberUpdated, bot: Bot):
    """Détecte quand quelqu'un rejoint le groupe — vérifie s'il est inscrit en base."""
    try:
        new_status = update.new_chat_member.status
        old_status = update.old_chat_member.status
        
        if old_status not in ["member", "administrator"] and new_status in ["member", "administrator"]:
            user_id = update.new_chat_member.user.id
            tg_first_name = update.new_chat_member.user.first_name or "مجهول"
            tg_username = update.new_chat_member.user.username or ""
            chat_id = update.chat.id
            chat_title = update.chat.title or "المجموعة الرسمية"
            base_url = get_webapp_base_url()
            
            # Vérifier si ce Telegram ID est dans la base des élèves inscrits
            async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                db_conn.row_factory = aiosqlite.Row
                async with db_conn.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (user_id,)) as cur:
                        student = await cur.fetchone()
            
            if not student:
                # ❌ INTRUS : pas dans la base → expulser immédiatement
                try:
                    await bot.ban_chat_member(chat_id, user_id)
                    await bot.unban_chat_member(chat_id, user_id)  # unban pour ne pas le blacklister, juste virer
                except Exception as e:
                    logger.error(f"[KICK] Failed to kick unauthorized user {user_id}: {e}")
                
                # Avertir l'intrus
                try:
                    await bot.send_message(
                        user_id,
                        f"⛔ <b>تعذّر الانضمام إلى {chat_title}</b>\n\n"
                        f"لم يتم التعرف على حسابك في قاعدة بيانات أكاديمية الباجي.\n"
                        f"يُرجى التواصل مع الإدارة إذا كنت تعتقد أن هناك خطأ.",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
                
                await log_student_action(0, 'UNAUTHORIZED_JOIN_KICKED', f"تم طرد مستخدم غير مسجل من {chat_title}", telegram_id=user_id, telegram_name=tg_first_name, telegram_username=tg_username)
                return
            
            # ✅ Élève reconnu → marquer group_joined = 1
            student_dict = dict(student)
            async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                await db_conn.execute("UPDATE academy_students SET group_joined = 1, joined_at = datetime('now') WHERE telegram_id = ?", (user_id,))
                await db_conn.commit()
                
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 دليل الطالب والأسئلة الشائعة (FAQ)", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=rag_v2"))],
                [InlineKeyboardButton(text="💬 مركز الدعم والاستفسارات", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=rag_v2"))]
            ])
            
            msg = (
                f"🎉 <b>تم تأكيد انضمامك رسمياً وبنجاح إلى: {chat_title}!</b>\n\n"
                f"✅ تم تفعيل عضويتك واكتمال إعداد حسابك.\n"
                f"📚 نتمنى لك مسيرة علمية موفقة ومباركة في أكاديمية الباجي!\n\n"
                f"👇 يمكنك في أي وقت مراجعة الدليل أو طرح استفساراتك:"
            )
            
            try:
                await bot.send_message(user_id, msg, reply_markup=kb, parse_mode="HTML")
            except Exception:
                pass
                
            await log_student_action(student_dict['student_id'], 'MEMBER_JOINED', f"انضم رسمياً إلى {chat_title}", telegram_id=user_id, telegram_name=tg_first_name, telegram_username=tg_username)
    except Exception as e:
        logger.error(f"[CHAT_MEMBER] Error: {e}")

# ==========================================================
# 1-CLICK INSTANT ADMIN APPROVAL (FROM TELEGRAM SUPPORT GROUP)
# ==========================================================
@router.callback_query(F.data.startswith("admin_approve_"))
async def handle_admin_instant_approval(callback: CallbackQuery, bot: Bot):
    admin_user = callback.from_user
    data = callback.data or ""
    is_woman = "admin_approve_woman_" in data
    gender = "FEMME" if is_woman else "HOMME"
    gender_ar = "نساء 🧕" if is_woman else "رجال 🧔"
    
    parts = data.split("_")
    target_tg_id = parts[-1]
    
    try:
        target_tg_id = int(target_tg_id)
    except Exception:
        await callback.answer("❌ معرف الطالب غير صالح", show_alert=True)
        return

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (target_tg_id,)) as cur:
                student = await cur.fetchone()
                
            if not student:
                async with db.execute("SELECT * FROM pending_verifications WHERE telegram_id = ? ORDER BY id DESC LIMIT 1", (target_tg_id,)) as cur:
                    pv = await cur.fetchone()
                if pv and pv['email']:
                    async with db.execute("SELECT * FROM academy_students WHERE LOWER(email) = LOWER(?)", (pv['email'],)) as cur2:
                        student = await cur2.fetchone()

            if not student:
                await callback.answer("❌ تعذر العثور على بيانات هذا الطالب في النظام", show_alert=True)
                return

            s_dict = dict(student)
            real_sid = s_dict['student_id']
            first_name = s_dict.get('first_name') or "طالب العلم"
            
            await db.execute("""
                UPDATE academy_students 
                SET payment_status = 'PAID', gender = ?, telegram_id = ?
                WHERE student_id = ?
            """, (gender, target_tg_id, real_sid))
            
            await db.execute("DELETE FROM pending_verifications WHERE telegram_id = ?", (target_tg_id,))
            await db.commit()
            
            s_dict['gender'] = gender
            folder_link, group_desc = await resolve_student_folder_link(db, s_dict)
            
            base_url = get_webapp_base_url()
            kb_student = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📁 إضافة مجلد الأكاديمية كاملاً إلى تليجرام", url=folder_link)],
                [InlineKeyboardButton(text="🔗 منصة تأكيد البيانات", web_app=WebAppInfo(url=f"{base_url}/link.html?v=approved"))],
                [InlineKeyboardButton(text="💬 مركز الدعم والاستفسارات", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=rag_v2"))]
            ])
            
            student_msg = (
                f"🎉 <b>مبارك يا {first_name}! تمت المصادقة على حسابك وتفعيله بنجاح</b> ✅\n\n"
                f"• رقم الطالب: <code>{real_sid}</code>\n"
                f"• مجموعتك الدراسية: <b>{group_desc}</b>\n\n"
                f"👇 <b>اضغط على الزر أدناه لإضافة مجلد قنوات ومجموعات دراستك بنقرة واحدة:</b>"
            )
            
            try:
                await bot.send_message(target_tg_id, student_msg, reply_markup=kb_student, parse_mode="HTML")
            except Exception as e_send:
                logger.warning(f"Could not send instant approval message to {target_tg_id}: {e_send}")

            await log_student_action(
                real_sid, 
                'ADMIN_INSTANT_APPROVED', 
                f"تمت المصادقة الفورية من تليجرام بواسطة المشرف {admin_user.first_name} ({gender_ar})",
                telegram_id=target_tg_id
            )

        admin_name = admin_user.first_name or "المشرف"
        await callback.answer(f"✅ تم تفعيل حساب الطالب بنجاح ({gender_ar})")
        try:
            new_caption = (callback.message.text or callback.message.caption or "") + f"\n\n<b>✅ تم التفعيل الفوري بواسطة المشرف {admin_name} ({gender_ar})</b>"
            await callback.message.edit_reply_markup(reply_markup=None)
            if callback.message.text:
                await callback.message.edit_text(new_caption, parse_mode="HTML")
            elif callback.message.caption:
                await callback.message.edit_caption(caption=new_caption, parse_mode="HTML")
        except Exception as e_edit:
            logger.warning(f"Could not edit admin message: {e_edit}")

    except Exception as ex:
        logger.error(f"Error in instant approval: {ex}")
        await callback.answer("❌ حدث خطأ أثناء التفعيل", show_alert=True)

# ==========================================================

# ==========================================================
# TEST COMMAND FOR ADMINS (CLEAN SLATE)
# ==========================================================
@router.message(Command("reset_test"))
async def cmd_reset_test(message: Message):
    """Removes the admin's telegram_id from the database to simulate a brand new student."""
    if message.from_user.id not in TELEGRAM_ADMIN_IDS:
        return
        
    user_id = message.from_user.id
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("UPDATE academy_students SET telegram_id = NULL, group_joined = 0 WHERE telegram_id = ?", (user_id,))
            await db.execute("DELETE FROM bot_visitors WHERE telegram_id = ?", (user_id,))
            await db.execute("DELETE FROM student_logs WHERE telegram_id = ?", (user_id,))
            await db.commit()
            
        await message.answer(
            "🧹 <b>Mémoire effacée !</b>\n\n"
            "Ton compte Telegram a été totalement supprimé de la base de données du bot. "
            "Tu es maintenant un parfait inconnu.\n\n"
            "👉 <b>Tu peux maintenant cliquer sur un lien magique (ex: <code>t.me/ton_bot?start=h1</code>) pour tester le parcours du début (A à Z).</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Erreur: {e}")
        
# CONVERSATIONAL FALLBACK (WHEN STUDENT SENDS TEXT MESSAGES)
# ==========================================================
@router.message(F.text)
async def handle_student_text_fallback(message: Message, bot: Bot):
    """Réponse intelligente et polie quand un élève envoie un message texte libre au bot."""
    if message.chat.type != "private":
        return
        
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "طالب العلم"
    base_url = get_webapp_base_url()
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (user_id,)) as cur:
                student = await cur.fetchone()
                
            if student:
                s_dict = dict(student)
                folder_link, group_desc = await resolve_student_folder_link(db, s_dict)
                has_joined = s_dict.get('group_joined') == 1
                
                buttons = [
                    [InlineKeyboardButton(text="📚 دليل الطالب والأسئلة الشائعة (FAQ)", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=rag_v2"))],
                    [InlineKeyboardButton(text="🔗 منصة فحص وتأكيد الحساب", web_app=WebAppInfo(url=f"{base_url}/link.html?v=status"))]
                ]
                if not has_joined:
                    buttons.insert(0, [InlineKeyboardButton(text="📁 إضافة مجلد الأكاديمية إلى تليجرام", url=folder_link)])
                    
                kb = InlineKeyboardMarkup(inline_keyboard=buttons)
                resp_text = (
                    f"مرحباً بك يا <b>{first_name}</b> 🎓\n\n"
                    f"أنا المساعد الآلي لأكاديمية الباجي.\n"
                    f"• مجموعتك الدراسية: <b>{group_desc}</b>\n\n"
                    f"👇 لتصفح الدروس، مراجعة الأسئلة الشائعة أو التأكد من بياناتك، يُرجى استخدام الأزرار أدناه:"
                )
            else:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔗 منصة تفعيل وربط الحساب", web_app=WebAppInfo(url=f"{base_url}/link.html?v=chat_start"))],
                    [InlineKeyboardButton(text="💬 مركز الدعم والاستفسارات", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=rag_v2"))]
                ])
                resp_text = (
                    f"مرحباً بك يا <b>{first_name}</b> في أكاديمية الباجي 🎓\n\n"
                    f"لم يتم ربط حسابك الدراسي بعد.\n\n"
                    f"👇 يُرجى الضغط على الزر أدناه لتفعيل حسابك والانضمام لمجموعات دراستك المقررة:"
                )
                
            await message.answer(resp_text, reply_markup=kb, parse_mode="HTML")
    except Exception as e_fall:
        logger.error(f"[FALLBACK] Error: {e_fall}")
