import os
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatJoinRequest, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiosqlite
from config import DATABASE_PATH, TELEGRAM_ADMIN_IDS
import re
import logging
from database import log_student_action

logger = logging.getLogger('bot')
router = Router(name="auth")

def get_webapp_base_url() -> str:
    """Retourne l'URL publique HTTPS valide de Railway."""
    for k in ["WEBAPP_URL", "BASE_URL", "RAILWAY_PUBLIC_DOMAIN", "RAILWAY_STATIC_URL", "RAILWAY_SERVICE_URL"]:
        val = os.getenv(k)
        if val and val.strip():
            v = val.strip().rstrip('/')
            if not v.startswith("http://") and not v.startswith("https://"):
                v = f"https://{v}"
            return v
    return "https://web-production-64c9ab.up.railway.app"

@router.message(CommandStart())
@router.message(Command("start"))
@router.message(F.text.startswith("/start"))
async def handle_command_start(message: Message, state: FSMContext, bot: Bot):
    """Expérience 100% Native Telegram Bot : Rapide, fluide et sans aucune lenteur de Mini-App."""
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
            student = None
            
            # 1. Traitement du Lien Magique depuis Email / WhatsApp
            if start_arg:
                clean_sid = re.sub(r'^(auth_|src_email_|src_wa_|src_web_|token_)', '', start_arg)
                
                async with db.execute("SELECT * FROM academy_students WHERE student_id = ? OR LOWER(email) = ?", (clean_sid, clean_sid.lower())) as cur:
                    student = await cur.fetchone()
                    
                if student:
                    s_dict = dict(student)
                    real_sid = s_dict['student_id']
                    # Association instantanée du Telegram ID
                    await db.execute("UPDATE academy_students SET telegram_id = ?, telegram_username = ? WHERE student_id = ?", (user_id, username, real_sid))
                    await db.commit()
                    
                    # Récupération du lien de dossier / groupe
                    async with db.execute("SELECT * FROM group_settings LIMIT 1") as cur:
                        settings_row = await cur.fetchone()
                    settings = dict(settings_row) if settings_row else {}
                    
                    folder_link = settings.get('folder_link') or "https://t.me/addlist/u2f-aW9sdhk1NmVk"
                    student_first = s_dict.get('first_name') or first_name
                    gender_clean = (s_dict.get('gender') or 'HOMME').upper()
                    is_female = gender_clean in ['FEMME', 'FEMALE', 'F', 'WOMAN', 'WOMEN']
                    group_desc = "السنة الأولى نساء" if is_female else "السنة الأولى رجال"
                    
                    # BOUTONS DIRECTS NATIFS TELEGRAM (0 LATENCE)
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📁 إضافة مجلد الأكاديمية كاملاً إلى تليجرام", url=folder_link)],
                        [InlineKeyboardButton(text="💬 مركز الدعم والأسئلة الشائعة", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=native"))]
                    ])
                    
                    magic_welcome = (
                        f"🎉 <b>أهلاً وسهلاً بك يا {student_first}! نبارك لك انضمامك لأكاديمية البدر</b> 🎓\n\n"
                        f"✅ <b>تم تفعيل وربط حسابك الدراسي بنجاح!</b>\n"
                        f"• رقم الطالب: <code>{real_sid}</code>\n"
                        f"• مجموعتك: <b>{group_desc}</b>\n\n"
                        f"👇 <b>اضغط على الزر أدناه لإضافة مجلد قنوات ومجموعات دراستك بنقرة واحدة:</b>"
                    )
                    
                    await message.answer(magic_welcome, reply_markup=kb, parse_mode="HTML")
                    await log_student_action(real_sid, 'MAGIC_LINK_SUCCESS', f"تم الربط التلقائي بنقرة واحدة من الإيميل ({start_arg})", telegram_id=user_id, telegram_name=first_name, telegram_username=username)
                    return

            # 2. Vérification par Telegram ID si déjà lié
            async with db.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (user_id,)) as cur:
                student = await cur.fetchone()

        if student:
            s_dict = dict(student)
            real_name = s_dict.get('first_name') or first_name
            
            async with aiosqlite.connect(DATABASE_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM group_settings LIMIT 1") as cur:
                    settings_row = await cur.fetchone()
                settings = dict(settings_row) if settings_row else {}
            folder_link = settings.get('folder_link') or "https://t.me/addlist/u2f-aW9sdhk1NmVk"
            
            welcome_text = (
                f"أهلاً بك مجدداً يا <b>{real_name}</b> في أكاديمية البدر! 🎓\n\n"
                f"حسابك مفعل ومربوط بنجاح ✅\n\n"
                f"👇 يمكنك إضافة مجلد دراستك أو التواصل مع الدعم عبر الأزرار أدناه:"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📁 إضافة مجلد الأكاديمية إلى تليجرام", url=folder_link)],
                [InlineKeyboardButton(text="💬 مركز الدعم والأسئلة الشائعة", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=native"))]
            ])
        else:
            welcome_text = (
                f"مرحباً بك يا <b>{first_name}</b> في أكاديمية البدر! 🎓\n\n"
                f"هذا البوت هو بوابتك الرسمية لتفعيل عضويتك والانضمام للمجموعات الدراسية المقررة.\n\n"
                f"إذا كنت مسجلاً في الأكاديمية، يرجى الضغط على رابط التفعيل الذي وصلك عبر البريد الإلكتروني، أو استخدام الزر أدناه:"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 منصة ربط الحساب وتفعيل الاشتراك", web_app=WebAppInfo(url=f"{base_url}/link.html?v=start"))],
                [InlineKeyboardButton(text="💬 مركز الدعم والأسئلة الشائعة", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=start"))]
            ])

        await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")
        await log_student_action(student['student_id'] if student else 0, 'BOT_START', f"فتح البوت ({'مفعل' if student else 'جديد'})", telegram_id=user_id, telegram_name=first_name, telegram_username=username)

    except Exception as e:
        logger.error(f"[START] Error: {e}")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 تفعيل الحساب", web_app=WebAppInfo(url=f"{base_url}/link.html"))]
        ])
        await message.answer("مرحباً بك في أكاديمية البدر! اضغط على الزر أدناه لتفعيل حسابك:", reply_markup=kb)

@router.message(Command("federer"))
async def cmd_federer(message: Message):
    """Menu complet pour les administrateurs et accès à toutes les applications."""
    user_id = message.from_user.id
    base_url = get_webapp_base_url()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 لوحة تحكم المشرفين وإدارة الطلاب (Gateway Admin)", web_app=WebAppInfo(url=f"{base_url}/admin_gateway.html?v=live_admin"))],
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
                    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ دخلت المجموعات بنجاح", callback_data=f"confirm_join_{student_dict['student_id']}")],
                        [InlineKeyboardButton(text="🆘 لدي مشكلة / لم أتمكن من الدخول", web_app=WebAppInfo(url=support_url))]
                    ])
                    welcome_text = (
                        f"🎉 <b>أهلاً بك يا {real_first_name}!</b>\n\n"
                        f"✅ تمت الموافقة على انضمامك إلى: <b>{chat_title}</b>.\n\n"
                        f"نتمنى لك رحلة تعليمية مباركة ونافعة في أكاديمية البدر! 📚"
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
                    await bot.send_message(user_id, msg_text, parse_mode="HTML")
                except Exception:
                    pass
                return

    except Exception as e:
        logger.error(f"[JOIN_REQUEST] Error: {e}")

@router.chat_member()
async def handle_chat_member_update(update: ChatMemberUpdated, bot: Bot):
    """Détecte quand l'élève rejoint effectivement le groupe via son lien unique et met à jour son statut."""
    try:
        new_status = update.new_chat_member.status
        old_status = update.old_chat_member.status
        
        if old_status not in ["member", "administrator"] and new_status in ["member", "administrator"]:
            user_id = update.new_chat_member.user.id
            chat_title = update.chat.title or "المجموعة الرسمية"
            base_url = get_webapp_base_url()
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 دليل الطالب والأسئلة الشائعة (FAQ)", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=joined"))],
                [InlineKeyboardButton(text="💬 مركز الدعم والاستفسارات", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=support"))]
            ])
            
            msg = (
                f"✅ <b>تم انضمامك وتأكيد عضويتك بنجاح في: {chat_title}!</b>\n\n"
                f"🎉 نتمنى لك مسيرة علمية موفقة ومباركة في أكاديمية البدر.\n"
                f"👇 يمكنك في أي وقت مراجعة دليل الطالب أو طرح استفساراتك عبر الأزرار أدناه:"
            )
            
            try:
                await bot.send_message(user_id, msg, reply_markup=kb, parse_mode="HTML")
            except Exception:
                pass
                
            await log_student_action(0, 'MEMBER_JOINED', f"انضم إلى {chat_title}", telegram_id=user_id, telegram_name=update.new_chat_member.user.first_name, telegram_username=update.new_chat_member.user.username)
    except Exception as e:
        logger.error(f"[CHAT_MEMBER] Error: {e}")

