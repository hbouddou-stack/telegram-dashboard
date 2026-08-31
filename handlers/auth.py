import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiosqlite
from config import DATABASE_PATH
import re
import logging
from database import log_student_action

logger = logging.getLogger('bot')
router = Router(name="auth")

class AuthStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_dob = State()

@router.chat_join_request()
async def handle_join_request(update: ChatJoinRequest, bot: Bot):
    """
    Gestionnaire intelligent des demandes d'adhésion aux groupes et canaux.
    Ne bloque JAMAIS brutalement l'élève.
    """
    user_id = update.from_user.id
    chat_id = update.chat.id
    chat_title = update.chat.title or "مجموعات الأكاديمية"
    tg_first_name = update.from_user.first_name or "طالب العلم"
    username = update.from_user.username or ""

    base_url = os.environ.get("BASE_URL", "https://oswah-academy.up.railway.app")
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
            
            # Vérification du genre si le titre du groupe le spécifie
            is_men_group = any(k in chat_title for k in ['رجال', 'إخوة', 'ذكور', 'Men', 'Hommes'])
            is_women_group = any(k in chat_title for k in ['نساء', 'أخوات', 'إناث', 'Women', 'Femmes'])
            
            wrong_gender = (is_men_group and gender == 'FEMME') or (is_women_group and gender == 'HOMME')

            if payment_status in ['PAID', 'PAYE', 'YES', 'OUI', 'VALIDE', 'ACTIVE', 'COMPLETED'] and not wrong_gender:
                # 1. Étudiant payant & bon groupe -> APPROBATION IMMÉDIATE
                try:
                    await update.approve()
                    
                    # Message de bienvenue avec boutons de confirmation et d'aide
                    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ دخلت المجموعات بنجاح", callback_data=f"confirm_join_{student_dict['student_id']}")],
                        [InlineKeyboardButton(text="🆘 لدي مشكلة / لم أتمكن من الدخول", web_app=WebAppInfo(url=support_url))]
                    ])
                    
                    welcome_text = (
                        f"🎉 <b>أهلاً بك يا {real_first_name}!</b>\n\n"
                        f"✅ تمت الموافقة على انضمامك إلى: <b>{chat_title}</b>.\n\n"
                        f"نتمنى لك رحلة تعليمية مباركة ونافعة في أكاديمية أُسوة! 📚\n\n"
                        f"👇 يرجى تأكيد دخولك بالضغط على الزر أدناه:"
                    )
                    await bot.send_message(user_id, welcome_text, reply_markup=confirm_kb, parse_mode="HTML")
                    
                    await log_student_action(student_dict['student_id'], 'JOIN_REQUEST_APPROVED', f"تمت الموافقة على الدخول إلى {chat_title}", telegram_id=user_id, telegram_name=tg_first_name, telegram_username=username)
                except Exception as e:
                    logger.error(f"[JOIN_REQUEST] Failed to approve: {e}")
                return
            elif wrong_gender:
                # Genre non correspondant -> Message d'explication courtois
                group_destination = "مجموعة الأخوات (نساء) 🧕" if gender == 'FEMME' else "مجموعة الإخوة (رجال) 🧔"
                msg_text = (
                    f"👋 مرحباً بك يا {real_first_name},\n\n"
                    f"تنبيه: هذه المجموعة مخصصة لـ ({'الرجال' if is_men_group else 'النساء'}).\n"
                    f"وفقاً لبيانات تسجيلك، مجموعتك المخصصة هي: <b>{group_destination}</b>.\n"
                    f"يرجى استخدام رابط مجموعتك المناسبة."
                )
                try:
                    await bot.send_message(user_id, msg_text, parse_mode="HTML")
                    await log_student_action(student_dict['student_id'], 'WRONG_GENDER_GROUP_ATTEMPT', f"محاولة دخول لمجموعة غير مطابقة: {chat_title}", telegram_id=user_id, telegram_name=tg_first_name, telegram_username=username)
                except Exception:
                    pass
                return

        # 2. Étudiant non encore validé dans l'Excel (Virement en cours / En attente de synchronisation)
        import database as db_mod
        await db_mod.add_pending_verification(user_id, "", username, tg_first_name)
        await log_student_action(0, 'JOIN_REQUEST_WAITING', f"طلب انضمام قيد الانتظار لمجموعة: {chat_title}", telegram_id=user_id, telegram_name=tg_first_name, telegram_username=username)

        waiting_notification = (
            f"⏳ <b>مرحباً بك يا {tg_first_name}!</b>\n\n"
            f"📥 لقد استلمنا طلب انضمامك إلى: <b>{chat_title}</b>.\n\n"
            f"📋 طلبك حالياً <b>قيد المراجعة والمصادقة</b> مع إدارة الأكاديمية (لتأكيد التحويل البنكي أو مطابقة السجل).\n\n"
            f"⚡ <b>لا تقلق:</b> سيتم قبول طلبك ودخولك تلقائياً فور تأكيد الإدارة دون الحاجة لإعادة إرسال الطلب!\n\n"
            f"💬 إذا كان لديك أي استفسار، يمكنك التواصل المباشر عبر مركز الدعم:"
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
    """L'élève confirme qu'il a bien rejoint les groupes avec succès."""
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
