import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiosqlite
from config import DATABASE_PATH
import re
import logging

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
    first_name = update.from_user.first_name or "طالب العلم"
    username = update.from_user.username or ""

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (user_id,)) as cursor:
                student = await cursor.fetchone()

        if student:
            student_dict = dict(student)
            payment_status = (student_dict.get('payment_status') or 'PAID').upper()
            gender = (student_dict.get('gender') or 'HOMME').upper()
            
            # Vérification du genre si le titre du groupe le spécifie
            is_men_group = any(k in chat_title for k in ['رجال', 'إخوة', 'ذكور', 'Men', 'Hommes'])
            is_women_group = any(k in chat_title for k in ['نساء', 'أخوات', 'إناث', 'Women', 'Femmes'])
            
            wrong_gender = (is_men_group and gender == 'FEMME') or (is_women_group and gender == 'HOMME')

            if payment_status in ['PAID', 'PAYE', 'YES', 'OUI', 'VALIDE', 'ACTIVE', 'COMPLETED'] and not wrong_gender:
                # 1. Étudiant payant & bon groupe -> APPROBATION IMMÉDIATE
                try:
                    await update.approve()
                    welcome_text = (
                        f"🎉 <b>أهلاً بك يا {first_name}!</b>\n\n"
                        f"✅ تمت الموافقة التلقائية على انضمامك إلى: <b>{chat_title}</b>.\n"
                        f"نتمنى لك رحلة تعليمية مباركة ونافعة! 📚"
                    )
                    await bot.send_message(user_id, welcome_text, parse_mode="HTML")
                    
                    from database import log_student_action
                    await log_student_action(student_dict['student_id'], 'GROUP_JOINED', f"انضم إلى المجموعة: {chat_title}")
                except Exception as e:
                    logger.error(f"[JOIN_REQUEST] Failed to approve: {e}")
                return
            elif wrong_gender:
                # Genre non correspondant -> Message d'explication courtois (sans rejet définitif)
                group_destination = "مجموعة الأخوات (نساء) 🧕" if gender == 'FEMME' else "مجموعة الإخوة (رجال) 🧔"
                msg_text = (
                    f"👋 مرحباً بك يا {first_name},\n\n"
                    f"تنبيه: هذه المجموعة مخصصة لـ ({'الرجال' if is_men_group else 'النساء'}).\n"
                    f"وفقاً لبيانات تسجيلك، مجموعتك المخصصة هي: <b>{group_destination}</b>.\n"
                    f"يرجى استخدام رابط مجموعتك المناسبة."
                )
                try:
                    await bot.send_message(user_id, msg_text, parse_mode="HTML")
                except Exception:
                    pass
                return

        # 2. Étudiant non encore validé dans l'Excel (Virement en cours / En attente de synchronisation)
        # ⚠️ RÈGLE FONDAMENTALE : ON NE DÉCLINE PAS LA DEMANDE ! On la laisse en attente.
        import database as db_mod
        await db_mod.add_pending_verification(user_id, "", username, first_name)

        waiting_notification = (
            f"⏳ <b>مرحباً بك يا {first_name}!</b>\n\n"
            f"📥 لقد استلمنا طلب انضمامك إلى: <b>{chat_title}</b>.\n\n"
            f"📋 طلبك حالياً <b>قيد المراجعة والمصادقة</b> مع إدارة الأكاديمية (لتأكيد التحويل البنكي أو مطابقة التسجيل الجديد).\n\n"
            f"⚡ <b>لا تقلق:</b> سيتم قبول طلبك ودخولك تلقائياً فور تأكيد الإدارة دون الحاجة لإعادة إرسال الطلب!\n\n"
            f"💬 إذا كان لديك أي استفسار، يمكنك فتح تذكرة عبر مركز الدعم في أي وقت."
        )
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
            base_url = os.environ.get("BASE_URL", "https://oswah-academy.up.railway.app")
            support_url = f"{base_url}/ask.html"
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 فتح مركز الدعم والاستفسار", web_app=WebAppInfo(url=support_url))]
            ])
            await bot.send_message(user_id, waiting_notification, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            logger.error(f"[JOIN_REQUEST] Failed to send waiting notification: {e}")

    except Exception as e:
        logger.error(f"[JOIN_REQUEST] Global error: {e}")