@router.callback_query(F.data.startswith("admin_approve_"))
async def handle_admin_instant_approval(callback: CallbackQuery, bot: Bot):
    try:
        data = callback.data
        parts = data.split("_")
        gender_type = parts[2]
        target_tg_id = int(parts[3])
        
        admin_name = callback.from_user.first_name or "المشرف"
        gender_str = "HOMME" if gender_type == "man" else "FEMME"
        
        import database as db
        success = await db.approve_pending_student(target_tg_id, gender_str, admin_name)
        
        if success:
            await callback.answer("✅ تمت المصادقة بنجاح!", show_alert=True)
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (target_tg_id,)) as cur:
                    row = await cur.fetchone()
            
            if row:
                student_data = dict(row)
                from main import generate_and_send_student_links
                await generate_and_send_student_links(bot, target_tg_id, student_data)
                
            await callback.message.edit_text(
                f"{callback.message.text}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ <b>تمت المصادقة بنجاح بواسطة: {admin_name}</b>\n"
                f"• تم تفعيل الحساب وتحديد الجنس: ({'رجال 🧔' if gender_str == 'HOMME' else 'نساء 🧕'})\n"
                f"• تم إرسال روابط المجموعات الخاصة للطالب فوراً.",
                parse_mode="HTML",
                reply_markup=None
            )
        else:
            await callback.answer("⚠️ تعذر العثور على بيانات هذا الطالب أو تمت معالجته مسبقاً.", show_alert=True)
    except Exception as e:
        logger.error(f"[ADMIN_APPROVE_ERROR] {e}")
        await callback.answer(f"خطأ أثناء المصادقة: {e}", show_alert=True)
