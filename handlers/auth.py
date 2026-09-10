import os
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatJoinRequest, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo, FSInputFile
from aiogram.fsm.context import FSMContext
import aiosqlite
from config import DATABASE_PATH, TELEGRAM_ADMIN_IDS
import re
import logging
from database import log_student_action

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
    return "https://web-production-64c9ab.up.railway.app"

async def send_welcome_with_banner(message: Message, text: str, reply_markup: InlineKeyboardMarkup):
    logo_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "logo_albaji.png")
    if os.path.exists(logo_path):
        try:
            photo = FSInputFile(logo_path)
            await message.answer_photo(photo=photo, caption=text, reply_markup=reply_markup, parse_mode="HTML")
            return
        except Exception as e:
            logger.error(f"[BANNER_ERROR] {e}")
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


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
                    await db.commit()
                    
                    # Récupération du lien officiel du dossier
                    async with db.execute("SELECT * FROM group_settings LIMIT 1") as cur:
                        settings_row = await cur.fetchone()
                    settings = dict(settings_row) if settings_row else {}
                    
                    folder_link = settings.get('folder_link') or "https://t.me/addlist/Yw-eXYtl1BVkYTdk"
                    student_first = s_dict.get('first_name') or first_name
                    gender_clean = (s_dict.get('gender') or 'HOMME').upper()
                    is_female = gender_clean in ['FEMME', 'FEMALE', 'F', 'WOMAN', 'WOMEN']
                    group_desc = "السنة الأولى نساء" if is_female else "السنة الأولى رجال"
                    has_joined = s_dict.get('group_joined') == 1
                    
                    if has_joined:
                        # DÉJÀ REJOINT : PAS DE BOUTON DOSSIER
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="📚 دليل الطالب والأسئلة الشائعة والمكتبة", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=magic_v45_active"))],
                            [InlineKeyboardButton(text="🔗 منصة تأكيد البيانات والحساب", web_app=WebAppInfo(url=f"{base_url}/link.html?v=magic_v45_active"))]
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
                            [InlineKeyboardButton(text="🔗 منصة ربط الحساب وتأكيد البيانات", web_app=WebAppInfo(url=f"{base_url}/link.html?v=magic_v45"))],
                            [InlineKeyboardButton(text="💬 مركز الدعم والأسئلة الشائعة والمكتبة", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=magic_v45"))]
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
                
                else:
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

            # 2. Vérification par Telegram ID si déjà lié
            async with db.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (user_id,)) as cur:
                student = await cur.fetchone()

        if student:
            s_dict = dict(student)
            real_name = s_dict.get('first_name') or first_name
            gender_clean = (s_dict.get('gender') or 'HOMME').upper()
            is_female = gender_clean in ['FEMME', 'FEMALE', 'F', 'WOMAN', 'WOMEN']
            group_desc = "السنة الأولى نساء" if is_female else "السنة الأولى رجال"
            has_joined = s_dict.get('group_joined') == 1
            
            async with aiosqlite.connect(DATABASE_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM group_settings LIMIT 1") as cur:
                    settings_row = await cur.fetchone()
                settings = dict(settings_row) if settings_row else {}
            folder_link = settings.get('folder_link') or "https://t.me/addlist/Yw-eXYtl1BVkYTdk"
            
            if has_joined:
                # ÉLÈVE AYANT DÉJÀ REJOINT : LE BOUTON DU DOSSIER DISPARAÎT !
                welcome_text = (
                    f"أهلاً بك مجدداً يا <b>{real_name}</b> في أكاديمية الباجي! 🎓\n\n"
                    f"✅ <b>حسابك مفعل وأنت عضو رسمي في مجموعات الدراسة:</b>\n"
                    f"• مجموعتك الدراسية: <b>{group_desc}</b>\n\n"
                    f"👇 يمكنك متابعة الدروس أو استخدام المنصة أو التواصل مع الدعم عبر الأزرار أدناه:"
                )
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📚 دليل الطالب والأسئلة الشائعة والمكتبة", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=joined_active"))],
                    [InlineKeyboardButton(text="🔗 منصة تأكيد البيانات والحساب", web_app=WebAppInfo(url=f"{base_url}/link.html?v=linked_active"))]
                ])
            else:
                # ÉLÈVE N'AYANT PAS ENCORE REJOINT : BOUTON DU DOSSIER PRÉSENT
                welcome_text = (
                    f"أهلاً بك يا <b>{real_name}</b> في أكاديمية الباجي! 🎓\n\n"
                    f"✅ حسابك مربوط وجاهز لتأكيد الدخول.\n"
                    f"• مجموعتك المقررة: <b>{group_desc}</b>\n\n"
                    f"👇 <b>اضغط على الزر أدناه لإضافة مجلد الأكاديمية والانضمام فوراً للمجموعات:</b>"
                )
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📁 إضافة مجلد الأكاديمية كاملاً إلى تليجرام", url=folder_link)],
                    [InlineKeyboardButton(text="🔗 منصة ربط الحساب وتأكيد البيانات", web_app=WebAppInfo(url=f"{base_url}/link.html?v=pending_folder"))],
                    [InlineKeyboardButton(text="💬 مركز الدعم والاستفسارات", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=pending_folder"))]
                ])
        else:
            welcome_text = (
                f"مرحباً بك يا <b>{first_name}</b> في أكاديمية الباجي! 🎓\n\n"
                f"هذا البوت هو بوابتك الرسمية لتفعيل عضويتك والانضمام للمجموعات الدراسية المقررة.\n\n"
                f"👇 <b>أنت على بُعد خطوة واحدة:</b> اضغط على الزر أدناه لربط حسابك أو التواصل مع الدعم:"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 منصة ربط الحساب وتفعيل الاشتراك", web_app=WebAppInfo(url=f"{base_url}/link.html?v=start"))],
                [InlineKeyboardButton(text="💬 مركز الدعم والأسئلة الشائعة والمكتبة المرئية", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=start"))]
            ])

        await send_welcome_with_banner(message, welcome_text, kb)
        await log_student_action(student['student_id'] if student else 0, 'BOT_START', f"فتح البوت ({'مفعل' if student else 'جديد'})", telegram_id=user_id, telegram_name=first_name, telegram_username=username)

    except Exception as e:
        logger.error(f"[START] Error: {e}")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 منصة ربط الحساب", web_app=WebAppInfo(url=f"{base_url}/link.html"))]
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
        [InlineKeyboardButton(text="📊 لوحة تحكم المشرفين (Gateway Admin)", web_app=WebAppInfo(url=f"{base_url}/admin_gateway.html?v=live_admin_v45"))]
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
        [InlineKeyboardButton(text="📊 لوحة تحكم المشرفين وإدارة الطلاب (Gateway Admin)", web_app=WebAppInfo(url=f"{base_url}/admin_gateway.html?v=live_admin_v45"))],
        [InlineKeyboardButton(text="📥 إرسال نموذج الإكسيل الفارغ هنا (Telegram)", callback_data="btn_send_excel_template")],
        [InlineKeyboardButton(text="💬 مركز الدعم والأسئلة الشائعة (ask.html)", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=pro_new"))],
        [InlineKeyboardButton(text="🔗 منصة ربط الحساب والتحقق (link.html)", web_app=WebAppInfo(url=f"{base_url}/link.html?v=link2"))]
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
                        [InlineKeyboardButton(text="📚 دليل الطالب والأسئلة الشائعة", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=approved"))],
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
                [InlineKeyboardButton(text="📚 دليل الطالب والأسئلة الشائعة (FAQ)", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=joined"))],
                [InlineKeyboardButton(text="💬 مركز الدعم والاستفسارات", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=support"))]
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
