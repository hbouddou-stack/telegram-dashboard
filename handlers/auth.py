import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiosqlite
from config import DATABASE_PATH
import re

router = Router(name="auth")

class AuthStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_dob = State()

@router.callback_query(F.data == "cmd_lier_compte")
async def cb_lier_compte(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    class MockMessage:
        def __init__(self, msg, user):
            self.message = msg
            self.from_user = user
        async def answer(self, *args, **kwargs):
            return await self.message.answer(*args, **kwargs)
    
    mock_msg = MockMessage(callback.message, callback.from_user)
    await cmd_lier_compte(mock_msg, state)

@router.message(Command("lier_compte"))
async def cmd_lier_compte(message: Message, state: FSMContext):
    # Check if already linked
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT student_id, first_name FROM academy_students WHERE telegram_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                await message.answer(f"✅ Ton compte est déjà lié, {row[1]} !")
                return

    await state.set_state(AuthStates.waiting_for_email)
    await message.answer(
        "🔒 **Connexion à l'Académie**\n\n"
        "Pour accéder aux groupes privés et à la Mini App, nous devons vérifier ton identité.\n\n"
        "👉 **Quel est l'email que tu as utilisé lors de ton inscription ?**",
        parse_mode="Markdown"
    )

@router.message(AuthStates.waiting_for_email, F.text)
async def process_email(message: Message, state: FSMContext):
    email = message.text.strip().lower()
    
    # Basic email validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await message.answer("❌ Cet email n'est pas valide. Veuillez réessayer.")
        return

    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT student_id FROM academy_students WHERE email = ?", (email,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await message.answer("❌ Aucun compte trouvé avec cet email dans notre base.\nVérifie les fautes de frappe et réessaie, ou contacte le support.")
                return
            
    await state.update_data(email=email)
    await state.set_state(AuthStates.waiting_for_dob)
    await message.answer(
        "✅ Email trouvé !\n\n"
        "Par mesure de sécurité, merci de confirmer ton identité.\n"
        "👉 **Tape ta date de naissance au format JJ/MM/AAAA** (ex: 15/04/1995) :"
    )

@router.message(AuthStates.waiting_for_dob, F.text)
async def process_dob(message: Message, state: FSMContext):
    dob = message.text.strip()
    data = await state.get_data()
    email = data.get("email")

    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT student_id, first_name, dob, telegram_id FROM academy_students WHERE email = ?", (email,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await state.clear()
                await message.answer("Une erreur est survenue. Recommencez avec /lier_compte.")
                return
            
            actual_dob = row[2]
            if dob != actual_dob:
                await message.answer("❌ La date de naissance ne correspond pas à nos dossiers. Veuillez réessayer (JJ/MM/AAAA).")
                return
            
            # Link successful
            await db.execute("UPDATE academy_students SET telegram_id = ? WHERE email = ?", (message.from_user.id, email))
            await db.commit()
            
            first_name = row[1]
            
            await state.clear()
            await message.answer(
                f"🎉 **Félicitations {first_name} !**\n\n"
                f"Ton compte est désormais lié à l'Académie.\n"
                f"Tu peux maintenant rejoindre nos espaces privés et accéder à la Mini App en un clic.",
                parse_mode="Markdown"
            )

@router.chat_join_request()
async def handle_join_request(update: ChatJoinRequest, bot: Bot):
    user_id = update.from_user.id
    chat_id = update.chat.id
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT student_id FROM academy_students WHERE telegram_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                # User is validated in academy_students
                try:
                    await update.approve()
                    # Optional: Send welcome DM
                    await bot.send_message(user_id, f"🎉 Ta demande pour rejoindre le groupe '{update.chat.title}' a été approuvée automatiquement !")
                    
                    from database import log_student_action
                    await log_student_action(row[0], 'GROUP_JOINED', f"A rejoint le groupe/dossier: {update.chat.title}")
                    
                except Exception as e:
                    print(f"Failed to approve join request: {e}")
            else:
                # Decline or ignore
                try:
                    await update.decline()
                    await bot.send_message(user_id, "❌ Ta demande d'adhésion a été refusée car ton compte n'est pas lié.\nVa sur le bot et clique sur Lier mon compte d'abord.")
                except Exception as e:
                    print(f"Failed to decline join request: {e}")

@router.callback_query(F.data.startswith("feedback_"))
async def handle_feedback(callback: CallbackQuery):
    feedback_type = callback.data.split("_")[1]
    
    if feedback_type == "easy":
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ شكراً لك! يسعدنا أن العملية كانت سهلة."
        )
    else:
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ نأسف لأنك واجهت صعوبة. سنعمل على تحسين النظام باستمرار."
        )
    await callback.answer("شكراً على تقييمك!")

@router.message(Command("test_message"))
async def cmd_test_message(message: Message):
    welcome_msg = (
        f"أهلاً بك Houssam في أكاديمية الباجي.\n\n"
        f"تم التحقق من هويتك بنجاح (رقم الطالب: 123456).\n"
        f"يمكنك الآن الوصول إلى جميع قنوات الأكاديمية والمجموعات الدراسية مباشرة عبر المجلد الرسمي الذي قمت بإضافته.\n\n"
        f"هل كانت عملية الدخول سهلة بالنسبة لك؟"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 نعم، كانت سهلة", callback_data="feedback_easy"),
            InlineKeyboardButton(text="👎 واجهت صعوبة", callback_data="feedback_hard")
        ]
    ])
    await message.answer(welcome_msg, reply_markup=kb)

from aiogram.types import WebAppInfo

@router.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "مرحباً بك في بوابة أكاديمية الباجي 👋\n\n"
        "للوصول إلى القنوات والمجموعات الخاصة بك، يجب عليك التحقق من هويتك أولاً.\n"
        "يرجى الضغط على الزر أدناه للبدء."
    )
    
    # Resolve WebApp URL
    domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    if domain:
        webapp_url = f"https://{domain}/link.html"
    else:
        # Fallback to WEBAPP_URL if defined, else use a default template
        base_url = os.getenv('WEBAPP_URL', 'https://telegram-dashboard-production.up.railway.app').rstrip('/')
        webapp_url = f"{base_url}/link.html"
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 بوابة التحقق (Mini App)", web_app=WebAppInfo(url=webapp_url))]
    ])
    await message.answer(welcome_text, reply_markup=kb)
