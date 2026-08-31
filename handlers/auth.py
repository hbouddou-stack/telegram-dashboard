import os
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo
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
    """Retourne toujours l'URL publique HTTPS valide de Railway."""
    import os
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
@router.message(F.text == "/start")
async def handle_command_start(message: Message, state: FSMContext):
    """Gestionnaire principal de la commande /start (Bouton Unique : منصة ربط الحساب)."""
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "طالب العلم"
    username = message.from_user.username or ""
    base_url = get_webapp_base_url()

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (user_id,)) as cur:
                student = await cur.fetchone()

        if student:
            s_dict = dict(student)
            real_name = s_dict.get('first_name') or first_name
            welcome_text = (
                f"أهلاً بك مجدداً يا <b>{real_name}</b> في أكاديمية أُسوة! 🎓\n\n"
                f"حسابك مفعل ومربوط بنجاح ✅\n\n"
                f"👇 اضغط على الزر أدناه لإدارة حسابك ومجموعاتك الدراسية:"
            )
        else:
            welcome_text = (
                f"مرحباً بك يا <b>{first_name}</b> في أكاديمية أُسوة! 🎓\n\n"
                f"هذا البوت هو بوابتك الرسمية لربط حسابك وتفعيل عضويتك والانضمام للمجموعات الدراسية المقررة.\n\n"
                f"👇 <b>أنت على بُعد خطوة واحدة:</b> اضغط على الزر أدناه للبدء:"
            )

        # 1. منصة ربط الحساب + 2. مركز الدعم والأسئلة الشائعة والفيديوهات (ask.html)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 منصة ربط الحساب وتفعيل الاشتراك", web_app=WebAppInfo(url=f"{base_url}/link.html?v=auth_{user_id}"))],
            [InlineKeyboardButton(text="💬 مركز الدعم والأسئلة الشائعة والمكتبة المرئية", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=support_{user_id}"))]
        ])

        await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")
        await log_student_action(student['student_id'] if student else 0, 'BOT_START', f"فتح البوت ({'مفعل' if student else 'جديد'})", telegram_id=user_id, telegram_name=first_name, telegram_username=username)

    except Exception as e:
        logger.error(f"[START] Error: {e}")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 منصة ربط الحساب", web_app=WebAppInfo(url=f"{base_url}/link.html"))]
        ])
        await message.answer("مرحباً بك في أكاديمية أُسوة! اضغط على الزر أدناه لتفعيل حسابك:", reply_markup=kb)

@router.message(Command("federer"))
async def cmd_federer(message: Message):
    """Menu complet pour les administrateurs et accès à toutes les applications."""
    user_id = message.from_user.id
    base_url = get_webapp_base_url()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 منصة الطالب والدروس (reader.html)", web_app=WebAppInfo(url=f"{base_url}/reader.html?v=dash2"))],
        [InlineKeyboardButton(text="💬 مركز الدعم والأسئلة الشائعة (ask.html)", web_app=WebAppInfo(url=f"{base_url}/ask.html?v=ask2"))],
        [InlineKeyboardButton(text="🔗 منصة ربط الحساب (link.html)", web_app=WebAppInfo(url=f"{base_url}/link.html?v=link2"))],
        [InlineKeyboardButton(text="🔧 لوحة تحكم المشرفين (admin.html)", web_app=WebAppInfo(url=f"{base_url}/admin.html"))]
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
                        f"نتمنى لك رحلة تعليمية مباركة ونافعة في أكاديمية أُسوة! 📚"
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

        # En attente
        import database as db_mod
        await db_mod.add_pending_verification(user_id, "", username, tg_first_name)
        await log_student_action(0, 'JOIN_REQUEST_WAITING', f"طلب انضمام قيد الانتظار لمجموعة: {chat_title}", telegram_id=user_id, telegram_name=tg_first_name, telegram_username=username)

        waiting_notification = (
            f"⏳ <b>مرحباً بك يا {tg_first_name}!</b>\n\n"
            f"📥 لقد استلمنا طلب انضمامك إلى: <b>{chat_title}</b>.\n\n"
            f"📋 طلبك حالياً <b>قيد المراجعة والمصادقة</b> مع إدارة الأكاديمية (لتأكيد التحويل البنكي أو مطابقة السجل).\n\n"
            f"⚡ <b>لا تقلق:</b> سيتم قبول طلبك ودخولك تلقائياً فور تأكيد الإدارة دون الحاجة لإعادة إرسال الطلب!\n\n"
            f"💬 إذا كان لديك أي استفسار، يمكنك فتح تذكرة عبر مركز الدعم في أي وقت."
        )
        try:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 فتح مركز الدعم والاستفسار", web_app=WebAppInfo(url=support_url))]
            ])
            await bot.send_message(user_id, waiting_notification, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            logger.error(f"[JOIN_REQUEST] Failed to send waiting notification: {e}")

    except Exception as e:
        logger.error(f"[JOIN_REQUEST] Global error: {e}")

@router.callback_query(F.data.startswith("confirm_join_"))
async def handle_confirm_join(callback: CallbackQuery):
    student_id_str = callback.data.replace("confirm_join_", "")
    student_id = int(student_id_str) if student_id_str.isdigit() else 0
    user_id = callback.from_user.id
    name = callback.from_user.first_name or ""
    
    await log_student_action(student_id, 'CONFIRM_JOIN_SUCCESS', "أكد الطالب دخوله للمجموعات بنجاح", telegram_id=user_id, telegram_name=name)
    await callback.answer("🎉 تم تأكيد دخولك بنجاح! دراسة موفقة بإذن الله.", show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("✅ <b>شكراً لتأكيدك!</b> حسابك الآن مفعل 100% ومكتمل في المنصة.")
    except Exception:
        pass
