# ==========================================
# SINGLE-USE INVITE LINKS & GENDER SEGREGATION ENGINE
# ==========================================

async def generate_and_send_student_links(bot, telegram_id: int, student_data: dict, app=None) -> dict:
    """
    Génère des liens uniques (member_limit=1) selon le genre et les envoie à l'élève.
    """
    import database as db
    import logging
    _log = logging.getLogger('bot')
    
    settings = await db.get_group_settings()
    general_id = settings.get('general_channel_id')
    men_id = settings.get('men_group_id')
    women_id = settings.get('women_group_id')
    
    gender = (student_data.get('gender') or 'HOMME').upper()
    email = (student_data.get('email') or '').lower()
    first_name = student_data.get('first_name') or 'طالب العلم'
    
    links = {}
    
    # 1. Lien du Canal Général (si configuré)
    if general_id and bot:
        try:
            link_obj = await bot.create_chat_invite_link(
                chat_id=int(general_id) if str(general_id).lstrip('-').isdigit() else general_id,
                member_limit=1,
                name=f"General_{first_name}_{telegram_id}"[:32]
            )
            links['general'] = link_obj.invite_link
            await db.record_issued_link(telegram_id, email, 'general', str(general_id), link_obj.invite_link)
        except Exception as e:
            _log.error(f"[LINKS] Error creating general invite link: {e}")
            
    # 2. Lien du Groupe selon le Genre
    target_group_id = women_id if gender == 'FEMME' else men_id
    target_group_type = 'women' if gender == 'FEMME' else 'men'
    group_title_ar = "مجموعة الأخوات (نساء) 🧕" if gender == 'FEMME' else "مجموعة الإخوة (رجال) 🧔"
    
    if target_group_id and bot:
        try:
            link_obj = await bot.create_chat_invite_link(
                chat_id=int(target_group_id) if str(target_group_id).lstrip('-').isdigit() else target_group_id,
                member_limit=1,
                name=f"{target_group_type.capitalize()}_{first_name}_{telegram_id}"[:32]
            )
            links['group'] = link_obj.invite_link
            links['group_type'] = target_group_type
            await db.record_issued_link(telegram_id, email, target_group_type, str(target_group_id), link_obj.invite_link)
        except Exception as e:
            _log.error(f"[LINKS] Error creating {target_group_type} invite link: {e}")

    # 3. Envoi du message Telegram avec boutons
    if bot and (links.get('general') or links.get('group')):
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb_buttons = []
            if links.get('general'):
                kb_buttons.append([InlineKeyboardButton(text="📢 الانضمام للقناة العامة للدروس", url=links['general'])])
            if links.get('group'):
                kb_buttons.append([InlineKeyboardButton(text=f"💬 الانضمام إلى {group_title_ar}", url=links['group'])])
                
            reply_markup = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
            
            welcome_text = (
                f"🎉 <b>أهلاً بك يا {first_name} في أكاديمية الباجي!</b>\n\n"
                f"✅ تم تأكيد اشتراكك وتفعيل حسابك بنجاح.\n\n"
                f"🔒 <b>تنبيه أمني هام:</b> هذه الروابط مخصصة لك فقط (أحادية الاستخدام)، وتنتهي صلاحيتها فور استخدامك لها.\n\n"
                f"👇 اضغط على الأزرار أدناه للانضمام إلى مجموعاتك المقررة:"
            )
            
            await bot.send_message(
                chat_id=telegram_id,
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            _log.info(f"[LINKS] Sent unique invite links to {telegram_id} ({email})")
            await db.mark_pending_verification_processed(telegram_id, email)
        except Exception as e:
            _log.error(f"[LINKS] Error sending telegram message with links: {e}")
            
    return links

import asyncio

# --- DB TRANSCRIPTS HELPERS ---
async def load_lessons_from_db():
    import aiosqlite, json
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT lesson_data FROM course_transcripts") as cur:
            rows = await cur.fetchall()
    return [json.loads(r[0]) for r in rows]

async def update_static_json_cache():
    import json, os
    try:
        all_lessons = await load_lessons_from_db()
        dash_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'transcripts.json')
        with open(dash_path, 'w', encoding='utf-8') as f:
            json.dump(all_lessons, f, ensure_ascii=False)
    except Exception as e:
        import logging
        logging.error(f"Failed to update static JSON cache: {e}")

async def save_lesson_to_db(subject, lesson_num, lesson_data):
    import aiosqlite, json
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE course_transcripts SET lesson_data = ? WHERE subject = ? AND lesson_num = ?", 
            (json.dumps(lesson_data, ensure_ascii=False), subject, int(lesson_num)))
        await db.commit()
    await update_static_json_cache()

async def init_static_cache():
    import asyncio
    asyncio.create_task(update_static_json_cache())
# ------------------------------

import logging
import os
import json
import uuid
import re
import sys
import secrets
import signal
import aiosqlite
from aiohttp import web
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

import database as db
from config import TELEGRAM_BOT_TOKEN

from handlers.auth import router as auth_router
# ====== CSAT CALLBACK HANDLER ======
from aiogram import Router as _AiogramRouter
from aiogram.filters import Filter as _AiogramFilter

csat_router = _AiogramRouter()

class _CsatFilter(_AiogramFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data is not None and callback.data.startswith("csat_")

@csat_router.callback_query(_CsatFilter())
async def handle_csat_callback(callback: CallbackQuery):
    """Handles CSAT rating from students after ticket resolution."""
    try:
        # Expected format: csat_{ticket_id}_{score}
        parts = callback.data.split("_")
        if len(parts) < 3:
            await callback.answer()
            return
        
        ticket_id = parts[1]
        score = int(parts[2])
        
        import database as db
        
        # Save CSAT score to database
        try:
            from config import DATABASE_PATH
            import aiosqlite
            async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                # Try to save score - add column if not exists
                try:
                    await db_conn.execute(
                        "ALTER TABLE crm_tickets ADD COLUMN csat_score INTEGER DEFAULT NULL"
                    )
                    await db_conn.commit()
                except Exception:
                    pass  # Column already exists
                await db_conn.execute(
                    "UPDATE crm_tickets SET csat_score = ? WHERE id = ?",
                    (score, ticket_id)
                )
                await db_conn.commit()
        except Exception as db_err:
            print(f"[CSAT] DB error: {db_err}")
        
        # Build acknowledgement message
        stars = "\u2b50" * score
        if score <= 2:
            ack_text = f"{stars}\n\n\u0646\u0623\u0633\u0641 \u0644\u0639\u062f\u0645 \u0631\u0636\u0627\u0643\u0627\u0644\u062a\u0627\u0645! \u062a\u0645 \u0625\u0639\u0627\u062f\u0629 \u0641\u062a\u062d \u062a\u0630\u0643\u0631\u062a\u0643 \u0644\u0645\u062a\u0627\u0628\u0639\u0629 \u0623\u062d\u0633\u0646. \u0633\u064a\u062a\u0648\u0627\u0635\u0644 \u0645\u0639\u0643 \u0645\u0634\u0631\u0641 \u0622\u062e\u0631 \u0642\u0631\u064a\u0628\u0627\u064b."
            # Reopen ticket
            try:
                await db.update_crm_ticket_status(ticket_id, 'reopen')
            except Exception:
                pass
        elif score == 3:
            ack_text = f"{stars}\n\n\u0634\u0643\u0631\u0627\u064b \u0639\u0644\u0649 \u062a\u0642\u064a\u064a\u0645\u0643! \u0633\u0646\u0639\u0645\u0644 \u0639\u0644\u0649 \u062a\u062d\u0633\u064a\u0646 \u062e\u062f\u0645\u062a\u0646\u0627."
        else:
            ack_text = f"{stars}\n\n\u0634\u0643\u0631\u0627\u064b \u062c\u0632\u064a\u0644\u0627\u064b \u0639\u0644\u0649 \u062a\u0642\u064a\u064a\u0645\u0643 \u0627\u0644\u0631\u0627\u0626\u0639! \u064a\u0633\u0639\u062f\u0646\u0627 \u062e\u062f\u0645\u062a\u0643."
        
        # Edit message to remove buttons
        await callback.message.edit_text(
            f"\u2b50 \u062a\u0642\u064a\u064a\u0645\u0643: {stars}\n\n{ack_text}",
        )
        await callback.answer()
        
    except Exception as e:
        print(f"[CSAT] Handler error: {e}")
        await callback.answer()

# ===== END CSAT HANDLER =====







# Configuration du logging double (console et fichier bot.log)
INSTANCE_ID = str(uuid.uuid4())
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_file_path = os.path.join(os.path.dirname(__file__), "bot.log")
logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(log_file_path, encoding="utf-8")

    ]
)
logger = logging.getLogger("main")
logging.getLogger('aiosqlite').setLevel(logging.WARNING)  # Suppress DEBUG noise

# â”€â”€â”€ INSTANCE LOCK (anti-fantÃ´me) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PID_FILE = os.path.join(os.path.dirname(__file__), ".bot.pid")

def _kill_existing_instance():
    """Tue toute instance prÃ©cÃ©dente du bot avant de dÃ©marrer."""
    if not os.path.exists(PID_FILE):
        return
    try:
        with open(PID_FILE, "r") as f:
            old_pid = int(f.read().strip())
        if old_pid <= 1 or old_pid == os.getpid() or os.getenv("RAILWAY_ENVIRONMENT"):
            return
            
        if sys.platform == "win32":
            # Utilisation de taskkill sous Windows pour forcer l'arrÃªt de maniÃ¨re fiable
            import subprocess
            logger.warning(f"âš ï¸  Instance fantÃ´me dÃ©tectÃ©e (PID {old_pid}). ArrÃªt en cours...")
            subprocess.run(["taskkill", "/F", "/PID", str(old_pid)], capture_output=True)
        else:
            # VÃ©rifie si le processus tourne encore (Unix)
            os.kill(old_pid, 0)
            # Il tourne encore â†’ on le tue
            logger.warning(f"âš ï¸  Instance fantÃ´me dÃ©tectÃ©e (PID {old_pid}). ArrÃªt en cours...")
            os.kill(old_pid, signal.SIGTERM)
            import time; time.sleep(1)
            try:
                os.kill(old_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            logger.info(f"âœ… Instance prÃ©cÃ©dente (PID {old_pid}) arrÃªtÃ©e.")
    except (ValueError, ProcessLookupError, OSError):
        pass  # PID invalide, processus dÃ©jÃ  mort ou erreur OS (ex: WinError 87 sur Windows)
    except PermissionError:
        logger.warning("Permission refusÃ©e pour tuer l'ancienne instance.")

def _write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

def _remove_pid():
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass

_kill_existing_instance()
_write_pid()
import atexit
atexit.register(_remove_pid)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# â”€â”€â”€ AIOHTTP WEB SERVER & MINI-APP APIS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

DASHBOARD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard')

# â”€â”€â”€ MIDDLEWARE CORS (pour GitHub Pages â†’ API Serveo) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@web.middleware
async def cors_middleware(request, handler):
    """Autorise les requÃªtes cross-origin depuis GitHub Pages et autres origines."""
    # RÃ©pondre immÃ©diatement aux preflight OPTIONS
    if request.method == 'OPTIONS':
        return web.Response(
            status=204,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '86400',
            }
        )
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def handle_index(request):
    resp = web.FileResponse(os.path.join(DASHBOARD_DIR, 'index.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp

async def handle_interactive(request):
    resp = web.FileResponse(os.path.join(DASHBOARD_DIR, 'interactive.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp

async def handle_admin_mindmap(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'admin_mindmap.html'))

async def handle_course_slides(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'course_slides.html'))

async def handle_course_slides_css(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'course_slides.css'))

async def handle_course_slides_js(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'course_slides.js'))

async def handle_editor(request):
    print("============= handle_editor CALLED =============")
    f = os.path.join(DASHBOARD_DIR, 'editor.html')
    print(f"File path: {f}, exists: {os.path.exists(f)}")
    return web.FileResponse(f)

async def handle_support_app(request):
    resp = web.FileResponse(os.path.join(DASHBOARD_DIR, 'ask.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp

async def handle_support_css(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'support.css'))

async def handle_support_js(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'support.js'))

async def handle_admin(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'admin.html'))

async def handle_admin_bot(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'admin-bot.html'))

async def handle_admin_support(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'admin-support.html'))

async def handle_admin_css(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'admin.css'))

async def handle_admin_js(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'admin.js'))

async def handle_admin_late_js(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'admin-late.js'))


async def handle_logo_albaji_png(request):
    p = os.path.join(DASHBOARD_DIR, 'logo_albaji.png')
    if not os.path.exists(p):
        p = os.path.join(DASHBOARD_DIR, 'شعار الباجي.png')
    if not os.path.exists(p):
        p = os.path.join(DASHBOARD_DIR, 'logo.png')
    return web.FileResponse(p, headers={
        'Content-Type': 'image/png',
        'Cache-Control': 'public, max-age=31536000, immutable',
        'Access-Control-Allow-Origin': '*'
    })

async def handle_logo_albaji_svg(request):
    p = os.path.join(DASHBOARD_DIR, 'logo_albaji.svg')
    if not os.path.exists(p):
        p = os.path.join(DASHBOARD_DIR, 'Logo Baji vert.svg')
    if not os.path.exists(p):
        p = os.path.join(DASHBOARD_DIR, 'logo.svg')
    return web.FileResponse(p, headers={
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'public, max-age=31536000, immutable',
        'Access-Control-Allow-Origin': '*'
    })

async def handle_logo_png(request):
    return await handle_logo_albaji_png(request)
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'logo.png'))

async def handle_tuto_jpg(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'tuto.jpg'))

async def handle_dossiertelegram_jpg(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'dossiertelegram.jpg'))

async def handle_support(request):
    resp = web.FileResponse(os.path.join(DASHBOARD_DIR, 'ask.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp

async def handle_app(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'app.html'))

async def handle_search(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'search.html'))

async def handle_transcripts(request):
    try:
        lessons = await load_lessons_from_db()
        data = json.dumps(lessons, ensure_ascii=False)
        
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' in accept_encoding:
            import gzip
            compressed = gzip.compress(data.encode('utf-8'))
            return web.Response(
                body=compressed,
                content_type='application/json',
                headers={
                    'Content-Encoding': 'gzip',
                    'Content-Length': str(len(compressed))
                }
            )
        else:
            return web.Response(
                text=data,
                content_type='application/json'
            )
    except Exception as e:
        logger.error(f"Error serving transcripts: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_quran(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'quran_db.json'))


async def handle_quiz_journey(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'quiz_journey.html'))

async def handle_test(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'test.html'))

async def handle_reader(request):
    resp = web.FileResponse(os.path.join(DASHBOARD_DIR, 'reader.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp



# ==========================================
# BULK EMAIL ONBOARDING ENGINE (ANTI-SPAM 2s)
# ==========================================
email_dispatch_state = {
    "is_running": False,
    "total": 0,
    "sent": 0,
    "failed": 0,
    "current_student": "",
    "logs": []
}

async def send_single_onboarding_email(email, first_name, student_id, gender, step_prefix="auth"):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage
    import config as cfg
    
    if not cfg.SMTP_USER or not cfg.SMTP_PASSWORD:
        return True, "Simulated (No SMTP credentials configured yet)"
        
    try:
        gender_clean = (gender or 'HOMME').upper()
        is_female = gender_clean in ['FEMME', 'FEMALE', 'F', 'WOMAN', 'WOMEN']
        
        greeting = f"أهلاً بكِ يا طالبتنا العزيزة <b>{first_name}</b>" if is_female else f"أهلاً بك يا طالبنا العزيز <b>{first_name}</b>"
        group_title = "السنة الأولى نساء" if is_female else "السنة الأولى رجال"
        
        bot_username = cfg.MAIN_BOT_USERNAME or "alsirahquizz_bot"
        direct_tg_link = f"https://t.me/{bot_username}?start={step_prefix}_{student_id}"
        
        # Structure MIME standard sans pièce jointe externe
        msg_root = MIMEMultipart('related')
        msg_root['Subject'] = "الانضمام إلى المجموعة الرسمية - أكاديمية الباجي"
        msg_root['From'] = f"{cfg.SMTP_SENDER_NAME} <{cfg.SMTP_USER}>"
        msg_root['To'] = email
        
        msg_alternative = MIMEMultipart('alternative')
        msg_root.attach(msg_alternative)
        
        plain_text = f"مرحباً بك {first_name} في أكاديمية الباجي.\nرابط تفعيل حسابك والدخول للمجموعات: {direct_tg_link}"
        msg_alternative.attach(MIMEText(plain_text, 'plain', 'utf-8'))
        
        student_id_display = str(student_id).strip() if student_id and str(student_id).lower() != 'none' else '—'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>أكاديمية الباجي</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f0f4f3; margin: 0; padding: 14px 8px; color: #17262c; direction: rtl; text-align: right;">
            <div style="max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 20px; padding: 22px 18px; border-top: 5px solid #079176; box-shadow: 0 6px 25px rgba(12,74,60,0.06);">
                
                <!-- HEADER WITH LOGO -->
                <div style="text-align: center; margin-bottom: 12px;">
                    <img src="cid:albaji_logo" alt="شعار أكاديمية الباجي" width="110" style="max-width: 110px; height: auto; margin-bottom: 6px; display: inline-block; border: 0;">
                    <div>
                        <span style="background: rgba(7, 145, 118, 0.1); color: #0c4a3c; font-weight: 800; font-size: 12px; padding: 3px 14px; border-radius: 15px;">● رسالة التفعيل والانضمام الرسمية</span>
                    </div>
                </div>

                <!-- WELCOME GREETING & TEXT DIRECTEMENT COMPACT -->
                <div style="text-align: center; margin-bottom: 14px; line-height: 1.7;">
                    <h2 style="color: #0c4a3c; margin: 0 0 6px 0; font-size: 18px; font-weight: 900;">{greeting}</h2>
                    <p style="margin: 0 0 6px 0; color: #4a5568; font-size: 14px;">
                        يسعدنا ويشرفنا جداً انضمامك إلى <b>أكاديمية الباجي</b>! نحن فخورون وسعداء بأن تكون جزءاً من أسرتنا التعليمية المباركة.
                    </p>
                    <p style="margin: 0; color: #079176; font-size: 13.5px; font-weight: bold;">
                        تبقى لك خطوة واحدة وأخيرة لتتمكن من الانضمام إلى <b>قنوات الإعلانات الرسمية</b> و<b>منتدى النقاش والتدارس</b>:
                    </p>
                </div>
                
                <!-- BOUTON IMMÉDIATEMENT VISIBLE SANS SCROLLER -->
                <div style="text-align: center; margin: 12px 0 16px 0; background: linear-gradient(180deg, #edf7f4 0%, #e1f2ec 100%); padding: 16px 14px; border-radius: 16px; border: 1px dashed #079176;">
                    <p style="margin: 0 0 10px 0; font-weight: 800; color: #0c4a3c; font-size: 14px;">👇 اضغط هنا للانضمام إلى المجموعة الرسمية:</p>
                    <a href="{direct_tg_link}" style="background: linear-gradient(135deg, #079176 0%, #0c4a3c 100%); color: #ffffff !important; text-decoration: none; padding: 15px 30px; border-radius: 30px; font-weight: 900; font-size: 16px; display: inline-block; box-shadow: 0 6px 20px rgba(7, 145, 118, 0.3);">
                        تفعيل الحساب وإضافة المجلد (تيليجرام)
                    </a>
                </div>
                
                <!-- COMPACT DETAILS CARD -->
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 16px; margin: 12px 0;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <tr><td style="color: #64748b; padding: 4px 0;">• رقم الطالب:</td><td style="font-weight: bold; color: #079176; text-align: left; font-family: monospace; font-size: 15px;">{student_id_display}</td></tr>
                        <tr><td style="color: #64748b; padding: 4px 0;">• الشعبة والمجموعة:</td><td style="font-weight: bold; color: #1e293b; text-align: left;">{group_title}</td></tr>
                    </table>
                </div>
                
                <!-- FOOTER -->
                <p style="font-size: 11px; color: #94a3b8; text-align: center; margin-top: 14px; border-top: 1px solid #f1f5f9; padding-top: 10px; line-height: 1.5;">
                    أكاديمية الباجي • رسالة تأكيد رسمية للانضمام لمجموعات الدراسة.
                </p>
            </div>
        </body>
        </html>
        """
        msg_alternative.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # Attach image strictly with Content-ID (NO Content-Disposition, NO filename header!)
        logo_path = os.path.join(os.path.dirname(__file__), "dashboard", "logo_albaji.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(__file__), "dashboard", "شعار الباجي.png")
            
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                img_data = f.read()
            img = MIMEImage(img_data, _subtype='png')
            img.add_header('Content-ID', '<albaji_logo>')
            # NOTE: Absolutely do NOT set Content-Disposition or filename to prevent Gmail attachment paperclip icon
            msg_root.attach(img)
            
        server = smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=15)
        server.starttls()
        server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
        server.send_message(msg_root)
        server.quit()
        return True, "OK"
    except Exception as e:
        return False, str(e)

async def run_email_dispatcher_task(students_to_send):
    global email_dispatch_state
    import aiosqlite
    from config import DATABASE_PATH
    import asyncio
    from datetime import datetime
    
    email_dispatch_state["is_running"] = True
    email_dispatch_state["total"] = len(students_to_send)
    email_dispatch_state["sent"] = 0
    email_dispatch_state["failed"] = 0
    email_dispatch_state["logs"] = []
    
    for s in students_to_send:
        email = s.get('email', '').strip()
        first_name = s.get('first_name', '')
        sid = s.get('student_id', '')
        gender = s.get('gender', 'HOMME')
        
        email_dispatch_state["current_student"] = f"{first_name} ({email})"
        
        success, err = await send_single_onboarding_email(email, first_name, sid, gender, step_prefix="e1")
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if success:
            email_dispatch_state["sent"] += 1
            email_dispatch_state["logs"].append(f"[{now_str}] ✅ تم الإرسال بنجاح إلى: {email}")
            # Mark in DB
            try:
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    await db.execute("UPDATE academy_students SET email_sent = 1, email_sent_at = ? WHERE student_id = ?", (now_str, sid))
                    await db.commit()
            except Exception:
                pass
        else:
            email_dispatch_state["failed"] += 1
            email_dispatch_state["logs"].append(f"[{now_str}] ❌ فشل الإرسال إلى {email}: {err}")
            
        # Anti-spam delay between sends
        await asyncio.sleep(2.0)
        
    email_dispatch_state["is_running"] = False
    email_dispatch_state["current_student"] = "اكتمل الإرسال بنجاح ✅"


# ==========================================
# EMAIL PIXEL TRACKING & KPI ANALYTICS
# ==========================================
# 1x1 Transparent GIF Byte Data
TRANSPARENT_GIF_1X1 = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00,
    0x01, 0x00, 0x80, 0x00, 0x00, 0xff, 0xff, 0xff,
    0x00, 0x00, 0x00, 0x21, 0xf9, 0x04, 0x01, 0x00,
    0x00, 0x00, 0x00, 0x2c, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3b
])

async def api_track_open(request: web.Request):
    student_id = request.query.get('id')
    if student_id:
        try:
            import aiosqlite
            from config import DATABASE_PATH
            from datetime import datetime
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute(
                    "UPDATE academy_students SET email_opened_at = ? WHERE student_id = ? AND email_opened_at IS NULL",
                    (now_str, student_id)
                )
                await db.commit()
        except Exception as e:
            _log.error(f"[TRACK_OPEN] Error: {e}")
            
    return web.Response(
        body=TRANSPARENT_GIF_1X1,
        content_type='image/gif',
        headers={
            'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
            'Pragma': 'no-cache'
        }
    )

async def api_track_click(request: web.Request):
    """Méthode 2: Capture le clic immédiatement et ouvre Telegram via le protocole natif tg://."""
    student_id = request.query.get('id', '').strip()
    source = (request.query.get('src') or request.query.get('source') or 'email').lower().strip()
    
    import config as cfg
    bot_username = cfg.MAIN_BOT_USERNAME or "alsirahquizz_bot"
    tg_deep_link = f"tg://resolve?domain={bot_username}&start=auth_{student_id}" if student_id else f"tg://resolve?domain={bot_username}&start=link"
    https_tg_url = f"https://t.me/{bot_username}?start=auth_{student_id}" if student_id else f"https://t.me/{bot_username}?start=link"
    
    try:
        import aiosqlite
        from config import DATABASE_PATH
        from datetime import datetime
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ip = request.remote or request.headers.get('X-Forwarded-For', '')
        ua = request.headers.get('User-Agent', '')[:200]
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "INSERT INTO click_tracking (student_id, source, ip_address, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
                (student_id, source, ip, ua, now_str)
            )
            
            if student_id:
                if source in ['whatsapp', 'wa']:
                    await db.execute(
                        "UPDATE academy_students SET whatsapp_clicked_at = ?, last_click_source = ? WHERE student_id = ?",
                        (now_str, 'whatsapp', student_id)
                    )
                else:
                    await db.execute(
                        "UPDATE academy_students SET email_clicked_at = ?, last_click_source = ? WHERE student_id = ? AND email_clicked_at IS NULL",
                        (now_str, 'email', student_id)
                    )
            await db.commit()
    except Exception as e:
        _log.error(f"[TRACK_CLICK] Error: {e}")
        
    html_redirect = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>أكاديمية الباجي 🎓</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #fbf9f4; text-align: center; padding: 20px; box-sizing: border-box; }}
        .card {{ background: #ffffff; padding: 35px 25px; border-radius: 20px; box-shadow: 0 10px 30px rgba(12,74,60,0.08); max-width: 420px; width: 100%; border: 1px solid rgba(12,74,60,0.1); }}
        .btn {{ display: block; background: #0c4a3c; color: #ffffff !important; padding: 16px 24px; border-radius: 30px; text-decoration: none; font-weight: bold; font-size: 16px; margin: 15px 0 0 0; box-shadow: 0 4px 15px rgba(12,74,60,0.25); }}
    </style>
    <script>
        // Essai d'ouverture directe de l'application Telegram native
        window.location.href = "{tg_deep_link}";
        setTimeout(function() {{
            window.location.href = "{https_tg_url}";
        }}, 800);
    </script>
</head>
<body>
    <div class="card">
        <h2 style="color: #0c4a3c; margin: 0 0 10px 0; font-size: 22px;">أكاديمية الباجي 🎓</h2>
        <p style="color: #4b5563; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">جاري فتح تطبيق تليجرام لتفعيل حسابك الأكاديمي...</p>
        <a href="{tg_deep_link}" class="btn">🚀 فتح تطبيق تليجرام الآن</a>
        <a href="{https_tg_url}" style="display:inline-block; margin-top:15px; color:#079176; font-size:13px; text-decoration:none;">إذا لم يفتح التطبيق تلقائياً، اضغط هنا ➔</a>
    </div>
</body>
</html>"""
    return web.Response(text=html_redirect, content_type='text/html')


async def api_admin_gateway_home_stats(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # KPIs
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE excluded = 0 OR excluded IS NULL") as cur:
                total_students = (await cur.fetchone())['cnt']
                
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND telegram_id IS NOT NULL") as cur:
                linked_students = (await cur.fetchone())['cnt']
                
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND folder_clicked_at IS NOT NULL") as cur:
                in_groups = (await cur.fetchone())['cnt']
                
            async with db.execute("SELECT COUNT(*) as cnt FROM users u LEFT JOIN academy_students s ON s.telegram_id = u.telegram_id WHERE s.telegram_id IS NULL") as cur:
                ghosts = (await cur.fetchone())['cnt']

            # Funnel Data
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND (email_sent > 0 OR whatsapp_sent > 0)") as cur:
                contacted = (await cur.fetchone())['cnt']
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND bot_started_at IS NOT NULL") as cur:
                started_bot = (await cur.fetchone())['cnt']
                
            # Demographics
            async with db.execute("SELECT school_level, COUNT(*) as cnt FROM academy_students WHERE excluded = 0 OR excluded IS NULL GROUP BY school_level") as cur:
                levels = {str(r['school_level']): r['cnt'] for r in await cur.fetchall()}
            async with db.execute("SELECT gender, COUNT(*) as cnt FROM academy_students WHERE excluded = 0 OR excluded IS NULL GROUP BY gender") as cur:
                genders = {str(r['gender']): r['cnt'] for r in await cur.fetchall()}

            # Alerts
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND email_sent = 0 AND whatsapp_sent = 0") as cur:
                uncontacted = (await cur.fetchone())['cnt']
            
            # Ghosts from today
            async with db.execute("SELECT COUNT(*) as cnt FROM users u LEFT JOIN academy_students s ON s.telegram_id = u.telegram_id WHERE s.telegram_id IS NULL AND u.created_at >= date('now')") as cur:
                ghosts_today = (await cur.fetchone())['cnt']

            # Finances
            async with db.execute("SELECT payment_status, COUNT(*) as cnt FROM academy_students WHERE excluded = 0 OR excluded IS NULL GROUP BY payment_status") as cur:
                payments_raw = await cur.fetchall()
            finances = {"paid": 0, "unpaid": 0}
            for r in payments_raw:
                ps = str(r['payment_status'] or '').upper().strip()
                if ps in ['PAID', 'PAYE', 'مسدد']:
                    finances["paid"] += r['cnt']
                else:
                    finances["unpaid"] += r['cnt']

            return web.json_response({
                "success": True,
                "kpis": {
                    "total": total_students,
                    "linked": linked_students,
                    "groups": in_groups,
                    "ghosts": ghosts
                },
                "funnel": {
                    "imported": total_students,
                    "contacted": contacted,
                    "started_bot": started_bot,
                    "linked": linked_students,
                    "joined": in_groups
                },
                "finances": finances,
                "demographics": {
                    "levels": levels,
                    "genders": genders
                },
                "alerts": {
                    "uncontacted": uncontacted,
                    "ghosts_today": ghosts_today
                }
            })
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)})


async def api_admin_gateway_kpi(request: web.Request):
    try:
        import aiosqlite
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # 1. Total paid
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE payment_status = 'PAID' OR payment_status = 'PAYE'") as cur:
                total_paid = (await cur.fetchone())['cnt']
                
            # 2. Email funnel
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE email_sent = 1") as cur:
                email_sent = (await cur.fetchone())['cnt']
                
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE email_opened_at IS NOT NULL") as cur:
                email_opened = (await cur.fetchone())['cnt']
                
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE email_clicked_at IS NOT NULL") as cur:
                email_clicks = (await cur.fetchone())['cnt']
                
            # 3. WhatsApp funnel
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE whatsapp_sent = 1") as cur:
                wa_sent = (await cur.fetchone())['cnt']
                
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE whatsapp_clicked_at IS NOT NULL") as cur:
                wa_clicks = (await cur.fetchone())['cnt']
                
            # 4. Telegram Group conversions
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE telegram_id IS NOT NULL AND telegram_id != ''") as cur:
                telegram_linked = (await cur.fetchone())['cnt']
                
            # Joined directly via email
            async with db.execute("""
                SELECT COUNT(*) as cnt FROM academy_students 
                WHERE telegram_id IS NOT NULL AND telegram_id != '' 
                  AND (last_click_source = 'email' OR last_click_source IS NULL OR last_click_source = '')
            """) as cur:
                joined_via_email = (await cur.fetchone())['cnt']
                
            # Joined after WhatsApp follow-up
            async with db.execute("""
                SELECT COUNT(*) as cnt FROM academy_students 
                WHERE telegram_id IS NOT NULL AND telegram_id != '' 
                  AND (last_click_source = 'whatsapp' OR last_click_source = 'wa')
            """) as cur:
                joined_after_wa = (await cur.fetchone())['cnt']
                
            # 5. Overdue / Needs Follow-up (Paid but no telegram_id)
            async with db.execute("""
                SELECT student_id, first_name, last_name, email, phone, email_sent, email_sent_at, email_opened_at, email_clicked_at, 
                       whatsapp_sent, whatsapp_sent_at, whatsapp_clicked_at, created_at 
                FROM academy_students 
                WHERE (payment_status = 'PAID' OR payment_status = 'PAYE') 
                  AND (telegram_id IS NULL OR telegram_id = '')
                ORDER BY created_at DESC
            """) as cur:
                overdue_students = [dict(r) for r in await cur.fetchall()]
                
        open_rate = round((email_opened / email_sent * 100), 1) if email_sent > 0 else 0
        click_rate = round((email_clicks / email_sent * 100), 1) if email_sent > 0 else 0
        conversion_rate = round((telegram_linked / total_paid * 100), 1) if total_paid > 0 else 0
        wa_conversion_rate = round((joined_after_wa / wa_sent * 100), 1) if wa_sent > 0 else 0
        
        return web.json_response({
            "success": True,
            "kpi": {
                "total_paid": total_paid,
                "email_sent": email_sent,
                "email_opened": email_opened,
                "email_clicks": email_clicks,
                "wa_sent": wa_sent,
                "wa_clicks": wa_clicks,
                "telegram_linked": telegram_linked,
                "joined_via_email": joined_via_email,
                "joined_after_wa": joined_after_wa,
                "open_rate": open_rate,
                "click_rate": click_rate,
                "conversion_rate": conversion_rate,
                "wa_conversion_rate": wa_conversion_rate,
                "pending_count": len(overdue_students),
                "overdue_students": overdue_students
            }
        })
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_admin_send_bulk_emails(request: web.Request):
    global email_dispatch_state
    import aiosqlite
    from config import DATABASE_PATH
    import asyncio
    
    if email_dispatch_state["is_running"]:
        return web.json_response({"success": False, "error": "Un envoi est déjà en cours !"}, status=400)
        
    try:
        data = await request.json()
    except:
        data = {}
        
    action_type = data.get('action_type', 'email_1')
    target_ids = data.get('student_ids', [])
    
    if not target_ids:
        return web.json_response({"success": False, "error": "Aucun étudiant sélectionné."}, status=400)
        
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            placeholders = ','.join('?' for _ in target_ids)
            query = f"SELECT * FROM academy_students WHERE student_id IN ({placeholders})"
            async with db.execute(query, tuple(target_ids)) as cur:
                rows = await cur.fetchall()
                students = [dict(r) for r in rows]
                
        if not students:
            return web.json_response({"success": True, "count": 0, "message": "Aucun étudiant valide trouvé."})
            
        # Start background task
        asyncio.create_task(run_email_dispatcher_task(students, action_type))
        
        return web.json_response({"success": True, "count": len(students), "message": f"Envoi de {len(students)} emails en tâche de fond (Pause de 2s)."})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_admin_email_dispatch_status(request: web.Request):
    global email_dispatch_state
    return web.json_response({"success": True, "state": email_dispatch_state})


async def api_admin_gateway_export_template(request: web.Request):
    """Génère un fichier CSV modèle vierge avec 2 exemples pour importer de nouveaux étudiants."""
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['first_name', 'last_name', 'email', 'phone', 'gender', 'student_id', 'payment_status', 'year'])
    writer.writerow(['حسام', 'بودو', 'h.bouddou@gmail.com', '+33668959911', 'HOMME', '104820', 'PAID', '1'])
    writer.writerow(['مريم', 'العلمي', 'maryam.test@gmail.com', '+33600000000', 'FEMME', '104821', 'PAID', '1'])
    
    csv_data = output.getvalue().encode('utf-8-sig')
    return web.Response(
        body=csv_data,
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="albadr_students_template.csv"'}
    )

async def api_admin_gateway_export_all_students(request: web.Request):
    """Exporte TOUS les étudiants réels de la base de données avec leurs statuts réels en direct."""
    import io, csv, aiosqlite
    from config import DATABASE_PATH
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['student_id', 'first_name', 'last_name', 'email', 'phone', 'gender', 'payment_status', 'year', 'telegram_id', 'telegram_username', 'email_sent', 'email_opened_at', 'created_at'])
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM academy_students ORDER BY created_at DESC") as cur:
            rows = await cur.fetchall()
            for r in rows:
                d = dict(r)
                writer.writerow([
                    d.get('student_id', ''),
                    d.get('first_name', ''),
                    d.get('last_name', ''),
                    d.get('email', ''),
                    d.get('phone', ''),
                    d.get('gender', 'HOMME'),
                    d.get('payment_status', 'PAID'),
                    d.get('year', '1'),
                    d.get('telegram_id', ''),
                    d.get('telegram_username', ''),
                    d.get('email_sent', 0),
                    d.get('email_opened_at', ''),
                    d.get('created_at', '')
                ])
                
    csv_data = output.getvalue().encode('utf-8-sig')
    return web.Response(
        body=csv_data,
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="albadr_students_database_export.csv"'}
    )

async def handle_admin_gateway(request):
    resp = web.FileResponse(os.path.join(DASHBOARD_DIR, 'admin_gateway.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp

async def api_admin_gateway_stats(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM academy_students WHERE payment_status = 'PAID' AND (excluded = 0 OR excluded IS NULL)") as cur:
                total_paid = (await cur.fetchone())[0]
            if total_paid == 0:
                async with db.execute("SELECT COUNT(*) FROM academy_students WHERE excluded = 0 OR excluded IS NULL") as cur:
                    total_paid = (await cur.fetchone())[0]
                    
            async with db.execute("SELECT COUNT(*) FROM academy_students WHERE email_sent = 1 AND (excluded = 0 OR excluded IS NULL)") as cur:
                email_sent = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM academy_students WHERE email_opened_at IS NOT NULL AND (excluded = 0 OR excluded IS NULL)") as cur:
                email_opened = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND (telegram_id IS NOT NULL)") as cur:
                bot_linked = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(DISTINCT l.student_id) FROM student_logs l JOIN academy_students s ON l.student_id = s.student_id WHERE l.action_type IN ('FOLDER_CLICKED', 'APP_OPENED', 'TUTO_OPENED') AND (s.excluded = 0 OR s.excluded IS NULL)") as cur:
                folder_clicked = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM academy_students WHERE group_joined = 1 AND (excluded = 0 OR excluded IS NULL)") as cur:
                group_joined = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM academy_students WHERE whatsapp_sent = 1 AND (excluded = 0 OR excluded IS NULL)") as cur:
                wa_sent = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM academy_students WHERE whatsapp_sent = 1 AND group_joined = 1 AND (excluded = 0 OR excluded IS NULL)") as cur:
                wa_converted = (await cur.fetchone())[0]
                
            async with db.execute("SELECT value FROM settings WHERE key = 'night_patrol_enabled'") as cur:
                row = await cur.fetchone()
                patrol_enabled = row[0] == 'true' if row else False
                
        return web.json_response({
            'success': True,
            'stats': {
                'total_paid': total_paid,
                'email_sent': email_sent,
                'email_opened': email_opened,
                'bot_linked': bot_linked,
                'folder_clicked': folder_clicked,
                'group_joined': group_joined,
                'wa_sent': wa_sent,
                'wa_converted': wa_converted,
                'patrol_enabled': patrol_enabled
            }
        })
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})


async def api_admin_gateway_delete_source(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        source_file = data.get('source_file')
        if not source_file:
            return web.json_response({"success": False, "error": "No source_file provided"})
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("DELETE FROM academy_students WHERE source_file = ?", (source_file,)) as cur:
                deleted = cur.rowcount
            await db.commit()
            
        return web.json_response({"success": True, "deleted": deleted})
    except Exception as e:
        import logging
        logging.getLogger('main').error(f"Error in delete_source: {e}", exc_info=True)
        return web.json_response({"success": False, "error": str(e)})


async def api_admin_gateway_toggle_exclude(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        student_id = data.get('student_id')
        excluded = int(data.get('excluded', 1))
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("UPDATE academy_students SET excluded = ? WHERE student_id = ?", (excluded, student_id))
            await db.commit()
        return web.json_response({"success": True})
    except Exception as e:
        import logging
        logging.getLogger('main').error(f"Error in toggle_exclude: {e}")
        return web.json_response({"success": False, "error": str(e)})


async def api_admin_gateway_bulk_action(request: web.Request):
    import aiosqlite
    import datetime
    import logging
    import re
    from config import DATABASE_PATH
    _log = logging.getLogger('main')
    try:
        data = await request.json()
        action = data.get('action')
        student_ids = data.get('student_ids', [])
        subject = data.get('subject') or "رسالة من أكاديمية الباجي"
        message_template = data.get('message', '').strip()
        
        if not student_ids:
            return web.json_response({"success": False, "error": "Aucun étudiant sélectionné"})
        if not message_template and action != 'whatsapp':
            return web.json_response({"success": False, "error": "Le message est vide"})
            
        bot = request.app.get('bot')
        now_str = datetime.datetime.utcnow().isoformat()
        
        sent_count = 0
        not_linked_count = 0
        errors = []
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            for sid in student_ids:
                async with db.execute("SELECT * FROM academy_students WHERE student_id = ?", (sid,)) as cur:
                    student = await cur.fetchone()
                if not student:
                    continue
                    
                fname = student['first_name'] or ''
                lname = student['last_name'] or ''
                name = f"{fname} {lname}".strip() or "طالب العلم"
                
                # Replace variables in message
                msg_text = message_template.replace('{الاسم}', name).replace('{prenom}', fname).replace('{nom}', lname).replace('{name}', name)
                if '{token}' in msg_text:
                    token = student.get('magic_token') or student.get('student_id')
                    msg_text = msg_text.replace('{token}', str(token))
                
                if action == 'telegram':
                    tid = student['telegram_id']
                    if tid and bot:
                        try:
                            await bot.send_message(chat_id=int(tid), text=msg_text)
                            sent_count += 1
                        except Exception as ex:
                            _log.error(f"Error sending bulk TG message to {tid}: {ex}")
                            errors.append(str(ex))
                    else:
                        not_linked_count += 1
                elif action == 'sms':
                    phone_raw = student['phone'] or ''
                    phone = re.sub(r'\D', '', phone_raw)
                    if phone.startswith('0'): phone = '212' + phone[1:]
                    if phone:
                        await db.execute(
                            "INSERT INTO sms_queue (student_id, phone, message, status, created_at) VALUES (?, ?, ?, 'PENDING', ?)",
                            (sid, phone, msg_text, now_str)
                        )
                        sent_count += 1
                    else:
                        errors.append(f"Student {sid} has no phone")
                elif action == 'email':
                    em = student['email']
                    if em:
                        try:
                            import config as cfg
                            if cfg.SMTP_USER and cfg.SMTP_PASSWORD:
                                import smtplib
                                from email.mime.multipart import MIMEMultipart
                                from email.mime.text import MIMEText
                                msg_root = MIMEMultipart('alternative')
                                msg_root['Subject'] = subject
                                msg_root['From'] = f"{getattr(cfg, 'SMTP_SENDER_NAME', 'Académie')} <{cfg.SMTP_USER}>"
                                msg_root['To'] = em
                                msg_root.attach(MIMEText(msg_text, 'plain', 'utf-8'))
                                server = smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=10)
                                server.starttls()
                                server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
                                server.send_message(msg_root)
                                server.quit()
                            sent_count += 1
                            await db.execute("UPDATE academy_students SET email_sent = COALESCE(email_sent, 0) + 1, email_sent_at = ? WHERE student_id = ?", (now_str, sid))
                        except Exception as em_err:
                            _log.error(f"Error sending bulk email to {em}: {em_err}")
                            errors.append(str(em_err))
                elif action == 'whatsapp':
                    sent_count += 1
                    await db.execute("UPDATE academy_students SET whatsapp_sent = COALESCE(whatsapp_sent, 0) + 1, whatsapp_sent_at = ? WHERE student_id = ?", (now_str, sid))
            
            await db.commit()
            
        return web.json_response({
            "success": True,
            "sent": sent_count,
            "not_linked": not_linked_count,
            "count": len(student_ids),
            "errors": errors[:5]
        })
    except Exception as e:
        import logging
        logging.getLogger('main').error(f"Error in bulk_action: {e}")
        return web.json_response({"success": False, "error": str(e)})

async def api_admin_gateway_students(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT s.student_id, s.academic_id, s.first_name, s.last_name, s.email, s.telegram_id, s.telegram_username,
                       s.year, s.gender, s.dob, s.source, s.source_file, s.phone, s.created_at, s.payment_status,
                       s.profession, s.country, s.nationality, s.arabic_level, s.school_level,
                       s.team, s.comments, s.appel_1, s.appel_2, s.appel_3,
                       s.email_sent, s.email_sent_at, s.email_opened_at, s.email_clicked_at,
                       s.whatsapp_sent, s.whatsapp_sent_at, s.whatsapp_clicked_at, s.sms_sent, s.sms_sent_at, s.last_click_source,
                       s.group_joined, s.joined_at, s.folder_clicked_at, s.bot_started_at, s.excluded,
                       s.last_onboarding_step, s.last_onboarding_at, s.last_onboarding_detail,
                       u.first_name as tg_first_name, u.last_name as tg_last_name, s.magic_token
                FROM academy_students s
                LEFT JOIN users u ON u.telegram_id = s.telegram_id
                ORDER BY s.created_at DESC, s.first_name ASC
            """) as cur:
                students = [dict(row) for row in await cur.fetchall()]
        import config as cfg
        bot_user = getattr(cfg, 'MAIN_BOT_USERNAME', 'alsirahquizz_bot') or 'alsirahquizz_bot'
        return web.json_response({'success': True, 'students': students, 'bot_username': bot_user})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})



async def api_admin_gateway_ghost_visitors(request: web.Request):
    """Returns users who visited/started the bot, filtered by linked or unlinked status, along with latest funnel action and student details"""
    import aiosqlite
    from config import DATABASE_PATH
    try:
        status = request.query.get('status', 'unlinked').strip().lower()
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            if status == 'linked':
                # Return users who ARE linked to an academy student record
                async with db.execute("""
                    SELECT 
                        u.telegram_id,
                        u.first_name,
                        u.last_name,
                        u.username,
                        u.created_at,
                        s.student_id,
                        s.first_name as student_first_name,
                        s.last_name as student_last_name,
                        s.email as student_email,
                        s.gender as student_gender,
                        s.last_onboarding_step,
                        s.last_onboarding_at,
                        s.last_onboarding_detail,
                        (SELECT action_type FROM student_logs WHERE telegram_id = u.telegram_id OR student_id = s.student_id ORDER BY id DESC LIMIT 1) as last_action,
                        (SELECT description FROM student_logs WHERE telegram_id = u.telegram_id OR student_id = s.student_id ORDER BY id DESC LIMIT 1) as last_desc,
                        (SELECT timestamp FROM student_logs WHERE telegram_id = u.telegram_id OR student_id = s.student_id ORDER BY id DESC LIMIT 1) as last_time
                    FROM users u
                    JOIN academy_students s ON s.telegram_id = u.telegram_id
                    ORDER BY COALESCE((SELECT timestamp FROM student_logs WHERE telegram_id = u.telegram_id ORDER BY id DESC LIMIT 1), u.created_at) DESC
                    LIMIT 300
                """) as cur:
                    rows = [dict(r) for r in await cur.fetchall()]
            else:
                # Default: Return unlinked users (ghosts)
                async with db.execute("""
                    SELECT 
                        u.telegram_id,
                        u.first_name,
                        u.last_name,
                        u.username,
                        u.created_at,
                        NULL as student_id,
                        NULL as student_first_name,
                        NULL as student_last_name,
                        NULL as student_email,
                        NULL as student_gender,
                        NULL as last_onboarding_step,
                        NULL as last_onboarding_at,
                        NULL as last_onboarding_detail,
                        (SELECT action_type FROM student_logs WHERE telegram_id = u.telegram_id ORDER BY id DESC LIMIT 1) as last_action,
                        (SELECT description FROM student_logs WHERE telegram_id = u.telegram_id ORDER BY id DESC LIMIT 1) as last_desc,
                        (SELECT timestamp FROM student_logs WHERE telegram_id = u.telegram_id ORDER BY id DESC LIMIT 1) as last_time
                    FROM users u
                    LEFT JOIN academy_students s ON s.telegram_id = u.telegram_id
                    WHERE s.telegram_id IS NULL
                    ORDER BY COALESCE((SELECT timestamp FROM student_logs WHERE telegram_id = u.telegram_id ORDER BY id DESC LIMIT 1), u.created_at) DESC
                    LIMIT 300
                """) as cur:
                    rows = [dict(r) for r in await cur.fetchall()]
        return web.json_response({'success': True, 'visitors': rows, 'count': len(rows), 'status': status})
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_student_timeline(request: web.Request):
    student_id = request.query.get('id')
    tid = request.query.get('tid')
    import aiosqlite
    from config import DATABASE_PATH
    try:
        timeline = []
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            if tid and tid != 'null' and tid != 'undefined':
                async with db.execute("SELECT id, action_type, description, timestamp FROM student_logs WHERE telegram_id = ? OR student_id = ? ORDER BY id DESC LIMIT 100", (tid, student_id)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'student_logs'
                        timeline.append(r)
                async with db.execute("SELECT id, message, status, timestamp FROM gateway_sos WHERE telegram_id = ? OR student_id = ? ORDER BY id DESC", (tid, student_id)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'gateway_sos'
                        timeline.append(r)
                async with db.execute("SELECT id, message, status, timestamp, theme FROM crm_tickets WHERE telegram_id = ? ORDER BY id DESC", (tid,)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'crm_tickets'
                        timeline.append(r)
            else:
                async with db.execute("SELECT id, action_type, description, timestamp FROM student_logs WHERE student_id = ? ORDER BY id DESC LIMIT 100", (student_id,)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'student_logs'
                        timeline.append(r)
                async with db.execute("SELECT id, message, status, timestamp FROM gateway_sos WHERE student_id = ? ORDER BY id DESC", (student_id,)) as cur:
                    for row in await cur.fetchall():
                        r = dict(row)
                        r['source_table'] = 'gateway_sos'
                        timeline.append(r)
        
        timeline.sort(key=lambda x: x['timestamp'], reverse=True)
        return web.json_response({'success': True, 'timeline': timeline})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_add_crm_note(request: web.Request):
    data = await request.json()
    student_id = data.get('student_id') or 0
    tid = data.get('telegram_id')
    ctype = data.get('type', 'AUTRE')
    tag = data.get('tag', 'INFO')
    note = data.get('note', '')
    admin_name = data.get('admin_name', 'Admin')
    
    if not note:
        return web.json_response({'success': False, 'error': 'Note is empty'})
        
    description = f"[{ctype}] [{tag}] [بواسطة: {admin_name}] {note}"
    import database as db
    try:
        await db.log_student_action(student_id, "CRM_NOTE", description, telegram_id=tid)
        
        # If it's a Marketing note, update the main marketing_notes column
        if ctype == 'Marketing':
            import aiosqlite
            async with aiosqlite.connect(db.DATABASE_PATH) as conn:
                await conn.execute("UPDATE academy_students SET marketing_notes = ? WHERE student_id = ?", (note, student_id))
                await conn.commit()
                
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_logs(request: web.Request):
    student_id = request.query.get('id')
    tid = request.query.get('tid')
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            if tid and tid != 'null' and tid != 'undefined':
                async with db.execute("SELECT action_type, description, timestamp, telegram_id, telegram_name, telegram_username FROM student_logs WHERE telegram_id = ? OR student_id = ? ORDER BY id DESC LIMIT 50", (tid, student_id)) as cur:
                    logs = [dict(row) for row in await cur.fetchall()]
            else:
                async with db.execute("SELECT action_type, description, timestamp, telegram_id, telegram_name, telegram_username FROM student_logs WHERE student_id = ? ORDER BY id DESC LIMIT 50", (student_id,)) as cur:
                    logs = [dict(row) for row in await cur.fetchall()]
        return web.json_response({'success': True, 'logs': logs})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_logs_all(request: web.Request):
    """Return all recent student logs joined with student name and Telegram name"""
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT sl.action_type, sl.description, sl.timestamp, sl.telegram_id, sl.telegram_name, sl.telegram_username,
                       COALESCE(s.first_name, 'ID:'||sl.student_id) as first_name,
                       u.first_name as tg_first_name, u.last_name as tg_last_name, s.magic_token, u.username as tg_username,
                       sl.student_id
                FROM student_logs sl
                LEFT JOIN academy_students s ON s.student_id = sl.student_id
                LEFT JOIN users u ON u.telegram_id = sl.telegram_id
                ORDER BY sl.id DESC LIMIT 100
            """) as cur:
                logs = [dict(row) for row in await cur.fetchall()]
        return web.json_response({'success': True, 'logs': logs})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})


async def api_admin_gateway_check_member(request: web.Request):
    telegram_id = request.query.get('telegram_id')
    if not telegram_id:
        return web.json_response({'success': False, 'error': 'Missing telegram_id'})
    try:
        bot = request.app['bot']
        from config import ACADEMY_GROUP_ID
        member = await bot.get_chat_member(chat_id=ACADEMY_GROUP_ID, user_id=int(telegram_id))
        has_joined = member.status in ['creator', 'administrator', 'member', 'restricted']
        return web.json_response({'success': True, 'status': member.status, 'has_joined': has_joined})
    except Exception as e:
        return web.json_response({'success': True, 'status': 'left', 'has_joined': False, 'debug_error': str(e)})

async def api_admin_gateway_add_student(request: web.Request):
    try:
        import aiosqlite
        from config import DATABASE_PATH
        from datetime import datetime
        data = await request.json()
        email = data.get('email', '').strip().lower()
        dob = data.get('dob', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        student_id = data.get('student_id', '').strip()
        phone = data.get('phone', '').strip()

        if not email or not dob:
            return web.json_response({'success': False, 'error': 'L\'email et la date de naissance sont requis.'})

        now_str = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT student_id FROM academy_students WHERE email = ?", (email,)) as cur:
                exists = await cur.fetchone()
            if exists:
                await db.execute("""
                    UPDATE academy_students
                    SET dob = ?, first_name = ?, last_name = ?, phone = ?, source = ?
                    WHERE email = ?
                """, (dob, first_name, last_name, phone, 'manuel', email))
            else:
                if student_id:
                    await db.execute("""
                        INSERT INTO academy_students (student_id, email, dob, first_name, last_name, phone, year, gender, source, magic_token, created_at, payment_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (student_id, email, dob, first_name, last_name, phone, '1', 'homme', 'manuel', secrets.token_urlsafe(8), now_str, 'PAID'))
                else:
                    await db.execute("""
                        INSERT INTO academy_students (email, dob, first_name, last_name, phone, year, gender, source, magic_token, created_at, payment_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (email, dob, first_name, last_name, phone, '1', 'homme', 'manuel', secrets.token_urlsafe(8), now_str, 'PAID'))
            await db.commit()
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})


async def api_admin_gateway_archive_student(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        student_id = data.get('student_id')
        reason = data.get('reason', 'Non specifie')
        admin_name = data.get('admin_name', 'Admin')
        
        if not student_id:
            return web.json_response({'success': False, 'error': 'ID etudiant manquant'})
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Check if student exists
            async with db.execute("SELECT first_name FROM academy_students WHERE student_id = ?", (student_id,)) as cur:
                if not await cur.fetchone():
                    return web.json_response({'success': False, 'error': 'Etudiant introuvable'})
            
            # Archive
            await db.execute("UPDATE academy_students SET excluded = 1 WHERE student_id = ?", (student_id,))
            
            # Add CRM Note
            note_text = f"[ARCHIVÉ] L'étudiant a été archivé/exclu.\nRaison : {reason}"
            await db.execute(
                "INSERT INTO student_logs (student_id, action_type, description, telegram_name) VALUES (?, ?, ?, ?)",
                (student_id, "CRM_NOTE", f"[بواسطة: {admin_name}] [نوع: SYSTEM]\n{note_text}", "Admin")
            )
            await db.commit()
            
        return web.json_response({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})


async def api_admin_gateway_import_students(request: web.Request):
    try:
        import aiosqlite
        import io
        import csv
        import hashlib
        from config import DATABASE_PATH
        
        reader = await request.multipart()
        field = await reader.next()
        if not field:
            return web.json_response({'success': False, 'error': 'لم يتم العثور على أي ملف مرفوع'})
        
        filename = (field.filename or '').lower()
        file_data = await field.read()
        
        raw_rows = []
        
        # 1. Extraction from XLSX or CSV
        if file_data.startswith(b'PK') or filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.xlsm'):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(file_data), data_only=True)
            sheet = wb.active
            for r in sheet.iter_rows(values_only=True):
                if any(r):
                    raw_rows.append([str(c).strip() if c is not None else '' for c in r])
        else:
            try:
                text_content = file_data.decode('utf-8-sig')
            except Exception:
                try:
                    text_content = file_data.decode('utf-8')
                except Exception:
                    text_content = file_data.decode('latin-1')
            
            lines = [l for l in text_content.splitlines() if l.strip()]
            if lines:
                delimiter = ';' if ';' in lines[0] and ',' not in lines[0] else ','
                if '\t' in lines[0]:
                    delimiter = '\t'
                csv_reader = csv.reader(io.StringIO(text_content), delimiter=delimiter)
                for r in csv_reader:
                    if any(r):
                        raw_rows.append([str(c).strip() for c in r])
                        
        if not raw_rows:
            return web.json_response({'success': False, 'error': 'الملف فارغ'})
            
        imported = 0
        async with aiosqlite.connect(DATABASE_PATH) as db:
            for row in raw_rows:
                # Find the email cell anywhere in the row

                student_id = str(row[0]).strip() if len(row) > 0 else ''
                first_name = str(row[2]).strip() if len(row) > 2 else ''
                email = str(row[3]).strip().lower() if len(row) > 3 else ''
                
                if not email or '@' not in email or email in ['email', 'بريد']:
                    continue
                    
                phone = str(row[4]).strip() if len(row) > 4 else ''
                year = str(row[5]).strip() if len(row) > 5 else '1'
                
                gender_raw = str(row[6]).upper().strip() if len(row) > 6 else ''
                gender = 'HOMME'
                if gender_raw in ["FEMME", "FEMALE", "FILLE", "F", "أنثى"]: gender = 'FEMME'
                elif gender_raw in ["HOMME", "MALE", "GARCON", "M", "ذكر"]: gender = 'HOMME'
                
                # DETECTION BULLETPROOF DU PAIEMENT
                # REGLE D'OR: tester UNPAID EN PREMIER
                # car 'مسدد' (paid) est une sous-chaine de 'غير مسدد' (unpaid) !
                def _clean(v):
                    import unicodedata as _ud
                    s = _ud.normalize('NFKC', str(v or '').strip())
                    for c in ['\u200f','\u200e','\u200b','\u200c','\u200d','\ufeff']:
                        s = s.replace(c, '')
                    return s.strip()

                _UNPAID = ['غير مسدد', 'UNPAID', 'NON PAYE', 'NON PAYÉ', 'غير مدفوع']
                _PAID   = ['مسدد', 'مدفوع', 'PAID', 'PAYÉ', 'PAYE', 'OUI', 'YES', 'VALIDE', 'CONFIRME', '1']
                _cells  = [_clean(c) for c in row]

                payment_status = 'UNPAID'  # defaut = non paye
                # On cherche uniquement dans la colonne H (index 7)
                if len(_cells) > 7:
                    cell_h = _cells[7]
                    if 'معفي' in cell_h:
                        payment_status = 'معفي'
                    else:
                        _found_unpaid = False
                        for _w in _UNPAID:
                            if _w in cell_h:
                                payment_status = 'UNPAID'
                                _found_unpaid = True
                                break
                        if not _found_unpaid:
                            for _w in _PAID:
                                # Attention: 'مسدد' est dans 'غير مسدد', mais vu qu'on a check _UNPAID avant,
                                # on est sûr que si 'مسدد' est trouvé, ce n'est pas 'غير مسدد'
                                if _w in cell_h:
                                    payment_status = 'PAID'
                                    break
                
                # DEBUG TEMPORAIRE - voir dans les logs Railway exactement ce que contient col H
                _cell_h_raw = row[7] if len(row) > 7 else 'COLONNE_H_MANQUANTE'
                import logging as _log_tmp
                _log_tmp.warning(f'[PAY] {email} | H={repr(str(row[7] if len(row)>7 else ""))[:40]} | {payment_status}')
                
                country = str(row[8]).strip() if len(row) > 8 else ''
                dob = str(row[9]).strip() if len(row) > 9 else ''

                school_level = str(row[12]).strip() if len(row) > 12 else ''
                created_at_val = str(row[13]).strip() if len(row) > 13 else ''
                profession = str(row[14]).strip() if len(row) > 14 else ''
                last_name = str(row[15]).strip() if len(row) > 15 else ''
                nationality = str(row[16]).strip() if len(row) > 16 else ''
                arabic_level = str(row[17]).strip() if len(row) > 17 else ''
                
                if not student_id:
                    import hashlib
                    student_id = str(int(hashlib.md5(email.encode()).hexdigest()[:6], 16))[:6]

                    
                async with db.execute("SELECT student_id FROM academy_students WHERE LOWER(email) = ? OR student_id = ?", (email, student_id)) as cur:
                    exists = await cur.fetchone()
                    
                if exists:
                    original_file_name = field.filename if field.filename else 'Fichier Excel'
                    await db.execute("""
                        UPDATE academy_students 
                        SET first_name = ?, last_name = ?, phone = ?, gender = ?, payment_status = ?, dob = ?, year = ?, profession = ?, country = ?, nationality = ?, arabic_level = ?, school_level = ?, created_at = COALESCE(NULLIF(?, ''), created_at), source = 'excel', source_file = ?
                        WHERE LOWER(email) = ? OR student_id = ?
                    """, (first_name, last_name, phone, gender, payment_status, dob, year, profession, country, nationality, arabic_level, school_level, created_at_val, original_file_name, email, student_id))
                else:
                    original_file_name = field.filename if field.filename else 'Fichier Excel'
                    await db.execute("""
                        INSERT INTO academy_students (student_id, first_name, last_name, email, phone, gender, payment_status, dob, year, profession, country, nationality, arabic_level, school_level, source, source_file, magic_token, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'excel', ?, ?, 1, COALESCE(NULLIF(?, ''), datetime('now')))
                    """, (student_id, first_name, last_name, email, phone, gender, payment_status, dob, year, profession, country, nationality, arabic_level, school_level, original_file_name, secrets.token_urlsafe(8), created_at_val))
                    
                imported += 1
            
            # Log the import
            await db.execute("""
                CREATE TABLE IF NOT EXISTS import_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_name TEXT,
                    filename TEXT,
                    imported_count INTEGER,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            admin_name = request.query.get('admin', 'Admin inconnu')
            await db.execute("INSERT INTO import_logs (admin_name, filename, imported_count) VALUES (?, ?, ?)", (admin_name, filename, imported))
            
            await db.commit()
            
        return web.json_response({'success': True, 'count': imported})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_import_logs(request: web.Request):
    try:
        import aiosqlite
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("""
                CREATE TABLE IF NOT EXISTS import_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_name TEXT,
                    filename TEXT,
                    imported_count INTEGER,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            async with db.execute("SELECT * FROM import_logs ORDER BY id DESC LIMIT 100") as cur:
                logs = [dict(row) for row in await cur.fetchall()]
        return web.json_response({'success': True, 'logs': logs})
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_sync_sheets(request: web.Request):
    try:
        from sync_sheets import run_google_sheets_sync
        from config import GOOGLE_SHEET_ID
        
        data = await request.json()
        sheet_id = data.get('sheet_id') or GOOGLE_SHEET_ID
        
        if not sheet_id:
            return web.json_response({'success': False, 'error': "L'ID de la Google Sheet n'a pas été fourni ou configuré."})
            
        imported, new_count, last_new = await run_google_sheets_sync(sheet_id)
        return web.json_response({'success': True, 'count': imported})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_purge_sheets(request: web.Request):
    try:
        import aiosqlite
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DELETE FROM academy_students WHERE source='google_sheets'")
            deleted = db.total_changes
            await db.commit()
        return web.json_response({'success': True, 'count': deleted})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_export_sheets(request: web.Request):
    try:
        from sync_sheets import export_students_to_sheets
        from config import GOOGLE_SHEET_ID
        
        data = await request.json()
        sheet_id = data.get('sheet_id') or GOOGLE_SHEET_ID
        
        if not sheet_id:
            return web.json_response({'success': False, 'error': "L'ID de la Google Sheet n'a pas été fourni ou configuré."})
            
        exported = await export_students_to_sheets(sheet_id)
        return web.json_response({'success': True, 'count': exported})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_settings(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        key = data.get('key')
        value = data.get('value')
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
            await db.commit()
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_settings_get(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT key, value FROM settings") as cur:
                rows = await cur.fetchall()
                settings_dict = {row['key']: row['value'] for row in rows}
        return web.json_response({'success': True, 'settings': settings_dict})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})




async def api_gateway_log_open(request: web.Request):
    # Deprecated endpoint previously writing duplicate APP_OPENED_UNLINKED
    # Kept for backward-compatibility with older cached browsers; returns success without duplicate log
    return web.json_response({'success': True, 'skipped': 'unified_in_log_action'})

async def api_gateway_log_action(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    import datetime
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        student_id_in = data.get('student_id')
        student_token = data.get('student_token') or data.get('token')
        source_in = data.get('source', '')
        action_type = data.get('action_type', 'TUTO_OPENED')
        first_name = data.get('first_name', '')
        username = data.get('username', '')
        description = data.get('description')
        step_code = data.get('step_code') or action_type
        
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Clean student_id_in if provided
        matched_student_id = 0
        if student_id_in:
            try:
                matched_student_id = int(student_id_in)
            except Exception:
                matched_student_id = 0

        async with aiosqlite.connect(DATABASE_PATH) as db:
            # 1. Resolve student if not directly identified
            student_row = None
            if matched_student_id > 0:
                async with db.execute("SELECT student_id, first_name, email FROM academy_students WHERE student_id = ?", (matched_student_id,)) as cur:
                    student_row = await cur.fetchone()
            
            if not student_row and student_token:
                async with db.execute("SELECT student_id, first_name, email FROM academy_students WHERE magic_token = ?", (str(student_token).strip(),)) as cur:
                    student_row = await cur.fetchone()

            if not student_row and source_in:
                # e.g., source could be e1_TOKEN, w1_TOKEN, or H123456 / F123456
                src_token = source_in
                if '_' in source_in:
                    src_token = source_in.split('_', 1)[1]
                async with db.execute("SELECT student_id, first_name, email FROM academy_students WHERE magic_token = ? OR student_id = ?", (src_token, src_token)) as cur:
                    student_row = await cur.fetchone()

            if not student_row and telegram_id:
                async with db.execute("SELECT student_id, first_name, email FROM academy_students WHERE telegram_id = ?", (telegram_id,)) as cur:
                    student_row = await cur.fetchone()

            # Retrieve Telegram first_name / username if missing from bot_visitors
            if telegram_id and (not first_name or not username):
                try:
                    async with db.execute("SELECT first_name, username FROM bot_visitors WHERE telegram_id = ?", (telegram_id,)) as cur_v:
                        v_row = await cur_v.fetchone()
                        if v_row:
                            if not first_name:
                                first_name = v_row[0] or ''
                            if not username:
                                username = v_row[1] or ''
                except Exception:
                    pass

            folder_link = ""
            group_desc = ""
            source_tag = f" [رابط: {source_in}]" if source_in else ""
            if student_row:
                resolved_id = student_row[0]
                st_name = student_row[1] or first_name
                desc = description or f"نشاط في مسار التأهيل للطالب {st_name} ({action_type})"
                if source_tag and (source_in not in desc):
                    desc += source_tag
                await db.execute(
                    "INSERT INTO student_logs (student_id, telegram_id, telegram_name, telegram_username, action_type, description) VALUES (?, ?, ?, ?, ?, ?)", 
                    (resolved_id, telegram_id or 0, first_name, username, action_type, desc)
                )
                # Update last onboarding step in academy_students
                try:
                    await db.execute("""
                        UPDATE academy_students 
                        SET last_onboarding_step = ?, last_onboarding_at = ?, last_onboarding_detail = ?
                        WHERE student_id = ?
                    """, (step_code, now_str, desc, resolved_id))
                except Exception:
                    pass
                
                try:
                    async with db.execute("SELECT * FROM academy_students WHERE student_id = ?", (resolved_id,)) as cur_full:
                        st_full = await cur_full.fetchone()
                        if st_full:
                            from handlers.auth import resolve_student_folder_link
                            # Convert to dict if row_factory is not set
                            st_dict = dict(zip([col[0] for col in cur_full.description], st_full))
                            folder_link, group_desc = await resolve_student_folder_link(db, st_dict)
                except Exception as e_fl:
                    logger.warning(f"Failed to resolve folder link in log_action: {e_fl}")
            else:
                target_sid = matched_student_id if matched_student_id > 0 else 0
                desc = description or f"نشاط مسار لمستخدم (المعرف: {matched_student_id or 'غير محدد'} | {first_name or telegram_id or 'مجهول'})"
                if source_tag and (source_in not in desc):
                    desc += source_tag
                await db.execute(
                    "INSERT INTO student_logs (student_id, telegram_id, telegram_name, telegram_username, action_type, description) VALUES (?, ?, ?, ?, ?, ?)", 
                    (target_sid, telegram_id or 0, first_name, username, action_type, desc)
                )

            await db.commit()
        return web.json_response({'success': True, 'folder_link': folder_link, 'group_desc': group_desc})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_student_folder_link(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        tg_id = request.query.get('telegram_id')
        sid = request.query.get('student_id')
        token = request.query.get('token')
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            student = None
            if tg_id and str(tg_id).strip() not in ('', '0'):
                async with db.execute("SELECT * FROM academy_students WHERE telegram_id = ?", (str(tg_id).strip(),)) as cur:
                    student = await cur.fetchone()
            if not student and sid and str(sid).strip() not in ('', '0'):
                async with db.execute("SELECT * FROM academy_students WHERE student_id = ?", (str(sid).strip(),)) as cur:
                    student = await cur.fetchone()
            if not student and token and str(token).strip():
                clean_tok = str(token).strip()
                import re as _re_tok
                clean_tok = _re_tok.sub(r'^(auth_|src_email_|src_wa_|src_web_|token_|e1_|e2_|w1_|w2_|sms_)', '', clean_tok)
                async with db.execute("SELECT * FROM academy_students WHERE magic_token = ? OR student_id = ?", (clean_tok, clean_tok)) as cur:
                    student = await cur.fetchone()
                    
            if student:
                s_dict = dict(student)
                from handlers.auth import resolve_student_folder_link
                folder_link, group_desc = await resolve_student_folder_link(db, s_dict)
                return web.json_response({
                    'success': True,
                    'found': True,
                    'folder_link': folder_link,
                    'group_desc': group_desc,
                    'first_name': s_dict.get('first_name', ''),
                    'gender': s_dict.get('gender', 'HOMME'),
                    'year': s_dict.get('year', 1)
                })
            else:
                async with db.execute("SELECT folder_link FROM group_settings LIMIT 1") as cur:
                    grow = await cur.fetchone()
                    default_link = grow[0] if (grow and grow[0]) else "https://t.me/addlist/Yw-eXYtl1BVkYTdk"
                return web.json_response({
                    'success': True,
                    'found': False,
                    'folder_link': default_link,
                    'group_desc': 'مجموعة الأكاديمية'
                })
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_gateway_sos(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        email = data.get('email', '')
        message = data.get('message', '')
        telegram_id = data.get('telegram_id')
        dob = data.get('dob', '')
        student_id = data.get('student_id', '')
        source = (data.get('source') or '').strip()
        first_name = (data.get('first_name') or '').strip()
        last_name = (data.get('last_name') or '').strip()
        username = (data.get('username') or '').strip()
        
        # Parse init_data if telegram_id was not directly sent
        init_data = data.get('init_data') or data.get('initData') or ''
        if (not telegram_id or str(telegram_id) in ('0', 'None', 'null', '')) and init_data:
            try:
                import json
                import urllib.parse
                qs = urllib.parse.parse_qs(init_data)
                if 'user' in qs:
                    u_obj = json.loads(qs['user'][0])
                    telegram_id = u_obj.get('id')
                    if not first_name:
                        first_name = u_obj.get('first_name', '')
                    if not last_name:
                        last_name = u_obj.get('last_name', '')
                    if not username:
                        username = u_obj.get('username', '')
            except Exception:
                pass

        if telegram_id:
            try:
                telegram_id = int(telegram_id)
            except Exception:
                pass

        # Parse numeric student id if present
        numeric_sid = 0
        if student_id:
            try:
                numeric_sid = int(str(student_id).strip())
            except Exception:
                numeric_sid = 0

        async with aiosqlite.connect(DATABASE_PATH) as db:
            try:
                await db.execute("ALTER TABLE gateway_sos ADD COLUMN source TEXT")
                await db.commit()
            except Exception:
                pass

            # Auto-resolve student if numeric_sid is 0
            if numeric_sid == 0 and telegram_id:
                try:
                    async with db.execute("SELECT student_id, first_name FROM academy_students WHERE telegram_id = ?", (telegram_id,)) as cur_s:
                        row_s = await cur_s.fetchone()
                        if row_s:
                            numeric_sid = row_s[0]
                except Exception:
                    pass
            if numeric_sid == 0 and email:
                try:
                    async with db.execute("SELECT student_id, first_name FROM academy_students WHERE LOWER(email) = ?", (email.strip().lower(),)) as cur_e:
                        row_e = await cur_e.fetchone()
                        if row_e:
                            numeric_sid = row_e[0]
                except Exception:
                    pass

            # Auto-resolve Telegram names from bot_visitors if missing
            if telegram_id and (not first_name or not username):
                try:
                    async with db.execute("SELECT first_name, username FROM bot_visitors WHERE telegram_id = ?", (telegram_id,)) as cur_v:
                        v_row = await cur_v.fetchone()
                        if v_row:
                            if not first_name: first_name = v_row[0] or ''
                            if not username: username = v_row[1] or ''
                except Exception:
                    pass

            tg_display = f"{first_name} {last_name}".strip()
            source_label = f" [رابط: {source}]" if source else ""
            desc_sos = f"🆘 طلب مساعدة SOS: '{message}' (الرقم: {numeric_sid or student_id or 'غير محدد'} | البريد: {email or 'غير محدد'}){source_label}"

            if telegram_id:
                try:
                    await db.execute("""
                        INSERT INTO users (telegram_id, first_name, last_name, username) 
                        VALUES (?, ?, ?, ?) 
                        ON CONFLICT(telegram_id) DO UPDATE SET 
                            first_name = COALESCE(NULLIF(excluded.first_name, ''), users.first_name),
                            last_name = COALESCE(NULLIF(excluded.last_name, ''), users.last_name),
                            username = COALESCE(NULLIF(excluded.username, ''), users.username)
                    """, (telegram_id, first_name, last_name, username))
                except Exception:
                    pass

            await db.execute("INSERT INTO gateway_sos (email_tentative, message, telegram_id, dob_tentative, student_id_tentative, source) VALUES (?, ?, ?, ?, ?, ?)", (email, message, telegram_id, dob, student_id or str(numeric_sid or ''), source))
            await db.execute(
                "INSERT INTO student_logs (student_id, telegram_id, telegram_name, telegram_username, action_type, description) VALUES (?, ?, ?, ?, ?, ?)",
                (numeric_sid, telegram_id or 0, tg_display, username, 'SOS_REQUESTED', desc_sos)
            )
            if numeric_sid > 0:
                try:
                    await db.execute("UPDATE academy_students SET last_onboarding_step = 'STEP_SOS_REQUESTED', last_onboarding_detail = ? WHERE student_id = ?", (desc_sos, numeric_sid))
                except Exception:
                    pass
            await db.commit()
        
        # Notify admins via Telegram
        try:
            from config import TELEGRAM_ADMIN_IDS
            user_info_str = f"✈️ <b>Compte Telegram :</b> {tg_display or 'N/A'}"
            if username:
                user_info_str += f" (@{username})"
            if telegram_id:
                user_info_str += f" [ID: <code>{telegram_id}</code>]"

            admin_notif = (
                f"🆘 <b>Nouveau SOS Liaison !</b>\n\n"
                f"{user_info_str}\n"
                f"📧 <b>Email saisi :</b> <code>{email or 'N/A'}</code>\n"
                f"🪪 <b>Matricule :</b> <code>{student_id or 'N/A'}</code>\n"
                f"🔗 <b>Lien / Source :</b> <code>{source or 'N/A'}</code>\n"
                f"💬 <b>Message :</b>\n<blockquote>{message}</blockquote>\n\n"
                f"👉 Répondez depuis le Dashboard Admin (/federer)"
            )
            bot = request.app['bot']
            for admin_id in TELEGRAM_ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, admin_notif, parse_mode="HTML")
                except Exception as ex:
                    print(f"Error sending SOS to admin {admin_id}: {ex}")
        except Exception as ex:
            print(f"Error in api_gateway_sos notify: {ex}")
            
        # Send confirmation to student in Arabic
        if telegram_id:
            try:
                bot = request.app['bot']
                confirm_msg = (
                    f"⚠️ <b>تم استلام طلب المساعدة الخاص بك بنجاح</b>\n\n"
                    f"<blockquote>"
                    f"<b>محتوى رسالتك:</b>\n<i>{message}</i>"
                    f"</blockquote>\n\n"
                    f"سيقوم أحد المشرفين بمراجعة طلبك والرد عليك في أقرب وقت ممكن عبر هذه المحادثة."
                )
                await bot.send_message(int(telegram_id), confirm_msg, parse_mode="HTML")
            except Exception as ex:
                print(f"Error sending SOS confirmation to student: {ex}")
            
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_links_get(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT key, value FROM settings WHERE key LIKE 'link_%'") as cur:
                links = [dict(row) for row in await cur.fetchall()]
        return web.json_response({'success': True, 'links': links})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_sos_list(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row

            # Repair historical misattributed tickets
            try:
                # Tickets 5, 6, 7 ('test ping', 'Ping') were sent by Asdad01 (1838356491) at 21:09 / 21:14
                await db.execute("UPDATE gateway_sos SET telegram_id = 1838356491 WHERE id IN (5, 6, 7)")
                # Ticket 13 ('Gsh') was sent by Admin Houssam (2045194295) at 22:00:39
                await db.execute("UPDATE gateway_sos SET telegram_id = 2045194295 WHERE id = 13 OR message = 'Gsh'")
                await db.commit()
            except Exception:
                pass

            async with db.execute("""
                SELECT g.*, 
                       s.gender AS student_gender, s.first_name AS student_first_name, s.last_name AS student_last_name,
                       u.first_name AS tg_first_name, u.last_name AS tg_last_name, u.username AS tg_username
                FROM gateway_sos g
                LEFT JOIN academy_students s ON (
                    (g.email_tentative IS NOT NULL AND g.email_tentative != '' AND LOWER(TRIM(g.email_tentative)) = LOWER(TRIM(s.email))) 
                    OR (g.student_id_tentative IS NOT NULL AND g.student_id_tentative != '' AND CAST(g.student_id_tentative AS TEXT) = CAST(s.student_id AS TEXT))
                )
                LEFT JOIN users u ON CAST(g.telegram_id AS TEXT) = CAST(u.telegram_id AS TEXT) AND g.telegram_id IS NOT NULL AND g.telegram_id != 0 AND g.telegram_id != ''
                ORDER BY g.id DESC LIMIT 100
            """) as cur:
                rows = [dict(row) for row in await cur.fetchall()]
            
            sos_list = []
            for r in rows:
                item = dict(r)
                if item.get('student_first_name') or item.get('student_last_name'):
                    item['first_name'] = item.get('student_first_name')
                    item['last_name'] = item.get('student_last_name')
                    item['gender'] = item.get('student_gender')

                tid_val = str(item.get('telegram_id') or '').strip()
                if tid_val in ('0', 'None', 'null', ''):
                    tid_val = ''
                    item['telegram_id'] = None

                # If telegram_id was missing on this SOS record, discover it from student_logs
                if not tid_val:
                    email_t = (item.get('email_tentative') or '').strip().lower()
                    msg_t = (item.get('message') or '').strip()
                    sos_time = item.get('timestamp') or ''

                    found_tid = None
                    found_name = None
                    found_user = None

                    # 1. Match by exact or partial message in ONBOARDING_SOS_SENT student_logs
                    if msg_t and len(msg_t) >= 3 and not found_tid:
                        msg_snip = msg_t[:25]
                        async with db.execute("""
                            SELECT telegram_id, telegram_name, telegram_username 
                            FROM student_logs 
                            WHERE telegram_id IS NOT NULL AND telegram_id != 0 
                              AND action_type LIKE '%SOS%'
                              AND description LIKE ?
                            ORDER BY id DESC LIMIT 1
                        """, (f"%{msg_snip}%",)) as cur_m:
                            m_row = await cur_m.fetchone()
                            if m_row and m_row[0]:
                                found_tid, found_name, found_user = str(m_row[0]), m_row[1], m_row[2]

                    # 2. Match by email in student_logs (allow admin ID only if email matches admin's email)
                    if email_t and '@' in email_t and not email_t.startswith('@') and not found_tid:
                        async with db.execute("""
                            SELECT telegram_id, telegram_name, telegram_username 
                            FROM student_logs 
                            WHERE telegram_id IS NOT NULL AND telegram_id != 0 
                              AND (telegram_id != 2045194295 OR ? = 'h.bouddou@gmail.com')
                              AND LOWER(description) LIKE ?
                            ORDER BY id DESC LIMIT 1
                        """, (email_t, f"%{email_t}%")) as cur_m:
                            m_row = await cur_m.fetchone()
                            if m_row and m_row[0]:
                                found_tid, found_name, found_user = str(m_row[0]), m_row[1], m_row[2]

                    # 3. Match by time window: which visitor was active in the onboarding funnel within 5 minutes of this ticket?
                    if not found_tid and sos_time:
                        async with db.execute("""
                            SELECT telegram_id, telegram_name, telegram_username 
                            FROM student_logs 
                            WHERE telegram_id IS NOT NULL AND telegram_id != 0 
                              AND telegram_id != 2045194295
                              AND action_type IN ('ONBOARDING_FORM_REACHED', 'ONBOARDING_PAGE_OPENED', 'ONBOARDING_CHARTER_SIGNED', 'ONBOARDING_SOS_OPENED', 'ONBOARDING_SOS_SENT')
                              AND ABS(strftime('%s', timestamp) - strftime('%s', ?)) < 360
                            ORDER BY ABS(strftime('%s', timestamp) - strftime('%s', ?)) ASC LIMIT 1
                        """, (sos_time, sos_time)) as cur_m:
                            m_row = await cur_m.fetchone()
                            if m_row and m_row[0]:
                                found_tid, found_name, found_user = str(m_row[0]), m_row[1], m_row[2]

                    if found_tid:
                        tid_val = found_tid
                        item['telegram_id'] = int(found_tid) if found_tid.isdigit() else found_tid
                        if found_name and not item.get('tg_first_name'):
                            item['tg_first_name'] = found_name
                        if found_user and not item.get('tg_username'):
                            item['tg_username'] = found_user
                        try:
                            await db.execute("UPDATE gateway_sos SET telegram_id = ? WHERE id = ?", (item['telegram_id'], item['id']))
                            await db.commit()
                        except Exception:
                            pass

                # If telegram_id is known (whether admin or student):
                if tid_val:
                    int_tid = int(tid_val) if tid_val.isdigit() else 0
                    if not item.get('tg_first_name') or not item.get('tg_username'):
                        async with db.execute("SELECT first_name, last_name, username FROM users WHERE telegram_id = ? OR CAST(telegram_id AS TEXT) = ?", (int_tid, tid_val)) as cur_u:
                            u_row = await cur_u.fetchone()
                            if u_row:
                                if not item.get('tg_first_name') and u_row[0]: item['tg_first_name'] = u_row[0]
                                if not item.get('tg_last_name') and u_row[1]: item['tg_last_name'] = u_row[1]
                                if not item.get('tg_username') and u_row[2]: item['tg_username'] = u_row[2]

                    if not item.get('tg_first_name'):
                        async with db.execute("""
                            SELECT telegram_name, telegram_username 
                            FROM student_logs 
                            WHERE (telegram_id = ? OR CAST(telegram_id AS TEXT) = ?) AND (telegram_name != '' OR telegram_username != '')
                            ORDER BY id DESC LIMIT 1
                        """, (int_tid, tid_val)) as cur_l:
                            row_l = await cur_l.fetchone()
                            if row_l:
                                if not item.get('tg_first_name') and row_l[0]: item['tg_first_name'] = row_l[0]
                                if not item.get('tg_username') and row_l[1]: item['tg_username'] = row_l[1]

                sos_list.append(item)

        return web.json_response({'success': True, 'sos_list': sos_list})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_sos_reply(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    from keyboards import get_webapp_base_url
    try:
        data = await request.json()
        sos_id = data.get('sos_id')
        reply_message = (data.get('reply_message') or '').strip()
        telegram_id = data.get('telegram_id') # To send back if available, otherwise just mark closed
        
        email = ""
        student_id_entered = ""
        student_msg = ""
        source = ""

        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            if sos_id:
                async with db.execute("SELECT * FROM gateway_sos WHERE id = ?", (sos_id,)) as cur:
                    sos_row = await cur.fetchone()
                    if sos_row:
                        sos_dict = dict(sos_row)
                        email = sos_dict.get('email_tentative') or ""
                        student_id_entered = sos_dict.get('student_id_tentative') or ""
                        student_msg = sos_dict.get('message') or ""
                        source = sos_dict.get('source') or ""
                        if not telegram_id:
                            telegram_id = sos_dict.get('telegram_id')

            if not source and telegram_id:
                # Find source from recent student_logs
                async with db.execute("SELECT description FROM student_logs WHERE telegram_id = ? AND description LIKE '%[رابط:%' ORDER BY id DESC LIMIT 1", (telegram_id,)) as cur_src:
                    r_src = await cur_src.fetchone()
                    if r_src:
                        import re
                        m = re.search(r'\[رابط:\s*([^\]]+)\]', r_src[0])
                        if m:
                            source = m.group(1).strip()

            if not source and telegram_id:
                async with db.execute("SELECT gender FROM academy_students WHERE telegram_id = ?", (telegram_id,)) as cur_g:
                    rg = await cur_g.fetchone()
                    if rg and rg[0] == 'FEMME':
                        source = 'F1'
                    elif rg and rg[0] == 'HOMME':
                        source = 'H1'

            if not source:
                source = 'F1'

            if telegram_id:
                try:
                    bot = request.app['bot']
                    base_url = get_webapp_base_url()
                    reply_url = f"{base_url}/link.html?source={source}&telegram_id={telegram_id}&step=form&direct=1"
                    
                    response_text = (
                        "🛠️ <b>رد إدارة أكاديمية الباجي:</b>\n"
                        f"<blockquote>{reply_message}</blockquote>\n\n"
                        "📋 <b>تفاصيل طلبك المسجلة لدينا:</b>\n"
                        "<blockquote>"
                        f"• <b>رسالتك:</b> {student_msg or 'طلب مساعدة'}\n"
                        f"• <b>رقم الطالب المدخل:</b> <code>{student_id_entered or 'غير محدد'}</code>\n"
                        f"• <b>البريد الإلكتروني:</b>\n<code>{email or 'غير محدد'}</code>"
                        "</blockquote>\n\n"
                        "👇 <b>يمكنك إعادة المحاولة وتأكيد بياناتك مباشرة عبر الزر أدناه:</b>"
                    )
                    
                    reply_kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔄 إعادة محاولة تأكيد وربط الحساب", web_app=WebAppInfo(url=reply_url))]
                    ])
                    
                    await bot.send_message(int(telegram_id), response_text, reply_markup=reply_kb, parse_mode="HTML")
                    
                    # Log in student_logs
                    desc_reply = f"تم إرسال رد الإدارة على استغاثة SOS مع زر إعادة المحاولة [رابط: {source}]"
                    numeric_sid = int(student_id_entered) if student_id_entered and str(student_id_entered).isdigit() else 0
                    await db.execute(
                        "INSERT INTO student_logs (student_id, telegram_id, telegram_name, telegram_username, action_type, description) VALUES (?, ?, ?, ?, ?, ?)",
                        (numeric_sid, int(telegram_id), '', '', 'SOS_REPLIED', desc_reply)
                    )
                except Exception as e:
                    print(f"Error sending SOS reply to student {telegram_id}: {e}")

            await db.execute("UPDATE gateway_sos SET status = 'closed' WHERE id = ?", (sos_id,))
            await db.commit()
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_sos_delete(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        sos_id = request.match_info.get('id')
        if not sos_id:
            try:
                data = await request.json()
                sos_id = data.get('sos_id') or data.get('id')
            except Exception:
                pass
        
        if not sos_id:
            return web.json_response({'success': False, 'error': 'Missing sos_id'}, status=400)
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DELETE FROM gateway_sos WHERE id = ?", (sos_id,))
            await db.commit()
            
        return web.json_response({'success': True, 'deleted_id': sos_id})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_admin_gateway_chat(request: web.Request):
    telegram_id = request.query.get('id')
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT sender, message_text, timestamp FROM bot_conversations WHERE telegram_id = ? ORDER BY id ASC LIMIT 100", (telegram_id,)) as cur:
                chats = [dict(row) for row in await cur.fetchall()]
        return web.json_response({'success': True, 'chats': chats})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})


# ==========================================
# SMS GATEWAY API
# ==========================================

async def api_admin_gateway_queue_sms(request):
    from aiohttp import web
    import datetime
    import aiosqlite
    import re
    from config import DATABASE_PATH
    import config as cfg

    try:
        data = await request.json()
        student_ids = data.get('student_ids', [])
        if not student_ids: return web.json_response({'success': False})

        bot_user = getattr(cfg, 'MAIN_BOT_USERNAME', 'alsirahquizz_bot') or 'alsirahquizz_bot'
        now_str = datetime.datetime.utcnow().isoformat()
        queued = 0

        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            for sid in student_ids:
                async with db.execute("SELECT * FROM academy_students WHERE student_id = ?", (sid,)) as cur:
                    s = await cur.fetchone()
                if not s or not s['phone']: continue

                phone = re.sub(r'\D', '', s['phone'])
                if phone.startswith('0'): phone = '212' + phone[1:]
                
                token = s['magic_token'] or s['student_id']
                fname = s['first_name'] or ''
                text = f"السلام عليكم {fname}، إليك رابط الدخول الخاص بك للأكاديمية:\nhttps://t.me/{bot_user}?start=sms_{token}"

                await db.execute(
                    "INSERT INTO sms_queue (student_id, phone, message, status, created_at) VALUES (?, ?, ?, 'PENDING', ?)",
                    (sid, phone, text, now_str)
                )
                queued += 1
            await db.commit()

        return web.json_response({'success': True, 'queued': queued})
    except Exception as e:
        import traceback; traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)})

async def api_sms_gateway_poll(request):
    from aiohttp import web
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT COUNT(*) as cnt FROM sms_queue WHERE status = 'PENDING'") as cur:
                pending_count = (await cur.fetchone())['cnt']
            
            async with db.execute("SELECT id, phone, message FROM sms_queue WHERE status = 'PENDING' ORDER BY id ASC LIMIT 1") as cur:
                row = await cur.fetchone()

            if row:
                return web.json_response({
                    "success": True,
                    "pending_count": pending_count,
                    "message": {
                        "id": row['id'],
                        "to": "+" + row['phone'] if not row['phone'].startswith('+') else row['phone'],
                        "message": row['message']
                    }
                })
            return web.json_response({"success": False, "pending_count": 0})
    except Exception as e:
        from aiohttp import web
        return web.json_response({"success": False, "error": str(e)})

async def api_sms_gateway_callback(request):
    from aiohttp import web
    import datetime
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        msg_id = data.get('id')
        status = data.get('status', 'SENT')

        if msg_id:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                now_str = datetime.datetime.utcnow().isoformat()
                await db.execute("UPDATE sms_queue SET status = ?, sent_at = ? WHERE id = ?", (status, now_str, msg_id))
                
                if status == 'SENT':
                    async with db.execute("SELECT student_id FROM sms_queue WHERE id = ?", (msg_id,)) as cur:
                        row = await cur.fetchone()
                    if row:
                        sid = row['student_id']
                        await db.execute("UPDATE academy_students SET sms_sent = 1, sms_sent_at = ? WHERE student_id = ?", (now_str, sid))
                        admin_name = "SMS Gateway"
                        note_text = f"[بواسطة: {admin_name}] [نوع: SYSTEM]\nSMS automatique envoyé avec succès."
                        await db.execute(
                            "INSERT INTO student_logs (student_id, action_type, description, telegram_name) VALUES (?, ?, ?, ?)",
                            (sid, "SMS_SENT", note_text, admin_name)
                        )
                await db.commit()

        return web.json_response({"success": True})
    except Exception as e:
        import traceback; traceback.print_exc()
        from aiohttp import web
        return web.json_response({"success": False, "error": str(e)})

# ==========================================

async def api_admin_gateway_action(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    from database import log_student_action
    from datetime import datetime
    try:
        data = await request.json()
        action = data.get('action')
        student_id = data.get('student_id')
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM academy_students WHERE student_id = ?", (student_id,)) as cur:
                student = await cur.fetchone()
                
            if not student:
                return web.json_response({'success': False, 'error': 'Student not found'})
                
            if action == 'unlink':
                await db.execute("UPDATE academy_students SET telegram_id = NULL WHERE student_id = ?", (student_id,))
                await log_student_action(student_id, 'MANUAL_UNLINK', "L'administrateur a dissocié le compte manuellement.")
                
            elif action == 'manual_link':
                telegram_id = data.get('telegram_id')
                if not telegram_id:
                    return web.json_response({'success': False, 'error': 'Missing telegram_id'})
                await db.execute("UPDATE academy_students SET telegram_id = ? WHERE student_id = ?", (telegram_id, student_id))
                await log_student_action(student_id, 'MANUAL_LINK', f"تم ربط الحساب يدويًا بواسطة المشرف مع تيليجرام ID: {telegram_id}", telegram_id=telegram_id)
                
            elif action == 'send_email_1' or action == 'send_email_2':
                # Pour l'instant on utilise le template d'onboarding par défaut (à faire évoluer plus tard si on veut 2 templates différents)
                step_prefix = 'e1' if action == 'send_email_1' else 'e2'
                success, msg = await send_single_onboarding_email(student['email'], student['first_name'], student['student_id'], student['gender'], step_prefix=step_prefix)
                if success:
                    now_str = datetime.utcnow().isoformat()
                    step_num = 1 if action == 'send_email_1' else 2
                    await db.execute("UPDATE academy_students SET email_sent = ?, email_sent_at = ? WHERE student_id = ?", (step_num, now_str, student_id))
                    await log_student_action(student_id, 'EMAIL_SENT', f"Email de type {action} envoyé.")
                else:
                    return web.json_response({'success': False, 'error': msg})
                    
            elif action == 'log_tg_1':
                await log_student_action(student_id, 'TELEGRAM_CONTACT', f"Contact Telegram direct ({action}) effectué.")
                
            elif action == 'log_wa_1' or action == 'log_wa_2':
                now_str = datetime.utcnow().isoformat()
                step_wa = 1 if action == 'log_wa_1' else 2
                await db.execute("UPDATE academy_students SET whatsapp_sent = ?, whatsapp_sent_at = ? WHERE student_id = ?", (step_wa, now_str, student_id))
                await log_student_action(student_id, 'WHATSAPP_SENT', f"Relance WhatsApp ({action}) effectuée.")
                
            elif action == 'log_sms':
                now_str = datetime.utcnow().isoformat()
                await db.execute("UPDATE academy_students SET sms_sent = 1, sms_sent_at = ? WHERE student_id = ?", (now_str, student_id))
                await log_student_action(student_id, 'SMS_SENT', "Lien direct envoyé par SMS.")
                
            await db.commit()
            
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def handle_link(request):
    import aiosqlite
    from config import DATABASE_PATH
    html_path = os.path.join(DASHBOARD_DIR, 'link.html')
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        student_theme = 'default'
        student_font = 'font-tajawal'
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT value FROM settings WHERE key='student_theme'") as cur:
                r = await cur.fetchone()
                if r: student_theme = r[0]
            async with db.execute("SELECT value FROM settings WHERE key='student_font'") as cur:
                r = await cur.fetchone()
                if r: student_font = r[0]
                
        # Inject script
        script = f"<script>window.SERVER_STUDENT_THEME = '{student_theme}'; window.SERVER_STUDENT_FONT = '{student_font}';</script>"
        content = content.replace('<head>', '<head>' + script, 1)
        
        resp = web.Response(body=content, content_type='text/html')
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        return resp
    except Exception as e:
        return web.Response(text=str(e), status=500)


async def handle_reader_js(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'reader.js'))

async def handle_exam_js(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'exam.js'))

async def handle_quiz_js(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'quiz.js'))

async def handle_reader_css(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'reader.css'))

async def check_admin(user_id):
    if not user_id:
        return False
    from config import TELEGRAM_ADMIN_IDS, DATABASE_PATH
    if int(user_id) in TELEGRAM_ADMIN_IDS:
        return True
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            async with db_conn.execute("SELECT 1 FROM admins WHERE telegram_id = ?", (int(user_id),)) as cur:
                row = await cur.fetchone()
                if row:
                    return True
    except Exception as e:
        logger.error(f"Error checking admin status for {user_id}: {e}")
    return False

async def get_admin_role(user_id):
    if not user_id:
        return None
    from config import TELEGRAM_ADMIN_IDS, DATABASE_PATH
    if int(user_id) in TELEGRAM_ADMIN_IDS:
        return "super_admin"
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            async with db_conn.execute("SELECT role FROM admins WHERE telegram_id = ?", (int(user_id),)) as cur:
                row = await cur.fetchone()
                if row:
                    return row[0]
    except Exception as e:
        logger.error(f"Error getting admin role for {user_id}: {e}")
    return None

async def get_admin_info(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not user_id:
            return web.json_response({"success": False, "error": "Missing userId"}, status=400)
            
        from config import DATABASE_PATH, TELEGRAM_ADMIN_IDS
        role = "moderator"
        first_name = "Ù…Ø´Ø±Ù"
        username = "admin"
        
        if int(user_id) in TELEGRAM_ADMIN_IDS:
            role = "super_admin"
            first_name = "Super Admin"
            
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute("SELECT role, first_name, username, allowed_subjects, visible_sections FROM admins WHERE telegram_id = ?", (int(user_id),)) as cur:
                row = await cur.fetchone()
                if row:
                    role = row["role"]
                    first_name = row["first_name"] or first_name
                    username = row["username"] or username
                    allowed_subjects_raw = row["allowed_subjects"]
                    visible_sections_raw = row["visible_sections"]
                else:
                    allowed_subjects_raw = None
                    visible_sections_raw = None
            
            # Fallback if first_name/username is still generic/missing/default
            if first_name in ["Ù…Ø´Ø±Ù", "Super Admin"] or not first_name:
                async with db_conn.execute("SELECT first_name, username FROM users WHERE telegram_id = ?", (int(user_id),)) as cur:
                    r = await cur.fetchone()
                    if r and (r["first_name"] or r["username"]):
                        first_name = r["first_name"] or first_name
                        username = r["username"] or username
                        await db_conn.execute(
                            "UPDATE admins SET first_name = ?, username = ? WHERE telegram_id = ?",
                            (r["first_name"] or "", r["username"] or "", int(user_id))
                        )
            
            if first_name in ["Ù…Ø´Ø±Ù", "Super Admin"] or not first_name:
                bot = request.app.get('bot')
                if bot:
                    try:
                        chat = await bot.get_chat(chat_id=int(user_id))
                        if chat:
                            first_name = chat.first_name or first_name
                            username = chat.username or username
                            await db_conn.execute(
                                "UPDATE admins SET first_name = ?, username = ? WHERE telegram_id = ?",
                                (chat.first_name or "", chat.username or "", int(user_id))
                            )
                    except Exception as tg_err:
                        logger.warning(f"Could not retrieve admin chat info from Telegram in get_admin_info: {tg_err}")
                    
        import json as _json
        if allowed_subjects_raw:
            try:
                allowed_subjects = _json.loads(allowed_subjects_raw)
            except Exception:
                allowed_subjects = [s.strip() for s in allowed_subjects_raw.split(",") if s.strip()]
        else:
            allowed_subjects = None
        visible_sections = _json.loads(visible_sections_raw) if visible_sections_raw else None

        return web.json_response({
            "success": True, 
            "info": {
                "role": role,
                "firstName": first_name,
                "username": username,
                "allowedSubjects": allowed_subjects,
                "visibleSections": visible_sections
            }
        })
    except Exception as e:
        logger.error(f"Error fetching admin info: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def get_admin_settings(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        role = await get_admin_role(user_id)
        if role != "super_admin":
            return web.json_response({"success": False, "error": "Require super_admin role"}, status=403)
            
        from config import DATABASE_PATH
        settings = {}
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute("SELECT key, value FROM settings") as cur:
                async for row in cur:
                    settings[row["key"]] = row["value"]
                    
        # Provide default values if missing
        from config import ACADEMY_GROUP_ID
        settings.setdefault("academy_group_id", str(ACADEMY_GROUP_ID))
        settings.setdefault("test_group_id", "")
        settings.setdefault("restrict_to_academy_group", "True")
        settings.setdefault("disable_ai_for_students", "False")
        settings.setdefault("ticket_detail_level", "compact")
        settings.setdefault("maintenance_mode", "False")
        settings.setdefault("maintenance_message", "ðŸš§ Ø§Ù„Ø¨Ùˆت ÙÙŠ Ùˆضع Ø§Ù„ØµÙŠØ§Ù†ة Ù…Ø¤Ù‚ØªØ§Ù‹. Ø³ÙŠØ¹Ùˆد Ù‚Ø±ÙŠØ¨Ø§Ù‹ Ø¨Ø¥Ø°Ù† Ø§Ù„Ù„Ù‡.")
        settings.setdefault("quiz_questions_per_session", "10")
        settings.setdefault("quiz_cooldown_minutes", "0")
        settings.setdefault("enable_revision_mode", "False")
        settings.setdefault("quiz_pass_threshold", "60")
        settings.setdefault("bot_welcome_message", "Ù…Ø±Ø­Ø¨Ø§Ù‹ Ø¨Ùƒ ÙÙŠ Ø¨Ùˆت Ø£ÙƒØ§Ø¯ÙŠÙ…ÙŠة Ø§Ù„Ù†Ùˆر! ðŸŒŸ")
        settings.setdefault("notify_on_new_report", "True")
        settings.setdefault("quiz_reminder_enabled", "False")
        
        return web.json_response({"success": True, "settings": settings})
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def purge_old_tickets(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        days = int(data.get('days', 30))
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
        
        from config import DATABASE_PATH
        cutoff = f"datetime('now', '-{days} days')"
        deleted_total = 0
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            # Purge resolved/rejected chapter reports
            async with db_conn.execute(f"""
                DELETE FROM chapter_reports
                WHERE status IN ('resolved','rejected')
                AND created_at < {cutoff}
            """) as cur:
                deleted_total += cur.rowcount
            # Purge resolved/rejected question reports
            async with db_conn.execute(f"""
                DELETE FROM question_reports
                WHERE status IN ('resolved','rejected')
                AND created_at < {cutoff}
            """) as cur:
                deleted_total += cur.rowcount
            await db_conn.commit()
        
        return web.json_response({"success": True, "deleted": deleted_total})
    except Exception as e:
        logger.error(f"Error purging tickets: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def update_admin_setting(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        key = data.get('key')
        value = data.get('value')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        role = await get_admin_role(user_id)
        if role != "super_admin":
            return web.json_response({"success": False, "error": "Require super_admin role"}, status=403)
            
        if not key:
            return web.json_response({"success": False, "error": "Missing setting key"}, status=400)
            
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute("""
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            """, (key, str(value)))
            await db_conn.commit()
            
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error updating setting {key}: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def get_admin_students(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if user_id is not None:
            user_id = int(user_id)
            
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        students = []
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            
            # Fetch all students
            async with db_conn.execute("""
                SELECT telegram_id, username, first_name, gender, preferred_name, created_at 
                FROM users 
                ORDER BY created_at DESC
            """) as cur:
                async for r in cur:
                    student_id = r["telegram_id"]
                    
                    # Fetch counts
                    # 1. Quizzes taken
                    quiz_count = 0
                    async with db_conn.execute("SELECT COUNT(*) FROM quiz_logs WHERE user_id = ?", (student_id,)) as q_cur:
                        quiz_count = (await q_cur.fetchone())[0]
                        
                    # 2. Bug reports
                    report_count = 0
                    async with db_conn.execute("SELECT COUNT(*) FROM question_reports WHERE user_id = ?", (student_id,)) as rep_cur:
                        report_count = (await rep_cur.fetchone())[0]
                    try:
                        async with db_conn.execute("SELECT COUNT(*) FROM chapter_reports WHERE user_id = ?", (student_id,)) as ch_cur:
                            report_count += (await ch_cur.fetchone())[0]
                    except Exception:
                        pass

                    # 3. Question proposals
                    proposal_count = 0
                    async with db_conn.execute("SELECT COUNT(*) FROM question_proposals WHERE user_id = ?", (student_id,)) as prop_cur:
                        proposal_count = (await prop_cur.fetchone())[0]
                        
                    students.append({
                        "telegramId": student_id,
                        "username": r["username"] or "",
                        "firstName": r["first_name"] or "",
                        "gender": r["gender"] or "",
                        "preferredName": r["preferred_name"] or "",
                        "createdAt": r["created_at"],
                        "quizCount": quiz_count,
                        "reportCount": report_count,
                        "proposalCount": proposal_count
                    })
        return web.json_response({"success": True, "students": students})
    except Exception as e:
        logger.error(f"Error loading students: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def get_admin_student_details(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        student_id = data.get('studentId')
        if user_id is not None:
            user_id = int(user_id)
        if student_id is not None:
            student_id = int(student_id)
            
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        details = {
            "reports": [],
            "proposals": [],
            "quiz_logs": []
        }
        
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            
            # 1. Fetch both question reports and chapter reports
            reports = []
            
            # Fetch question reports
            try:
                async with db_conn.execute("""
                    SELECT id, question_id, report_type, notes, status, admin_reply, created_at 
                    FROM question_reports 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (student_id,)) as cur:
                    async for r in cur:
                        reports.append({
                            "id": r["id"],
                            "type": "question_report",
                            "questionId": r["question_id"],
                            "reportType": r["report_type"],
                            "report": r["notes"] or "",
                            "status": r["status"],
                            "adminReply": r["admin_reply"] or "",
                            "timestamp": r["created_at"]
                        })
            except Exception as e:
                logger.error(f"Error loading question reports in details: {e}")

            # Fetch chapter reports
            try:
                async with db_conn.execute("""
                    SELECT id, subject, lesson_num, chapter_idx, report, status, admin_reply, timestamp 
                    FROM chapter_reports 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                """, (student_id,)) as cur:
                    async for r in cur:
                        reports.append({
                            "id": r["id"],
                            "type": "chapter_report",
                            "subject": r["subject"],
                            "lessonNum": r["lesson_num"],
                            "chapterIdx": r["chapter_idx"],
                            "report": r["report"] or "",
                            "status": r["status"],
                            "adminReply": r["admin_reply"] or "",
                            "timestamp": r["timestamp"]
                        })
            except Exception as e:
                logger.error(f"Error loading chapter reports in details: {e}")

            # Sort merged reports chronologically (descending)
            def parse_ts(val):
                try:
                    if isinstance(val, (int, float)):
                        return val
                    import datetime
                    dt_str = str(val).split('.')[0].replace('T', ' ')
                    dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                    return dt.timestamp()
                except Exception:
                    return 0

            reports.sort(key=lambda x: parse_ts(x["timestamp"]), reverse=True)
            details["reports"] = reports
                    
            # 2. Fetch proposals
            async with db_conn.execute("""
                SELECT id, subject, course_number, question, status, admin_reply, created_at 
                FROM question_proposals 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (student_id,)) as cur:
                async for r in cur:
                    details["proposals"].append({
                        "id": r["id"],
                        "subject": r["subject"],
                        "courseNumber": r["course_number"],
                        "question": r["question"],
                        "status": r["status"],
                        "adminReply": r["admin_reply"] or "",
                        "createdAt": r["created_at"]
                    })

            # 3. Fetch quiz logs
            async with db_conn.execute("""
                SELECT ql.id, q.subject, ql.is_correct, ql.answered_at 
                FROM quiz_logs ql 
                JOIN questions q ON ql.question_id = q.id 
                WHERE ql.user_id = ? 
                ORDER BY ql.answered_at DESC 
                LIMIT 50
            """, (student_id,)) as cur:
                async for r in cur:
                    details["quiz_logs"].append({
                        "id": r["id"],
                        "subject": r["subject"],
                        "isCorrect": r["is_correct"],
                        "answeredAt": r["answered_at"]
                    })
                    
        return web.json_response({"success": True, "details": details})
    except Exception as e:
        logger.error(f"Error loading student details: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)




# Student API: Submit a content error report
async def report_chapter(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        username = data.get('username', '')
        first_name = data.get('firstName', '')
        subject = data.get('subject')
        lesson_num = data.get('lessonNum')
        chapter_idx = data.get('chapterIdx')
        report_text = data.get('report')
        
        if not user_id or not subject or lesson_num is None or chapter_idx is None or not report_text:
            return web.json_response({"success": False, "error": "Missing fields"}, status=400)
        
        from datetime import datetime
        from config import DATABASE_PATH
        
        report_id = str(uuid.uuid4())[:8]
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute("""
                INSERT INTO chapter_reports (id, user_id, username, first_name, subject, lesson_num, chapter_idx, report, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """, (report_id, int(user_id), username, first_name, subject, int(lesson_num), int(chapter_idx), report_text, datetime.now().isoformat()))
            await db_conn.commit()
            
        # Send Telegram notification to backup bot admins
        try:
            from config import TELEGRAM_ADMIN_IDS
            admins = TELEGRAM_ADMIN_IDS
            if not admins:
                admins = [2045194295]
                
            subj_ar = subject
            if subject == 'fiqh': subj_ar = 'Ø§Ù„ÙÙ‚Ù‡'
            elif subject == 'aqeeda': subj_ar = 'Ø§Ù„Ø¹Ù‚ÙŠدة'
            elif subject == 'sira': subj_ar = 'Ø§Ù„Ø³ÙŠرة'
            elif subject == 'tajweed': subj_ar = 'Ø§Ù„ØªØ¬ÙˆÙŠد'
            elif subject == 'nahw': subj_ar = 'Ø§Ù„Ù†حو'
            
            chapter_title = f"Ø§Ù„Ù…Ø­Ùˆر {chapter_idx + 1}"
            try:
                with open('dashboard/transcripts.json', 'r', encoding='utf-8') as f:
                    lessons = json.load(f)
                    lesson = next((l for l in lessons if l.get('subject') == subject and l.get('lessonNum') == lesson_num), None)
                    if lesson and 'thematic_blocks' in lesson and len(lesson['thematic_blocks']) > chapter_idx:
                        chapter_title = lesson['thematic_blocks'][chapter_idx].get('title', chapter_title)
            except Exception:
                pass
            
            notif_msg = (
                f"ðŸš© <b>[Ø§Ù„Ø¨Ùˆت Ø§Ù„Ø¨Ø¯ÙŠÙ„] Ø¨Ù„اغ Ø¬Ø¯ÙŠد Ø¹Ù† خطأ ÙÙŠ Ø§Ù„Ù…Ø­ØªÙˆÙ‰</b>\n"
                f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                f"ðŸ‘¤ Ø§Ù„Ø·Ø§Ù„ب: <b>{first_name}</b> (@{username})\n"
                f"ðŸ“ Ø§Ù„Ù…ادة: <b>{subj_ar}</b> â† درس {lesson_num} â† <b>{chapter_title}</b>\n\n"
                f"ðŸ“ <b>Ù…Ù„احظة Ø§Ù„Ø·Ø§Ù„ب:</b>\n"
                f"<i>\"{report_text}\"</i>\n"
                f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                f"ðŸ‘‰ ÙŠÙ…ÙƒÙ†Ùƒ Ù…راجعة Ø§Ù„Ø¨Ù„اغ ÙˆØªØ¹Ø¯ÙŠÙ„ Ø§Ù„Ù…Ø­ØªÙˆÙ‰ Ù…باشرة Ù…Ù† Ù„Ùˆحة Ø§Ù„ØªØ­ÙƒÙ… Ø¨Ø§Ù„Ù…Ù„Ù Ø§Ù„Ø´Ø®ØµÙŠ ÙÙŠ ØªØ·Ø¨ÙŠÙ‚ Ø§Ù„ÙˆÙŠب."
            )
            
            bot = request.app['bot']
            for adm in admins:
                try:
                    await bot.send_message(adm, notif_msg, parse_mode="HTML")
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error sending telegram admin notification: {e}")
            
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return web.Response(status=500)

async def get_media(request):
    try:
        file_id = request.query.get('file_id')
        if not file_id:
            return web.json_response({"success": False, "error": "Missing file_id"}, status=400)
            
        bot = request.app.get('bot')
        if not bot:
            return web.json_response({"success": False, "error": "Bot instance not found"}, status=500)
            
        file_info = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_info.file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
            
        return web.Response(body=file_bytes.read(), content_type=mime_type)
    except Exception as e:
        logger.error(f"Error serving media: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: List pending content reports
async def get_admin_reports(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        role = await get_admin_role(user_id)
        if role in ["support_admin", "tech_admin"]:
            return web.json_response({"success": True, "reports": []})
            
        reports = []
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute("""
                SELECT cr.id, cr.user_id, cr.username, cr.first_name, cr.subject, cr.lesson_num, 
                       cr.chapter_idx, cr.report, cr.status, cr.admin_reply, cr.timestamp,
                       u.academic_year, cr.source, cr.contact_info, cr.claimed_by, cr.tags, cr.media_file_id, cr.media_type
                FROM chapter_reports cr
                LEFT JOIN users u ON cr.user_id = u.telegram_id
                ORDER BY cr.timestamp DESC
            """) as cur:
                async for r in cur:
                    reports.append({
                        "id": r["id"],
                        "userId": r["user_id"],
                        "username": r["username"],
                        "firstName": r["first_name"],
                        "subject": r["subject"],
                        "lessonNum": r["lesson_num"],
                        "chapterIdx": r["chapter_idx"],
                        "report": r["report"],
                        "status": r["status"],
                        "adminReply": r["admin_reply"] or "",
                        "timestamp": r["timestamp"],
                        "academicYear": r["academic_year"],
                        "source": r["source"] or "telegram",
                        "contactInfo": r["contact_info"] or "",
                        "claimedBy": r["claimed_by"] or "",
                        "tags": json.loads(r["tags"] or "[]"),
                        "mediaFileId": r["media_file_id"] or "",
                        "mediaType": r["media_type"] or ""
                    })
        return web.json_response({"success": True, "reports": reports})
    except Exception as e:
        logger.error(f"Error loading reports: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def get_admin_dashboard_stats_api(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        import database as db
        stats = await db.get_dashboard_stats()
        return web.json_response({"success": True, "stats": stats})
    except Exception as e:
        logger.error(f"Error loading dashboard stats: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Resolve a report
async def resolve_admin_report(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        report_id = data.get('reportId')
        admin_reply = data.get('adminReply', '')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            
            # Fetch report details to notify the student
            async with db_conn.execute("SELECT user_id, report, subject, lesson_num FROM chapter_reports WHERE id = ?", (report_id,)) as cur:
                report_row = await cur.fetchone()
                
            if not report_row:
                return web.json_response({"success": False, "error": "Report not found"}, status=404)
                
            await db_conn.execute(
                "UPDATE chapter_reports SET status = 'resolved', admin_reply = ?, reviewed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (admin_reply, report_id)
            )
            await db_conn.commit()
            
            # Notify student on Telegram
            bot = request.app['bot']
            try:
                subj_map = {
                    "aqida": "Ø§Ù„Ø¹Ù‚ÙŠدة",
                    "fiqh": "Ø§Ù„ÙÙ‚Ù‡",
                    "sira": "Ø§Ù„Ø³ÙŠرة",
                    "hadith": "Ø§Ù„Ø­Ø¯ÙŠث",
                    "tazkiyah": "Ø§Ù„ØªØ²ÙƒÙŠة"
                }
                subj_ar = subj_map.get(report_row['subject'].lower(), report_row['subject'])
                
                notif = (
                    f"ðŸ”” <b>ØªØ­Ø¯ÙŠث Ø¨Ø®ØµÙˆص Ø¨Ù„Ø§ØºÙƒ Ø¹Ù† خطأ ÙÙŠ Ø§Ù„Ù…Ø­ØªÙˆÙ‰</b>\n"
                    f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                    f"ðŸ“ Ø§Ù„Ù…ادة: <b>{subj_ar}</b> â† درس {report_row['lesson_num']}\n"
                    f"ðŸ“ Ø¨Ù„اغك: <i>\"{report_row['report']}\"</i>\n\n"
                    f"âœ… <b>رد Ø§Ù„إدارة:</b>\n"
                    f"<i>\"{admin_reply}\"</i>\n"
                    f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                    f"Ø´ÙƒØ±Ø§Ù‹ Ù„Ù…Ø³Ø§Ø¹Ø¯ØªÙƒ ÙÙŠ Ø¨Ù†اء Ø§Ù„Ø£ÙƒØ§Ø¯ÙŠÙ…ÙŠة!"
                )
                await bot.send_message(report_row['user_id'], notif, parse_mode="HTML")
            except Exception as notify_err:
                logger.error(f"Error notifying student for report resolution: {notify_err}")
            
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error resolving report: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Edit course transcription text
async def edit_course_chapter(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        subject = data.get('subject')
        lesson_num = data.get('lessonNum')
        chapter_idx = data.get('chapterIdx')
        new_title = data.get('newTitle')
        new_text = data.get('newText')
        if new_text is None:
            new_text = data.get('content')
        new_video_url = data.get('newVideoUrl')
        new_poetry = data.get('newPoetry')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        lessons = await load_lessons_from_db()
        if lessons is not None:
            lesson = next((l for l in lessons if l.get('subject') == subject and l.get('lessonNum') == lesson_num), None)
            if lesson and 'thematic_blocks' in lesson and len(lesson['thematic_blocks']) > chapter_idx:
                block = lesson['thematic_blocks'][chapter_idx]
                if new_title is not None:
                    block['title'] = new_title
                if new_text is not None:
                    block['explanation'] = new_text
                if new_video_url is not None:
                    block['video_link'] = new_video_url
                if new_poetry is not None:
                    block['poetry_verses'] = new_poetry
                
                await save_lesson_to_db(subject, lesson_num, lesson)
                    
                # Sync with SQLite DB
                try:
                    import database as db
                    import re
                    timestamp_seconds = None
                    final_url = new_video_url if new_video_url is not None else block.get('video_link')
                    if final_url:
                        m = re.search(r'[?&]t=(\d+)s?', final_url)
                        if m:
                            timestamp_seconds = int(m.group(1))
                    
                    await db.add_course_chapter(
                        subject=subject,
                        course_number=int(lesson_num),
                        chapter_index=int(chapter_idx) + 1,
                        title=new_title if new_title is not None else block.get('title', ''),
                        content=new_text if new_text is not None else (block.get('explanation') or block.get('content') or block.get('search_text', '')),
                        youtube_link=final_url,
                        timestamp_seconds=timestamp_seconds,
                        poetry_verses=new_poetry if new_poetry is not None else block.get('poetry_verses')
                    )
                except Exception as db_err:
                    logger.error(f"Database sync failed in edit_course_chapter: {db_err}")
                    
                # Sync to prod folder if exists
                prod_transcripts = 'C:/Users/Houssam/Desktop/telegram-dashboard/transcripts.json'
                if os.path.exists(prod_transcripts):
                    with open(prod_transcripts, 'w', encoding='utf-8') as pf:
                        json.dump(lessons, pf, ensure_ascii=False, indent=4)
                        
                    # Optional Git auto push
                    try:
                        import subprocess
                        subprocess.run(["git", "add", "transcripts.json"], cwd="C:/Users/Houssam/Desktop/telegram-dashboard", check=True)
                        subprocess.run(["git", "commit", "-m", f"[Backup Bot] Admin edit {subject} course {lesson_num} chapter {chapter_idx}"], cwd="C:/Users/Houssam/Desktop/telegram-dashboard", check=True)
                        subprocess.run(["git", "push", "origin", "main"], cwd="C:/Users/Houssam/Desktop/telegram-dashboard", check=True)
                    except Exception as git_err:
                        logger.error(f"Git auto-deploy failed: {git_err}")
                        
                return web.json_response({"success": True})
            else:
                return web.json_response({"success": False, "error": "Chapter not found"}, status=404)
        else:
            return web.json_response({"success": False, "error": "Transcripts file not found"}, status=500)
    except Exception as e:
        logger.error(f"Error in edit_course_chapter: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def save_lesson_axes(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        subject = data.get('subject')
        lesson_num = data.get('lessonNum')
        axes = data.get('thematicBlocks', [])
        
        if user_id is not None:
            user_id = int(user_id)
        
        if lesson_num is not None:
            try:
                lesson_num = int(lesson_num)
            except (TypeError, ValueError):
                pass

        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        lessons = await load_lessons_from_db()
        if lessons is not None:
            lesson = next((l for l in lessons if l.get('subject') == subject and int(l.get('lessonNum', -1)) == int(lesson_num)), None)
            if lesson:
                # Update thematic blocks array in JSON
                new_blocks = []
                for ax in axes:
                    video_url = ax.get("video_link", "")
                    timestamp_seconds = None
                    if video_url:
                        m = re.search(r'[?&]t=(\d+)s?', video_url)
                        if m:
                            timestamp_seconds = int(m.group(1))
                            
                    start_sec = ax.get("start_seconds")
                    if start_sec is None:
                        start_sec = timestamp_seconds
                    else:
                        try:
                            start_sec = int(start_sec)
                        except (TypeError, ValueError):
                            start_sec = timestamp_seconds

                    ts_val = ax.get("timestamp")
                    if not ts_val and start_sec is not None:
                        m_val = start_sec // 60
                        s_val = start_sec % 60
                        ts_val = f"{m_val}:{s_val:02d}"

                    new_blocks.append({
                        "title": ax.get("title", ""),
                        "explanation": ax.get("explanation", ""),
                        "video_link": video_url,
                        "poetry_verses": ax.get("poetry_verses", ""),
                        "search_text": ax.get("search_text", ""),
                        "start_seconds": start_sec,
                        "end_seconds": ax.get("end_seconds"),
                        "timestamp": ts_val or "",
                        "citation": ax.get("citation", "")
                    })
                lesson['thematic_blocks'] = new_blocks
                
                await save_lesson_to_db(subject, lesson_num, lesson)
                    
                # Sync to database: DELETE existing and INSERT/REPLACE all
                try:
                    import database as db
                    import aiosqlite
                    from config import DATABASE_PATH
                    
                    async with aiosqlite.connect(DATABASE_PATH) as conn:
                        await conn.execute("DELETE FROM course_chapters WHERE subject = ? AND course_number = ?", (subject.lower().strip(), int(lesson_num)))
                        await conn.commit()
                        
                    for idx, block in enumerate(new_blocks):
                        video_url = block.get('video_link')
                        timestamp_seconds = block.get('start_seconds')
                        
                        await db.add_course_chapter(
                            subject=subject,
                            course_number=int(lesson_num),
                            chapter_index=idx + 1,
                            title=block.get('title', ''),
                            content=block.get('explanation') or block.get('content') or block.get('search_text', ''),
                            youtube_link=video_url,
                            timestamp_seconds=timestamp_seconds,
                            poetry_verses=block.get('poetry_verses', '')
                        )
                except Exception as db_err:
                    logger.error(f"Database sync failed in save_lesson_axes: {db_err}")
                    
                # Sync to prod folder if exists
                prod_transcripts = 'C:/Users/Houssam/Desktop/telegram-dashboard/transcripts.json'
                if os.path.exists(prod_transcripts):
                    with open(prod_transcripts, 'w', encoding='utf-8') as pf:
                        json.dump(lessons, pf, ensure_ascii=False, indent=4)
                        
                    pass
                        
                return web.json_response({"success": True})
            else:
                return web.json_response({"success": False, "error": "Lesson not found"}, status=404)
        else:
            return web.json_response({"success": False, "error": "Transcripts file not found"}, status=500)
    except Exception as e:
        logger.error(f"Error in save_lesson_axes: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Generate thematic questions with Gemini
async def generate_questions_ia(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        subject = data.get('subject', '').strip()
        lesson_num = data.get('lessonNum')
        chapter_idx = data.get('chapterIdx', 0)
        theme = data.get('theme', '').strip()
        num_questions = int(data.get('numQuestions', 3))
        instructions = data.get('instructions', '').strip()
        model_name = data.get('model', 'gemini-flash-lite-latest')

        strategy = data.get('strategy', 'smart')
        specific_subtheme = data.get('specificSubtheme', '').strip()

        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        if not subject or lesson_num is None:
            return web.json_response({"success": False, "error": "ParamÃ¨tres manquants (matiÃ¨re ou numÃ©ro de leÃ§on)"}, status=400)

        # Reload GEMINI_API_KEYS fresh from config (ensures .env was loaded)
        import importlib
        import config as cfg_module
        importlib.reload(cfg_module)
        api_keys = getattr(cfg_module, "GEMINI_API_KEYS", [])
        if not api_keys and getattr(cfg_module, "GEMINI_API_KEY", ""):
            api_keys = [cfg_module.GEMINI_API_KEY]
        if not api_keys:
            return web.json_response({"success": False, "error": "ClÃ© API Gemini non configurÃ©e dans .env"}, status=500)

        # Find reference text from transcript JSON file
        transcripts_path = 'dashboard/transcripts.json'
        chapter_content = ""
        course_name = ""
        all_course_subthemes = []
        if os.path.exists(transcripts_path):
            with open(transcripts_path, 'r', encoding='utf-8') as f:
                lessons = json.load(f)
            # Normalize aqida <-> aqeeda
            subj_variants = [subject]
            if subject.lower() in ('aqida', 'aqeeda'):
                subj_variants = ['aqida', 'aqeeda']
            lesson_obj = next(
                (l for l in lessons
                 if l.get('subject') in subj_variants
                 and (l.get('lessonNum') == lesson_num or str(l.get('lessonNum')) == str(lesson_num))),
                None
            )
            if lesson_obj:
                course_name = lesson_obj.get('title', '')
                blocks = lesson_obj.get('thematic_blocks', [])
                all_course_subthemes = [b.get('title', '') for b in blocks if b.get('title')]
                if blocks:
                    if chapter_idx is not None and 0 <= int(chapter_idx) < len(blocks):
                        block = blocks[int(chapter_idx)]
                        chapter_content = block.get('explanation') or block.get('search_text') or ""
                        if not theme:
                            theme = block.get('title', '')
                    else:
                        # User selected "All lesson", concatenate all blocks
                        content_parts = []
                        for b in blocks:
                            text = b.get('explanation') or b.get('search_text') or ""
                            if text:
                                content_parts.append(f"--- {b.get('title', 'Ù…Ø­Ùˆر')} ---\n{text}")
                        chapter_content = "\n\n".join(content_parts)
                        if not theme:
                            theme = "Ø§Ù„درس ÙƒØ§Ù…Ù„Ø§Ù‹"

        # Construct specialized prompts based on subject
        subj_clean = subject.lower().strip()

        # Dynamic strategy instructions
        strategy_instr = ""
        if strategy == "specific" and specific_subtheme:
            strategy_instr = f"ÙŠجب Ø£Ù† ØªÙƒÙˆÙ† Ø¬Ù…ÙŠع Ø§Ù„Ø£Ø³Ø¦Ù„ة Ø§Ù„Ù…ÙˆÙ„دة Ù…Ø³ØªÙ‡Ø¯Ùة Ø¨Ø¯Ù‚ة Ù„Ù„Ù…Ø­Ùˆر Ø§Ù„ÙØ±Ø¹ÙŠ Ø§Ù„ØªØ§Ù„ÙŠ Ø­ØµØ±Ø§Ù‹: \"{specific_subtheme}\" ÙˆÙŠجب ØªØ¹ÙŠÙŠÙ† Ù‚ÙŠÙ…ة Ø§Ù„Ø­Ù‚Ù„ sub_theme Ù„ÙƒÙ„ Ø³Ø¤Ø§Ù„ Ø¥Ù„Ù‰ \"{specific_subtheme}\" ØªÙ…Ø§Ù…Ø§Ù‹."
        else:
            # Smart balanced strategy: prioritize axes with fewest existing questions
            if all_course_subthemes:
                try:
                    from config import DATABASE_PATH
                    import aiosqlite as _aio
                    subj_norm = subject.lower()
                    if subj_norm == 'aqeeda': subj_norm = 'aqida'
                    axe_counts = {}
                    async with _aio.connect(DATABASE_PATH) as _db:
                        async with _db.execute(
                            "SELECT sub_theme, COUNT(*) as cnt FROM questions WHERE LOWER(subject) IN (?, ?) AND course_number = ? GROUP BY sub_theme",
                            (subj_norm, 'aqeeda' if subj_norm == 'aqida' else subj_norm, int(lesson_num))
                        ) as _cur:
                            async for _row in _cur:
                                if _row[0]:
                                    axe_counts[_row[0]] = _row[1]
                    # Sort: axes with fewest questions first (0 = highest priority)
                    sorted_subthemes = sorted(all_course_subthemes, key=lambda st: axe_counts.get(st, 0))
                    counts_info = [f'"{st}" ({axe_counts.get(st, 0)} Ø£Ø³Ø¦Ù„ة)' for st in sorted_subthemes]
                    subthemes_list_str = "، ".join(counts_info)
                    strategy_instr = (
                        f"ÙŠجب ØªÙˆØ²ÙŠع Ø§Ù„Ø£Ø³Ø¦Ù„ة Ø§Ù„Ù€ {num_questions} Ø¨Ø´ÙƒÙ„ Ø°ÙƒÙŠ ÙˆÙ…ØªÙˆØ§Ø²Ù† Ø¹Ù„Ù‰ Ø§Ù„Ù…Ø­Ø§Ùˆر Ø§Ù„ÙØ±Ø¹ÙŠة Ø§Ù„ØªØ§Ù„ÙŠة Ù„Ù‡ذا Ø§Ù„Ø¯Ø±Ø³ØŒ "
                        f"Ù…ع Ø§Ù„Ø£ÙˆÙ„ÙˆÙŠة Ù„Ù„Ù…Ø­Ø§Ùˆر Ø§Ù„ØªÙŠ ØªÙ…ØªÙ„Ùƒ Ø£Ù‚Ù„ عدد Ù…Ù† Ø§Ù„Ø£Ø³Ø¦Ù„ة Ø­Ø§Ù„ÙŠØ§Ù‹ ÙÙŠ Ù‚اعدة Ø§Ù„Ø¨ÙŠØ§Ù†ات (ØªÙØ°Ùƒر Ø§Ù„أعداد Ø§Ù„Ø­Ø§Ù„ÙŠة Ù„Ù„إرشاد ÙÙ‚ط): "
                        f"[{subthemes_list_str}]. ØªØ£Ùƒد Ù…Ù† ØªØ¹ÙŠÙŠÙ† sub_theme Ù„ÙƒÙ„ Ø³Ø¤Ø§Ù„ Ø¨Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„ÙØ±Ø¹ÙŠ Ø§Ù„Ù…Ù†اسب Ù„Ù‡ Ø¨Ø§Ù„ضبط."
                    )
                except Exception as _ex:
                    logger.warning(f"Could not fetch axe counts for smart distribution: {_ex}")
                    subthemes_list_str = "، ".join([f'"{st}"' for st in all_course_subthemes])
                    strategy_instr = f"ÙŠجب ØªÙˆØ²ÙŠع Ø§Ù„Ø£Ø³Ø¦Ù„ة Ø§Ù„Ù€ {num_questions} Ø¨Ø´ÙƒÙ„ Ù…ØªÙˆØ§Ø²Ù† Ù„ØªØºØ·ÙŠة Ø£Ùƒبر Ù‚در Ù…Ù…ÙƒÙ† Ù…Ù† Ø§Ù„Ù…Ø­Ø§Ùˆر Ø§Ù„ÙØ±Ø¹ÙŠة Ø§Ù„ØªØ§Ù„ÙŠة: [{subthemes_list_str}]. ØªØ£Ùƒد Ø£Ù† ØªØ¹ÙŠÙ† Ù„ÙƒÙ„ Ø³Ø¤Ø§Ù„ Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„ÙØ±Ø¹ÙŠ Ø§Ù„Ù…Ù†اسب Ù„Ù‡ Ù…Ù† Ø§Ù„Ù‚Ø§Ø¦Ù…ة ÙÙŠ Ø­Ù‚Ù„ sub_theme."
            else:
                strategy_instr = "Ù‚Ù… Ø¨ØªÙˆØ²ÙŠع Ø§Ù„Ø£Ø³Ø¦Ù„ة Ù„ØªØºØ·ÙŠ Ø¬Ø²Ø¦ÙŠات ÙØ±Ø¹ÙŠة Ù…ØªÙ†Ùˆعة ÙˆÙ…Ø®ØªÙ„Ùة Ù…Ù† Ø§Ù„Ø¯Ø±Ø³ØŒ ÙˆØ¹ÙŠÙ‘Ù† Ù‚ÙŠÙ…ة sub_theme Ø¨Ø´ÙƒÙ„ Ù…عبر Ù„ÙƒÙ„ Ø³Ø¤Ø§Ù„."

        if subj_clean in ("fiqh", "Ø§Ù„ÙÙ‚Ù‡"):
            prompt = f"""Ø£Ù†ت Ø®Ø¨ÙŠر ÙÙŠ Ø§Ù„ÙÙ‚Ù‡ Ø§Ù„Ø¥Ø³Ù„Ø§Ù…ÙŠ (Ø§Ù„Ù…Ø°Ù‡ب Ø§Ù„Ù…Ø§Ù„ÙƒÙŠ) ÙˆÙ…ØµÙ…Ù… اختبارات ØªØ¹Ù„ÙŠÙ…ÙŠة.
Ù‚Ù… Ø¨ØªÙˆÙ„ÙŠد {num_questions} Ø£Ø³Ø¦Ù„ة Ø§Ø®ØªÙŠار Ù…Ù† Ù…تعدد (QCM) Ø¨Ø§Ù„Ù„غة Ø§Ù„Ø¹Ø±Ø¨ÙŠة Ø§Ù„ÙØµØ­Ù‰.

Ø§Ù„Ù…ادة: Ø§Ù„ÙÙ‚Ù‡ Ø§Ù„Ø¥Ø³Ù„Ø§Ù…ÙŠ
Ø±Ù‚Ù… Ø§Ù„درس: {lesson_num}
Ø§Ø³Ù… Ø§Ù„درس: {course_name or f'Ø§Ù„درس {lesson_num}'}
Ø§Ù„Ù…ÙˆØ¶Ùˆع/Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ù†شط: {theme or 'Ø¹Ø§Ù…'}
Ø§Ù„Ù†ص Ø§Ù„Ù…Ø±Ø¬Ø¹ÙŠ Ù„Ù„درس:
{chapter_content or 'Ù„ا ÙŠÙˆجد Ù†ص Ù…Ø±Ø¬Ø¹ÙŠ - Ø§Ø¹ØªÙ…د Ø¹Ù„Ù‰ Ù…Ø¹Ø±ÙØªÙƒ Ø§Ù„Ø¹Ø§Ù…ة Ø¨Ø§Ù„Ù…ادة'}

Ø§Ù„ØªØ¹Ù„ÙŠÙ…ات Ø§Ù„Ø¥Ø¶Ø§ÙÙŠة:
{instructions if instructions else 'Ù„ا ØªÙˆجد ØªØ¹Ù„ÙŠÙ…ات خاصة'}

Ø¥Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠة Ø§Ù„ØªÙˆØ²ÙŠع Ø§Ù„Ù…Ø³ØªÙ‡Ø¯Ùة:
{strategy_instr}

Ø´Ø±Ùˆط ØµØ§Ø±Ù…ة Ù„Ù„ØªÙˆÙ„ÙŠد:
1. ÙƒÙ„ Ø³Ø¤Ø§Ù„ ÙŠØ­ØªÙˆÙŠ Ø¹Ù„Ù‰ 4 Ø®ÙŠارات (أ ب ج د) Ø¨Ø§Ù„Ù„غة Ø§Ù„Ø¹Ø±Ø¨ÙŠة.
2. إجابة ØµØ­ÙŠحة Ùˆاحدة ÙÙ‚ط.
3. Ø£Ø¶Ù Ø´Ø±Ø­Ø§Ù‹ Ø¹Ù„Ù…ÙŠØ§Ù‹ Ù…ÙˆØ¬Ø²Ø§Ù‹ ÙˆØ¯Ù‚ÙŠÙ‚Ø§Ù‹ Ù„ÙƒÙ„ Ø³Ø¤Ø§Ù„ ÙŠÙˆضح سبب صحة Ø§Ù„Ø®ÙŠار Ø§Ù„Ù…ختار.
4. **Ø­Ù‚Ù„ Ø§Ù„Ù€ theme (Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ø¹Ø§Ù… Ù„Ù„درس)**: ÙŠجب Ø£Ù† ÙŠحدد Ø¨Ø¯Ù‚ة أحد Ø§Ù„Ù…Ø­Ø§Ùˆر Ø§Ù„تسعة Ø§Ù„ØªØ§Ù„ÙŠة Ø­ØµØ±Ø§Ù‹ Ù„ÙŠÙƒÙˆÙ† Ù…ØªÙˆØ§ÙÙ‚Ø§Ù‹ Ù…ع Ø§Ù„Ù…Ù†صة (اختر Ø§Ù„Ø£Ùƒثر Ù…Ù„Ø§Ø¡Ù…ة Ù„Ù…ÙˆØ¶Ùˆع Ø§Ù„Ø³Ø¤Ø§Ù„):
[Ùرائض Ø§Ù„ØµÙ„Ø§Ø©ØŒ Ø´Ø±Ùˆط Ø§Ù„ØµÙ„Ø§Ø©ØŒ Ø³Ù†Ù† Ø§Ù„ØµÙ„Ø§Ø©ØŒ Ù…Ù†Ø¯Ùˆبات Ø§Ù„ØµÙ„Ø§Ø©ØŒ Ù…ÙƒØ±ÙˆÙ‡ات ÙˆÙ…Ø¨Ø·Ù„ات Ø§Ù„ØµÙ„Ø§Ø©ØŒ ØµÙ„اة Ø§Ù„Ø¬Ù…Ø¹Ø©ØŒ Ø³Ø¬Ùˆد Ø§Ù„Ø³Ù‡ÙˆØŒ Ùرض Ø¹ÙŠÙ† / Ùرض ÙƒÙØ§ÙŠØ©ØŒ Ø´Ø±Ùˆط Ø§Ù„Ø¥Ù…Ø§Ù…]
5. **Ø­Ù‚Ù„ Ø§Ù„Ù€ sub_theme (Ø§Ù„Ø¬Ø²Ø¦ÙŠة Ø§Ù„Ø¯Ù‚ÙŠÙ‚ة / Ø§Ù„Ø¹Ù†ÙˆØ§Ù† Ø§Ù„ÙØ±Ø¹ÙŠ Ø§Ù„خاص)**: ÙŠجب Ø£Ù† ÙŠحدد Ø¨Ø¯Ù‚ة Ø§Ø³Ù… Ø§Ù„شرط Ø£Ùˆ Ø§Ù„Ùرض Ø£Ùˆ Ø§Ù„Ø¬Ø²Ø¦ÙŠة Ø§Ù„Ù…حددة Ø§Ù„ØªÙŠ ÙŠØ¯Ùˆر Ø­ÙˆÙ„Ù‡ا Ø§Ù„Ø³Ø¤Ø§Ù„ Ù…Ù† Ø§Ù„Ù†ص Ø§Ù„Ù…Ø±Ø¬Ø¹ÙŠ (Ù…Ø«Ø§Ù„: "ستر Ø§Ù„Ø¹Ùˆرة"ØŒ "Ø§Ø³ØªÙ‚Ø¨Ø§Ù„ Ø§Ù„Ù‚Ø¨Ù„ة"ØŒ "Ø·Ù‡ارة Ø§Ù„حدث"ØŒ "Ø§Ù„Ù†ÙŠة"ØŒ "ØªÙƒØ¨ÙŠرة Ø§Ù„Ø¥Ø­Ø±Ø§Ù…"...). Ù„ا ØªØªØ±ÙƒÙ‡ ÙØ§Ø±ØºØ§Ù‹ ÙˆÙ„ا ØªÙƒØ±Ø±Ù‡ ÙƒØ§Ø³Ù… Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ø¹Ø§Ù… Ù†ÙØ³Ù‡.

أعد Ø§Ù„Ù†ØªÙŠجة ÙƒÙ€ JSON ÙÙ‚ط (Ù…ØµÙÙˆÙة) Ø¨Ø§Ù„Ø´ÙƒÙ„ Ø§Ù„ØªØ§Ù„ÙŠ Ø¨Ø¯ÙˆÙ† Ø£ÙŠ Ù†ص Ø¥Ø¶Ø§ÙÙŠ:
[
  {{
    "question": "Ù†ص Ø§Ù„Ø³Ø¤Ø§Ù„ Ø§Ù„ÙÙ‚Ù‡ÙŠ Ø§Ù„Ø¯Ù‚ÙŠÙ‚",
    "choice_a": "Ø§Ù„Ø®ÙŠار أ",
    "choice_b": "Ø§Ù„Ø®ÙŠار ب",
    "choice_c": "Ø§Ù„Ø®ÙŠار ج",
    "choice_d": "Ø§Ù„Ø®ÙŠار د",
    "correct_answer": "a",
    "explanation": "شرح Ø§Ù„إجابة Ø§Ù„ÙÙ‚Ù‡ÙŠة Ø¨Ø§Ù„ØªÙØµÙŠÙ„",
    "theme": "Ø´Ø±Ùˆط Ø§Ù„ØµÙ„اة",
    "sub_theme": "ستر Ø§Ù„Ø¹Ùˆرة"
  }}
]"""
        elif subj_clean in ("sira", "Ø§Ù„Ø³ÙŠرة"):
            prompt = f"""Ø£Ù†ت Ø®Ø¨ÙŠر ÙÙŠ Ø§Ù„Ø³ÙŠرة Ø§Ù„Ù†Ø¨ÙˆÙŠة ÙˆÙ…ØµÙ…Ù… اختبارات ØªØ¹Ù„ÙŠÙ…ÙŠة.
Ù‚Ù… Ø¨ØªÙˆÙ„ÙŠد {num_questions} Ø£Ø³Ø¦Ù„ة Ø§Ø®ØªÙŠار Ù…Ù† Ù…تعدد (QCM) Ø¨Ø§Ù„Ù„غة Ø§Ù„Ø¹Ø±Ø¨ÙŠة Ø§Ù„ÙØµØ­Ù‰.

Ø§Ù„Ù…ادة: Ø§Ù„Ø³ÙŠرة Ø§Ù„Ù†Ø¨ÙˆÙŠة
Ø±Ù‚Ù… Ø§Ù„درس: {lesson_num}
Ø§Ø³Ù… Ø§Ù„درس: {course_name or f'Ø§Ù„درس {lesson_num}'}
Ø§Ù„Ù…ÙˆØ¶Ùˆع/Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ù†شط: {theme or 'Ø¹Ø§Ù…'}
Ø§Ù„Ù†ص Ø§Ù„Ù…Ø±Ø¬Ø¹ÙŠ Ù„Ù„درس:
{chapter_content or 'Ù„ا ÙŠÙˆجد Ù†ص Ù…Ø±Ø¬Ø¹ÙŠ - Ø§Ø¹ØªÙ…د Ø¹Ù„Ù‰ Ù…Ø¹Ø±ÙØªÙƒ Ø§Ù„Ø¹Ø§Ù…ة Ø¨Ø§Ù„Ù…ادة'}

Ø§Ù„ØªØ¹Ù„ÙŠÙ…ات Ø§Ù„Ø¥Ø¶Ø§ÙÙŠة:
{instructions if instructions else 'Ù„ا ØªÙˆجد ØªØ¹Ù„ÙŠÙ…ات خاصة'}

Ø¥Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠة Ø§Ù„ØªÙˆØ²ÙŠع Ø§Ù„Ù…Ø³ØªÙ‡Ø¯Ùة:
{strategy_instr}

Ø´Ø±Ùˆط ØµØ§Ø±Ù…ة Ù„Ù„ØªÙˆÙ„ÙŠد:
1. ÙƒÙ„ Ø³Ø¤Ø§Ù„ ÙŠØ­ØªÙˆÙŠ Ø¹Ù„Ù‰ 4 Ø®ÙŠارات (أ ب ج د) Ø¨Ø§Ù„Ù„غة Ø§Ù„Ø¹Ø±Ø¨ÙŠة.
2. إجابة ØµØ­ÙŠحة Ùˆاحدة ÙÙ‚ط.
3. Ø£Ø¶Ù Ø´Ø±Ø­Ø§Ù‹ Ø¹Ù„Ù…ÙŠØ§Ù‹ Ù…ÙˆØ¬Ø²Ø§Ù‹ ÙˆØ¯Ù‚ÙŠÙ‚Ø§Ù‹ Ù„ÙƒÙ„ Ø³Ø¤Ø§Ù„ ÙŠÙˆضح سبب صحة Ø§Ù„Ø®ÙŠار Ø§Ù„Ù…ختار.
4. **Ø­Ù‚Ù„ Ø§Ù„Ù€ theme (Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„رئيسي)**: ÙŠجب Ø£Ù† ÙŠحدد Ø¨Ø¯Ù‚ة أحد Ø§Ù„Ù…Ø­Ø§Ùˆر Ø§Ù„ستة Ø§Ù„ØªØ§Ù„ÙŠة Ø­ØµØ±Ø§Ù‹ Ù„ÙŠÙƒÙˆÙ† Ù…ØªÙˆØ§ÙÙ‚Ø§Ù‹ Ù…ع Ø§Ù„Ù…Ù†صة:
[Ø§Ù„ØºØ²Ùˆات ÙˆØ§Ù„Ø³Ø±Ø§ÙŠØ§ØŒ Ø¨ÙŠت Ø§Ù„Ù†Ø¨Ùˆة ÙˆØ§Ù„Ø­ÙŠاة Ø§Ù„Ø´Ø®ØµÙŠØ©ØŒ Ø§Ù„عبادات ÙˆØ§Ù„Ù…Ø¹Ø§Ù…Ù„ات ÙˆØ§Ù„ØªØ´Ø±ÙŠØ¹Ø§ØªØŒ Ø§Ù„صحابة ÙˆØ§Ù„Ù…Ø¬ØªÙ…ع Ø§Ù„Ù…Ø¯Ù†ÙŠØŒ Ø§Ù„Ø¹Ù‡Ùˆد ÙˆØ§Ù„ÙˆÙÙˆد ÙˆØ§Ù„Ø¹Ù„Ø§Ù‚ات Ø§Ù„Ø®Ø§Ø±Ø¬ÙŠØ©ØŒ Ø§Ù„Ø´Ù…Ø§Ø¦Ù„ ÙˆØ§Ù„Ø£Ø®Ù„Ø§Ù‚ Ø§Ù„Ù†Ø¨ÙˆÙŠة]
5. **Ø­Ù‚Ù„ Ø§Ù„Ù€ sub_theme (Ø§Ù„Ø¬Ø²Ø¦ÙŠة Ø§Ù„Ø¯Ù‚ÙŠÙ‚ة / Ø§Ù„Ø¹Ù†ÙˆØ§Ù† Ø§Ù„ÙØ±Ø¹ÙŠ Ø§Ù„خاص)**: ÙŠجب Ø£Ù† ÙŠحدد Ø¨Ø¯Ù‚ة Ø§Ù„حدث Ø£Ùˆ Ø§Ù„Ù…ÙÙ‡ÙˆÙ… Ø§Ù„ÙØ±Ø¹ÙŠ Ø§Ù„Ù…حدد Ù„Ù„Ø³Ø¤Ø§Ù„ Ù…Ù† Ø§Ù„Ù†ص Ø§Ù„Ù…Ø±Ø¬Ø¹ÙŠ (Ù…Ø«Ø§Ù„: "ØºØ²Ùˆة بدر Ø§Ù„ÙƒØ¨Ø±Ù‰"ØŒ "ÙˆÙاة Ø²ÙŠÙ†ب Ø¨Ù†ت Ø®Ø²ÙŠÙ…ة"ØŒ "ØªØ­ÙˆÙŠÙ„ Ø§Ù„Ù‚Ø¨Ù„ة"...). Ù„ا ØªØªØ±ÙƒÙ‡ ÙØ§Ø±ØºØ§Ù‹.
6. **Ø­Ù‚Ù„ Ø§Ù„Ù€ hijra_year (Ø§Ù„Ø³Ù†ة Ø§Ù„Ù‡Ø¬Ø±ÙŠة)**: حدد Ø§Ù„Ø³Ù†ة Ø§Ù„Ù‡Ø¬Ø±ÙŠة Ø§Ù„ØªÙŠ ÙˆÙ‚ع ÙÙŠÙ‡ا Ù‡ذا Ø§Ù„حدث Ø¨Ø¯Ù‚ة Ùƒعدد ØµØ­ÙŠح (Ø¥Ù†تجر) (Ù…Ø«Ø§Ù„: 2 Ù„ØºØ²Ùˆة Ø¨Ø¯Ø±ØŒ 3 Ù„ØºØ²Ùˆة Ø£Ø­Ø¯ØŒ 9 Ù„ØºØ²Ùˆة ØªØ¨ÙˆÙƒ). إذا Ù„Ù… ÙŠÙƒÙ† Ù„Ù„Ø³Ø¤Ø§Ù„ ØªØ§Ø±ÙŠخ Ù‡Ø¬Ø±ÙŠ Ù…حدد ضع null.

أعد Ø§Ù„Ù†ØªÙŠجة ÙƒÙ€ JSON ÙÙ‚ط (Ù…ØµÙÙˆÙة) Ø¨Ø§Ù„Ø´ÙƒÙ„ Ø§Ù„ØªØ§Ù„ÙŠ Ø¨Ø¯ÙˆÙ† Ø£ÙŠ Ù†ص Ø¥Ø¶Ø§ÙÙŠ:
[
  {{
    "question": "Ù†ص Ø§Ù„Ø³Ø¤Ø§Ù„ Ø§Ù„ØªØ§Ø±ÙŠØ®ÙŠ Ø§Ù„Ø¯Ù‚ÙŠÙ‚",
    "choice_a": "Ø§Ù„Ø®ÙŠار أ",
    "choice_b": "Ø§Ù„Ø®ÙŠار ب",
    "choice_c": "Ø§Ù„Ø®ÙŠار ج",
    "choice_d": "Ø§Ù„Ø®ÙŠار د",
    "correct_answer": "a",
    "explanation": "شرح Ø§Ù„إجابة Ø§Ù„ØªØ§Ø±ÙŠØ®ÙŠة Ø¨Ø§Ù„ØªÙØµÙŠÙ„",
    "theme": "Ø§Ù„ØºØ²Ùˆات ÙˆØ§Ù„Ø³Ø±Ø§ÙŠا",
    "sub_theme": "ØºØ²Ùˆة بدر Ø§Ù„ÙƒØ¨Ø±Ù‰",
    "hijra_year": 2
  }}
]"""
        elif subj_clean in ("nahw", "Ø§Ù„Ù†حو"):
            calculated_theme = "باب Ø§Ù„Ù…Ø±ÙÙˆعات"
            try:
                l_num = int(lesson_num)
                if l_num == 14:
                    calculated_theme = "باب Ø§Ù„Ù†Ùƒرة ÙˆØ§Ù„Ù…Ø¹Ø±Ùة"
                elif l_num == 21:
                    # Check active theme or block name
                    if theme and "Ø§Ù„Ù…ÙØ¹ÙˆÙ„" in theme:
                        calculated_theme = "باب Ø§Ù„Ù…Ù†ØµÙˆبات"
                    else:
                        calculated_theme = "باب Ø§Ù„Ù…Ø±ÙÙˆعات"
                elif l_num > 21:
                    calculated_theme = "باب Ø§Ù„Ù…Ù†ØµÙˆبات"
            except:
                pass

            prompt = f"""Ø£Ù†ت Ø®Ø¨ÙŠر ÙÙŠ Ø§Ù„Ù†Ø­Ùˆ Ø§Ù„Ø¹Ø±Ø¨ÙŠ ÙˆÙ…ØµÙ…Ù… اختبارات ØªØ¹Ù„ÙŠÙ…ÙŠة.
Ù‚Ù… Ø¨ØªÙˆÙ„ÙŠد {num_questions} Ø£Ø³Ø¦Ù„ة Ø§Ø®ØªÙŠار Ù…Ù† Ù…تعدد (QCM) Ø¨Ø§Ù„Ù„غة Ø§Ù„Ø¹Ø±Ø¨ÙŠة Ø§Ù„ÙØµØ­Ù‰.

Ø§Ù„Ù…ادة: Ø§Ù„Ù†Ø­Ùˆ
Ø±Ù‚Ù… Ø§Ù„درس: {lesson_num}
Ø§Ø³Ù… Ø§Ù„درس: {course_name or f'Ø§Ù„درس {lesson_num}'}
Ø§Ù„Ù…ÙˆØ¶Ùˆع/Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ù†شط: {theme or 'Ø¹Ø§Ù…'}
Ø§Ù„Ù†ص Ø§Ù„Ù…Ø±Ø¬Ø¹ÙŠ Ù„Ù„درس:
{chapter_content or 'Ù„ا ÙŠÙˆجد Ù†ص Ù…Ø±Ø¬Ø¹ÙŠ - Ø§Ø¹ØªÙ…د Ø¹Ù„Ù‰ Ù…Ø¹Ø±ÙØªÙƒ Ø§Ù„Ø¹Ø§Ù…ة Ø¨Ø§Ù„Ù…ادة'}

Ø´Ø±Ùˆط ØµØ§Ø±Ù…ة Ù„Ù„ØªÙˆÙ„ÙŠد:
1. ÙƒÙ„ Ø³Ø¤Ø§Ù„ ÙŠØ­ØªÙˆÙŠ Ø¹Ù„Ù‰ 4 Ø®ÙŠارات (أ ب ج د) Ø¨Ø§Ù„Ù„غة Ø§Ù„Ø¹Ø±Ø¨ÙŠة.
2. إجابة ØµØ­ÙŠحة Ùˆاحدة ÙÙ‚ط.
3. Ø£Ø¶Ù Ø´Ø±Ø­Ø§Ù‹ Ø¹Ù„Ù…ÙŠØ§Ù‹ Ù…ÙˆØ¬Ø²Ø§Ù‹ ÙˆØ¯Ù‚ÙŠÙ‚Ø§Ù‹ Ù„ÙƒÙ„ Ø³Ø¤Ø§Ù„ ÙŠÙˆضح سبب صحة Ø§Ù„Ø®ÙŠار Ø§Ù„Ù…ختار.
4. **Ø­Ù‚Ù„ Ø§Ù„Ù€ theme (Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ø¹Ø§Ù…)**: ÙŠجب Ø£Ù† ÙŠحدد Ø¨Ø¯Ù‚ة Ø§Ù„Ù‚ÙŠÙ…ة Ø§Ù„ØªØ§Ù„ÙŠة Ù„ÙŠÙƒÙˆÙ† Ù…ØªÙˆØ§ÙÙ‚Ø§Ù‹ Ù…ع Ø§Ù„Ù…Ù†صة:
"{calculated_theme}"
5. **Ø­Ù‚Ù„ Ø§Ù„Ù€ sub_theme (Ø§Ù„Ø¬Ø²Ø¦ÙŠة Ø§Ù„Ø¯Ù‚ÙŠÙ‚ة / Ø§Ù„Ø¹Ù†ÙˆØ§Ù† Ø§Ù„ÙØ±Ø¹ÙŠ Ø§Ù„خاص)**: ÙŠجب Ø£Ù† ÙŠØ·Ø§Ø¨Ù‚ Ø¨Ø¯Ù‚ة Ø§Ù„Ø¬Ø²Ø¦ÙŠة Ø§Ù„Ø¯Ù‚ÙŠÙ‚ة Ø§Ù„Ù†Ø­ÙˆÙŠة Ø§Ù„ØªÙŠ ÙŠØ¯Ùˆر Ø­ÙˆÙ„Ù‡ا Ø§Ù„Ø³Ø¤Ø§Ù„ Ù…Ù† Ø§Ù„Ù‚Ø§Ø¦Ù…ة Ø§Ù„ØªØ§Ù„ÙŠة Ø¨Ù†Ø§Ø¡Ù‹ Ø¹Ù„Ù‰ Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ø¹Ø§Ù…:
- إذا ÙƒØ§Ù† Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ø¹Ø§Ù… "باب Ø§Ù„Ù†Ùƒرة ÙˆØ§Ù„Ù…Ø¹Ø±Ùة"ØŒ اختر أحد Ø§Ù„Ø®ÙŠØ§Ø±ÙŠÙ†: ["Ø§Ù„Ø§Ø³Ù… Ø§Ù„Ù…ÙˆØµÙˆÙ„ ÙˆØµÙ„ØªÙ‡"ØŒ "Ø§Ù„Ù…Ø¹Ø±Ù‘Ù بأداة"]
- إذا ÙƒØ§Ù† Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ø¹Ø§Ù… "باب Ø§Ù„Ù…Ø±ÙÙˆعات"ØŒ اختر أحد Ø§Ù„Ø®ÙŠارات Ø§Ù„Ù†Ø­ÙˆÙŠة Ø§Ù„ØªØ§Ù„ÙŠة:
  ["Ø§Ù„ÙØ§Ø¹Ù„"ØŒ "Ø§Ù„Ù…ÙØ¹ÙˆÙ„ Ø§Ù„Ø°ÙŠ Ù„Ù… ÙŠØ³Ù… ÙØ§Ø¹Ù„Ù‡"ØŒ "Ø§Ù„Ù…بتدأ ÙˆØ§Ù„خبر"ØŒ "Ø§Ù„Ø¹ÙˆØ§Ù…Ù„ - ÙƒØ§Ù† ÙˆØ£Ø®ÙˆØ§ØªÙ‡ا"ØŒ "Ø§Ù„Ø¹ÙˆØ§Ù…Ù„ - Ø§Ù„Ø­Ø±ÙˆÙ Ø§Ù„Ù…Ø´Ø¨Ù‡ة Ø¨Ù€ \"Ù„ÙŠس\""ØŒ "Ø§Ù„Ø¹ÙˆØ§Ù…Ù„ - Ø£ÙØ¹Ø§Ù„ Ø§Ù„Ù…Ù‚اربة"ØŒ "Ø§Ù„Ø¹ÙˆØ§Ù…Ù„ - Ø¥Ù†Ù‘ ÙˆØ£Ø®ÙˆØ§ØªÙ‡ا"ØŒ "Ø§Ù„Ø¹ÙˆØ§Ù…Ù„ - Ù„ا Ø§Ù„Ù†Ø§ÙÙŠة Ù„Ù„Ø¬Ù†س"ØŒ "Ø§Ù„Ø¹ÙˆØ§Ù…Ù„ - Ø¸Ù†Ù‘ ÙˆØ£Ø®ÙˆØ§ØªÙ‡ا"]
- إذا ÙƒØ§Ù† Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ø¹Ø§Ù… "باب Ø§Ù„Ù…Ù†ØµÙˆبات"ØŒ اختر: ["Ø§Ù„Ù…ÙØ¹ÙˆÙ„ Ø¨Ù‡"]

أعد Ø§Ù„Ù†ØªÙŠجة ÙƒÙ€ JSON ÙÙ‚ط (Ù…ØµÙÙˆÙة) Ø¨Ø§Ù„Ø´ÙƒÙ„ Ø§Ù„ØªØ§Ù„ÙŠ Ø¨Ø¯ÙˆÙ† Ø£ÙŠ Ù†ص Ø¥Ø¶Ø§ÙÙŠ:
[
  {{
    "question": "Ù†ص Ø§Ù„Ø³Ø¤Ø§Ù„ Ø§Ù„Ù†Ø­ÙˆÙŠ Ø§Ù„Ø¯Ù‚ÙŠÙ‚",
    "choice_a": "Ø§Ù„Ø®ÙŠار أ",
    "choice_b": "Ø§Ù„Ø®ÙŠار ب",
    "choice_c": "Ø§Ù„Ø®ÙŠار ج",
    "choice_d": "Ø§Ù„Ø®ÙŠار د",
    "correct_answer": "a",
    "explanation": "شرح Ø§Ù„إجابة Ø§Ù„Ù†Ø­ÙˆÙŠة ÙˆØ§Ù„Ù‚اعدة Ø¨Ø§Ù„ØªÙØµÙŠÙ„",
    "theme": "{calculated_theme}",
    "sub_theme": "Ø§Ù„ÙØ§Ø¹Ù„"
  }}
]"""
        else:
            prompt = f"""Ø£Ù†ت Ø®Ø¨ÙŠر ÙÙŠ Ø§Ù„Ø¹Ù„ÙˆÙ… Ø§Ù„Ø¥Ø³Ù„Ø§Ù…ÙŠة ÙˆÙ…ØµÙ…Ù… اختبارات ØªØ¹Ù„ÙŠÙ…ÙŠة.
Ù‚Ù… Ø¨ØªÙˆÙ„ÙŠد {num_questions} Ø£Ø³Ø¦Ù„ة Ø§Ø®ØªÙŠار Ù…Ù† Ù…تعدد (QCM) Ø¨Ø§Ù„Ù„غة Ø§Ù„Ø¹Ø±Ø¨ÙŠة Ø§Ù„ÙØµØ­Ù‰.

Ø§Ù„Ù…ادة: {subject}
Ø±Ù‚Ù… Ø§Ù„درس: {lesson_num}
Ø§Ø³Ù… Ø§Ù„درس: {course_name or f'Ø§Ù„درس {lesson_num}'}
Ø§Ù„Ù…ÙˆØ¶Ùˆع/Ø§Ù„Ù…Ø­Ùˆر: {theme or 'Ø¹Ø§Ù…'}
Ø§Ù„Ù†ص Ø§Ù„Ù…Ø±Ø¬Ø¹ÙŠ Ù„Ù„درس:
{chapter_content or 'Ù„ا ÙŠÙˆجد Ù†ص Ù…رجعي'}

Ø§Ù„ØªØ¹Ù„ÙŠÙ…ات Ø§Ù„Ø¥Ø¶Ø§ÙÙŠة:
{instructions if instructions else 'Ù„ا ØªÙˆجد ØªØ¹Ù„ÙŠÙ…ات خاصة'}

Ø¥Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠة Ø§Ù„ØªÙˆØ²ÙŠع Ø§Ù„Ù…Ø³ØªÙ‡Ø¯Ùة:
{strategy_instr}

Ø´Ø±Ùˆط:
1. ÙƒÙ„ Ø³Ø¤Ø§Ù„ ÙŠØ­ØªÙˆÙŠ Ø¹Ù„Ù‰ 4 Ø®ÙŠارات (أ ب ج د).
2. إجابة ØµØ­ÙŠحة Ùˆاحدة ÙÙ‚ط.
3. Ø£Ø¶Ù Ø´Ø±Ø­Ø§Ù‹ Ø¹Ù„Ù…ÙŠØ§Ù‹ Ù…ÙˆØ¬Ø²Ø§Ù‹ Ù„ÙƒÙ„ Ø³Ø¤Ø§Ù„.

أعد Ø§Ù„Ù†ØªÙŠجة ÙƒÙ€ JSON ÙÙ‚ط (Ù…ØµÙÙˆÙة) Ø¨Ø§Ù„Ø´ÙƒÙ„ Ø§Ù„ØªØ§Ù„ÙŠ Ø¨Ø¯ÙˆÙ† Ø£ÙŠ Ù†ص Ø¥Ø¶Ø§ÙÙŠ:
[
  {{
    "question": "Ù†ص Ø§Ù„Ø³Ø¤Ø§Ù„",
    "choice_a": "Ø§Ù„Ø®ÙŠار أ",
    "choice_b": "Ø§Ù„Ø®ÙŠار ب",
    "choice_c": "Ø§Ù„Ø®ÙŠار ج",
    "choice_d": "Ø§Ù„Ø®ÙŠار د",
    "correct_answer": "a",
    "explanation": "شرح Ø§Ù„إجابة",
    "theme": "Ø§Ù„Ù…Ø­Ùˆر Ø§Ù„Ø¹Ø§Ù…",
    "sub_theme": "Ø§Ù„Ø¬Ø²Ø¦ÙŠة Ø§Ù„Ø¹Ø§Ù…ة"
  }}
]"""
        # --- Use exact same SDK pattern as handlers/admin.py ---
        import google.generativeai as genai

        # Valid model names for old SDK
        valid_models = ['gemini-flash-lite-latest', 'gemini-flash-latest', 'gemini-1.5-flash-latest',
                        'gemini-1.5-pro', 'gemini-2.0-flash', 'gemini-2.0-flash-lite',
                        'gemini-2.5-flash-preview-05-20', 'gemini-2.5-flash']
        if model_name not in valid_models:
            model_name = 'gemini-flash-lite-latest'

        response_text = None
        last_error = None
        for current_key in api_keys:
            try:
                genai.configure(api_key=current_key)
                model = genai.GenerativeModel(model_name)
                response = await model.generate_content_async(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                response_text = response.text.strip()
                if response_text:
                    # Clean markdown wrappers if present
                    if response_text.startswith("```"):
                        response_text = re.sub(r"^```json\s*", "", response_text)
                        response_text = re.sub(r"^```\s*", "", response_text)
                        response_text = re.sub(r"\s*```$", "", response_text)
                        response_text = response_text.strip()
                    break
            except Exception as ex:
                logger.warning(f"Failed generation with key {current_key[:10]}...: {ex}")
                last_error = ex
                continue

        if not response_text:
            raise last_error or Exception("Toutes les clÃ©s API ont Ã©chouÃ© lors de la gÃ©nÃ©ration.")

        questions = json.loads(response_text)
        if isinstance(questions, dict) and "questions" in questions:
            questions = questions["questions"]

        import json
        return web.json_response({"success": True, "questions": questions}, dumps=lambda obj: json.dumps(obj, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Error generating questions: {e}", exc_info=True)
        return web.json_response({"success": False, "error": str(e)}, status=500)



# Admin API: Bulk Save Questions
async def save_bulk_questions(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        subject = data.get('subject')
        lesson_num = data.get('lessonNum')
        questions = data.get('questions', [])

        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        if not subject or lesson_num is None or not questions:
            return web.json_response({"success": False, "error": "Missing parameters"}, status=400)

        # Get course name
        course_name = ""
        lessons = await load_lessons_from_db()
        if True:
            lesson = next((l for l in lessons if l.get('subject') == subject and l.get('lessonNum') == lesson_num), None)
            if lesson:
                course_name = lesson.get('title', '')

        import database as db
        inserted_count = 0
        for q in questions:
            # Parse hijra_year safely as integer or None
            hijra_val = q.get("hijra_year")
            try:
                hijra_year = int(hijra_val) if hijra_val is not None and str(hijra_val).strip() != "" else None
            except (ValueError, TypeError):
                hijra_year = None

            q_data = {
                "subject": subject,
                "course_number": int(lesson_num),
                "course_name": course_name,
                "question": q.get("question", "").strip(),
                "choice_a": q.get("choice_a", "").strip(),
                "choice_b": q.get("choice_b", "").strip(),
                "choice_c": q.get("choice_c", "").strip(),
                "choice_d": q.get("choice_d", "").strip(),
                "correct_answer": q.get("correct_answer", "a").strip().lower(),
                "explanation": q.get("explanation", "").strip(),
                "source": "ai_generated",
                "hijra_year": hijra_year,
                "theme": q.get("theme") or "",
                "sub_theme": q.get("sub_theme") or ""
            }
            if q_data["question"] and q_data["choice_a"]:
                await db.add_question_to_db(q_data)
                inserted_count += 1

        return web.json_response({"success": True, "inserted_count": inserted_count})
    except Exception as e:
        logger.error(f"Error saving bulk questions: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Save complete lesson segments
async def save_full_transcript(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        subject = data.get('subject')
        lesson_num = data.get('lessonNum')
        new_segments = data.get('segments')
        new_thematic_blocks = data.get('thematicBlocks')

        if lesson_num is not None:
            try:
                lesson_num = int(lesson_num)
            except (TypeError, ValueError):
                pass
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        if not subject or lesson_num is None or new_segments is None:
            return web.json_response({"success": False, "error": "Missing parameters"}, status=400)
            
        lessons = await load_lessons_from_db()
        if lessons is not None:
            lesson = next((l for l in lessons if l.get('subject') == subject and int(l.get('lessonNum', -1)) == int(lesson_num)), None)
            if lesson:
                lesson['segments'] = new_segments
                if new_thematic_blocks is not None:
                    lesson['thematic_blocks'] = new_thematic_blocks
                
                # Also rebuild full_text
                lesson['full_text'] = " ".join(seg.get('text', '') for seg in new_segments)
                
                await save_lesson_to_db(subject, lesson_num, lesson)
                    
                # Sync all thematic blocks to SQLite DB
                try:
                    import database as db
                    from config import DATABASE_PATH
                    import aiosqlite
                    async with aiosqlite.connect(DATABASE_PATH) as conn:
                        await conn.execute("DELETE FROM course_chapters WHERE subject = ? AND course_number = ?", (subject.lower().strip(), int(lesson_num)))
                        await conn.commit()
                    
                    if new_thematic_blocks:
                        for idx, block in enumerate(new_thematic_blocks):
                            new_video_url = block.get('video_link')
                            timestamp_seconds = block.get('start_seconds')
                            
                            await db.add_course_chapter(
                                subject=subject,
                                course_number=int(lesson_num),
                                chapter_index=idx + 1,
                                title=block.get('title', ''),
                                content=block.get('explanation') or block.get('content') or block.get('search_text', ''),
                                youtube_link=new_video_url,
                                timestamp_seconds=timestamp_seconds,
                                poetry_verses=block.get('poetry_verses')
                            )
                except Exception as db_err:
                    logger.error(f"Database sync failed in save_full_transcript: {db_err}")
                    
                # Sync to prod folder if exists
                prod_transcripts = 'C:/Users/Houssam/Desktop/telegram-dashboard/transcripts.json'
                if os.path.exists(prod_transcripts):
                    with open(prod_transcripts, 'w', encoding='utf-8') as pf:
                        json.dump(lessons, pf, ensure_ascii=False, indent=4)
                        
                    pass
                        
                return web.json_response({"success": True})
                
        return web.json_response({"success": False, "error": "Transcripts file not found"}, status=404)
    except Exception as e:
        logger.error(f"Error saving full transcript: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def get_admin_question(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        question_id = data.get('questionId')

        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
        if not question_id:
            return web.json_response({"success": False, "error": "Missing questionId"}, status=400)

        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute("SELECT id, subject, course_number, course_name, question, choice_a, choice_b, choice_c, choice_d, correct_answer, explanation, source, created_at, hijra_year, theme, is_active, sub_theme FROM questions WHERE id = ?", (int(question_id),)) as cur:
                row = await cur.fetchone()

        if not row:
            return web.json_response({"success": False, "error": "Question not found"}, status=404)

        q_dict = dict(row)
        if q_dict.get("source") == "student_proposal":
            async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                db_conn.row_factory = aiosqlite.Row
                async with db_conn.execute("SELECT first_name, username, user_id FROM questions_proposees WHERE question = ? OR (subject = ? AND course_number = ? AND question = ?) LIMIT 1", (q_dict["question"], q_dict["subject"], q_dict["course_number"], q_dict["question"])) as cur:
                    prop_row = await cur.fetchone()
                    if prop_row:
                        q_dict["proposed_by"] = {
                            "first_name": prop_row["first_name"],
                            "username": prop_row["username"],
                            "user_id": prop_row["user_id"]
                        }

        return web.json_response({"success": True, "question": q_dict})
    except Exception as e:
        logger.error(f"Error loading admin question: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def delete_admin_question(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        question_id = data.get('questionId')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
        if not question_id:
            return web.json_response({"success": False, "error": "Missing questionId"}, status=400)
            
        import database as db
        success = await db.delete_question_from_db(question_id)
        if success:
            return web.json_response({"success": True})
        else:
            return web.json_response({"success": False, "error": "Database deletion failed"}, status=500)
    except Exception as e:
        logger.error(f"Error deleting admin question: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def delete_bulk_admin_questions(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        question_ids = data.get('questionIds', [])
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
        if not question_ids or not isinstance(question_ids, list):
            return web.json_response({"success": False, "error": "Missing or invalid questionIds"}, status=400)
            
        import database as db
        deleted_count = 0
        for qid in question_ids:
            success = await db.delete_question_from_db(qid)
            if success:
                deleted_count += 1
                
        return web.json_response({"success": True, "deleted": deleted_count})
    except Exception as e:
        logger.error(f"Error deleting bulk questions: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def update_admin_question(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        question_id = data.get('questionId')
        question = (data.get('question') or '').strip()
        choice_a = (data.get('choiceA') or '').strip()
        choice_b = (data.get('choiceB') or '').strip()
        choice_c = (data.get('choiceC') or '').strip()
        choice_d = (data.get('choiceD') or '').strip()
        correct_answer = (data.get('correctAnswer') or '').strip().lower()
        explanation = (data.get('explanation') or '').strip()
        is_active = 1 if data.get('isActive', True) else 0
        theme = (data.get('theme') or '').strip()
        sub_theme = (data.get('subTheme') or '').strip()
        hijra_val = data.get('hijraYear')
        try:
            hijra_year = int(hijra_val) if hijra_val is not None and str(hijra_val).strip() != "" else None
        except (ValueError, TypeError):
            hijra_year = None

        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
        if not question_id:
            return web.json_response({"success": False, "error": "Missing questionId"}, status=400)
        if not question or not choice_a or not choice_b:
            return web.json_response({"success": False, "error": "Question and choices A/B are required"}, status=400)
        if correct_answer not in {"a", "b", "c", "d"}:
            return web.json_response({"success": False, "error": "correctAnswer must be a, b, c, or d"}, status=400)
        if correct_answer == "c" and not choice_c:
            return web.json_response({"success": False, "error": "Choice C is empty"}, status=400)
        if correct_answer == "d" and not choice_d:
            return web.json_response({"success": False, "error": "Choice D is empty"}, status=400)

        def clean_val(val, is_expl=False):
            if not val or not isinstance(val, str):
                return val
            if is_expl:
                import re
                val = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", val)
                return val.replace("**", "")
            return val.replace("**", "")

        question = clean_val(question)
        choice_a = clean_val(choice_a)
        choice_b = clean_val(choice_b)
        choice_c = clean_val(choice_c)
        choice_d = clean_val(choice_d)
        explanation = clean_val(explanation, is_expl=True)

        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute("UPDATE questions SET question = ?, choice_a = ?, choice_b = ?, choice_c = ?, choice_d = ?, correct_answer = ?, explanation = ?, is_active = ?, theme = ?, sub_theme = ?, hijra_year = ? WHERE id = ?", (question, choice_a, choice_b, choice_c, choice_d, correct_answer, explanation, is_active, theme, sub_theme, hijra_year, int(question_id)))
            await db_conn.commit()

        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error updating admin question: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def toggle_question_active_api(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        question_id = data.get('questionId')
        is_active = 1 if data.get('isActive') else 0

        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
        if not question_id:
            return web.json_response({"success": False, "error": "Missing questionId"}, status=400)

        from config import DATABASE_PATH
        import aiosqlite
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute("UPDATE questions SET is_active = ? WHERE id = ?", (is_active, int(question_id)))
            await db_conn.commit()

        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error toggling question active status: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def update_admin_proposal(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        proposal_id = data.get('proposalId')
        question = (data.get('question') or '').strip()
        choice_a = (data.get('choiceA') or '').strip()
        choice_b = (data.get('choiceB') or '').strip()
        choice_c = (data.get('choiceC') or '').strip()
        choice_d = (data.get('choiceD') or '').strip()
        correct_answer = (data.get('correctAnswer') or '').strip().lower()
        explanation = (data.get('explanation') or '').strip()

        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
        if not proposal_id:
            return web.json_response({"success": False, "error": "Missing proposalId"}, status=400)
        if not question or not choice_a or not choice_b:
            return web.json_response({"success": False, "error": "Question and choices A/B are required"}, status=400)
        if correct_answer not in {"a", "b", "c", "d"}:
            return web.json_response({"success": False, "error": "correctAnswer must be a, b, c, or d"}, status=400)
        if correct_answer == "c" and not choice_c:
            return web.json_response({"success": False, "error": "Choice C is empty"}, status=400)
        if correct_answer == "d" and not choice_d:
            return web.json_response({"success": False, "error": "Choice D is empty"}, status=400)

        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute("UPDATE questions_proposees SET question = ?, choice_a = ?, choice_b = ?, choice_c = ?, choice_d = ?, correct_answer = ?, explanation = ? WHERE id = ?", (question, choice_a, choice_b, choice_c, choice_d, correct_answer, explanation, int(proposal_id)))
            await db_conn.commit()

        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error updating admin proposal: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# Admin API: List student question proposals
async def get_admin_proposals(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        role = await get_admin_role(user_id)
        if role in ["support_admin", "tech_admin"]:
            return web.json_response({"success": True, "proposals": []})
            
        proposals = []
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute("SELECT qp.id, qp.user_id, qp.username, qp.first_name, qp.subject, qp.topic, qp.lesson, qp.question, qp.choice_a, qp.choice_b, qp.choice_c, qp.choice_d, qp.correct_answer, qp.explanation, qp.status, qp.admin_feedback, qp.created_at, u.academic_year, qp.source, qp.contact_info, qp.claimed_by, qp.tags, qp.media_file_id, qp.media_type FROM questions_proposees qp LEFT JOIN users u ON qp.user_id = u.telegram_id ORDER BY qp.created_at DESC") as cur:
                async for r in cur:
                    proposals.append({
                        "id": r["id"],
                        "userId": r["user_id"],
                        "username": r["username"],
                        "firstName": r["first_name"],
                        "subject": r["subject"],
                        "topic": r["topic"],
                        "lesson": r["lesson"],
                        "question": r["question"],
                        "choiceA": r["choice_a"],
                        "choiceB": r["choice_b"],
                        "choiceC": r["choice_c"],
                        "choiceD": r["choice_d"],
                        "correctAnswer": r["correct_answer"],
                        "explanation": r["explanation"],
                        "status": r["status"],
                        "adminReply": r["admin_feedback"] or "",
                        "createdAt": r["created_at"],
                        "academicYear": r["academic_year"],
                        "source": r["source"] or "telegram",
                        "contactInfo": r["contact_info"] or "",
                        "claimedBy": r["claimed_by"] or "",
                        "tags": json.loads(r["tags"] or "[]"),
                        "mediaFileId": r["media_file_id"] or "",
                        "mediaType": r["media_type"] or ""
                    })
        return web.json_response({"success": True, "proposals": proposals})
    except Exception as e:
        logger.error(f"Error loading proposals: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Resolve a proposal
async def resolve_admin_proposal(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        proposal_id = data.get('proposalId')
        action = data.get('action') # 'approved' or 'rejected'
        rejection_reason = data.get('rejectionReason', '')
        if not rejection_reason:
            rejection_reason = data.get('adminFeedback', '')
            
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            
            async with db_conn.execute("SELECT user_id, question FROM questions_proposees WHERE id = ?", (proposal_id,)) as cur:
                proposal = await cur.fetchone()
            
            if not proposal:
                return web.json_response({"success": False, "error": "Proposal not found"}, status=404)
                
            if action == 'approved':
                async with db_conn.execute("SELECT MAX(id) FROM questions") as cur:
                    row = await cur.fetchone()
                    next_id = (row[0] or 1000) + 1
                    
                async with db_conn.execute("SELECT * FROM questions_proposees WHERE id = ?", (proposal_id,)) as cur:
                    prop_details = await cur.fetchone()
                    
                await db_conn.execute("INSERT INTO questions (id, subject, course_number, course_name, question, choice_a, choice_b, choice_c, choice_d, correct_answer, explanation, source, theme, sub_theme, hijra_year) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'student_proposal', ?, ?, ?)", (next_id, prop_details["subject"], prop_details["course_number"], prop_details["lesson"], prop_details["question"], prop_details["choice_a"], prop_details["choice_b"], prop_details["choice_c"], prop_details["choice_d"], prop_details["correct_answer"], prop_details["explanation"], prop_details["topic"] or "", prop_details["tags"] or "", prop_details["hijra_year"]))
                
                await db_conn.execute("UPDATE questions_proposees SET status = 'approved', admin_feedback = ?, reviewed_at = CURRENT_TIMESTAMP WHERE id = ?", (rejection_reason, proposal_id))
            else:
                await db_conn.execute("UPDATE questions_proposees SET status = 'rejected', rejection_reason = ?, admin_feedback = ?, reviewed_at = CURRENT_TIMESTAMP WHERE id = ?", (rejection_reason, rejection_reason, proposal_id))
                
            await db_conn.commit()
            
            # Notify student on Telegram
            bot = request.app['bot']
            try:
                status_label = "✅ تم قبول سؤالك المقترح وإضافته للأسئلة الرسمية بالأكاديمية!"
                if rejection_reason and action == 'approved':
                    status_label += f"\n💬 تعليق الإدارة: {rejection_reason}"
                elif action != 'approved':
                    status_label = f"❌ عذراً، تم رفض سؤالك المقترح.\n💬 السبب: {rejection_reason}"
                    
                notif = (
                    f"📢 <b>تحديث بخصوص مقترحك لأسئلة المراجعة (البوت البديل)</b>\n"
                    f"—— —— —— —— —— —— —— —— —— —— \n"
                    f"السؤال: <i>\"{proposal['question']}\"</i>\n\n"
                    f"{status_label}\n"
                    f"—— —— —— —— —— —— —— —— —— —— \n"
                    f"شكراً لمساهمتك في بناء الأكاديمية!"
                )
                await bot.send_message(proposal['user_id'], notif, parse_mode="HTML")
            except Exception as notify_err:
                logger.error(f"Error notifying student for proposal resolution: {notify_err}")
                
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error resolving proposal: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: List tickets from question_reports (suggestions, tech, errors, etc.)
async def get_admin_tickets(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        role = await get_admin_role(user_id)

        tickets = []
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            
            query = "SELECT qr.id, qr.user_id, qr.username, qr.first_name, qr.report_type, qr.question_id, qr.target, qr.notes, qr.urgency, qr.status, qr.admin_reply, qr.reviewed_at, qr.created_at, qr.claimed_by, qr.student_read, qr.tags, qr.media_file_id, qr.media_type, q.subject AS question_subject, q.course_number AS question_course_number, u.academic_year, qr.source, qr.contact_info FROM question_reports qr LEFT JOIN questions q ON qr.question_id = q.id LEFT JOIN users u ON qr.user_id = u.telegram_id WHERE 1=1"
            
            if role in ["support_admin", "tech_admin"]:
                query += " AND qr.report_type = 'tech'"
            elif role in ["improvement_admin", "academie_admin"]:
                query += " AND qr.report_type = 'schooling'"
                
            query += " ORDER BY qr.created_at DESC"
            
            async with db_conn.execute(query) as cur:
                async for r in cur:
                    tickets.append({
                        "id": r["id"],
                        "userId": r["user_id"],
                        "username": r["username"],
                        "firstName": r["first_name"],
                        "reportType": r["report_type"],
                        "questionId": r["question_id"],
                        "target": r["target"],
                        "notes": r["notes"],
                        "urgency": r["urgency"],
                        "status": r["status"],
                        "adminReply": r["admin_reply"] or "",
                        "reviewedAt": r["reviewed_at"] or "",
                        "createdAt": r["created_at"],
                        "claimedBy": r["claimed_by"] or "",
                        "studentRead": r["student_read"],
                        "subject": r["question_subject"] or "",
                        "courseNumber": r["question_course_number"],
                        "academicYear": r["academic_year"],
                        "source": r["source"] or "telegram",
                        "contactInfo": r["contact_info"] or "",
                        "tags": json.loads(r["tags"] or "[]"),
                        "mediaFileId": r["media_file_id"] or "",
                        "mediaType": r["media_type"] or ""
                    })
        return web.json_response({"success": True, "tickets": tickets})
    except Exception as e:
        logger.error(f"Error loading tickets: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Omnichannel API: Receive tickets from external platforms (WhatsApp, Web, Gmail)
async def receive_external_ticket(request):
    try:
        data = await request.json()
        source = data.get('source') # 'whatsapp', 'gmail', 'platform'
        contact_info = data.get('contactInfo', '')
        notes = data.get('notes', '')
        report_type = data.get('reportType', 'other')
        first_name = data.get('firstName', 'Utilisateur Externe')
        telegram_id = data.get('telegramId', 0)
        username = data.get('username', f"ext_{source}")
        
        if not source or not notes:
            return web.json_response({"success": False, "error": "Missing source or notes"}, status=400)
            
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            cursor = await db_conn.execute("INSERT INTO question_reports (user_id, username, first_name, report_type, notes, urgency, source, contact_info) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (telegram_id, username, first_name, report_type, notes, "Moyen", source, contact_info))
            await db_conn.commit()
            ticket_id = cursor.lastrowid
            
        return web.json_response({"success": True, "ticketId": ticket_id})
    except Exception as e:
        logger.error(f"Error receiving external ticket: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# AI Triage & Similarity API: find matching resolved tickets
async def handle_triage_match(request):
    try:
        data = await request.json()
        query = data.get('query', '').strip()
        use_ai = data.get('use_ai', False)
        if not query:
            return web.json_response({"success": True, "matches": []})
            
        import database as db
        matches = await db.search_similar_triage(query, use_ai=use_ai)
        return web.json_response({"success": True, "matches": matches})
    except Exception as e:
        logger.error(f"Error in handle_triage_match: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# Student/Admin API: List student's own tickets (Mini App support)
async def get_student_tickets(request):
    try:
        telegram_id = request.query.get('telegram_id')
        if not telegram_id:
            try:
                data = await request.json()
                telegram_id = data.get('telegram_id')
            except Exception:
                pass
        if not telegram_id:
            return web.json_response({"success": False, "error": "Missing telegram_id"}, status=400)
            
        import database as db
        tickets = await db.get_student_tickets(int(telegram_id))
        return web.json_response({"success": True, "tickets": tickets})
    except Exception as e:
        logger.error(f"Error loading student tickets: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Student/Admin API: Get ticket chat messages history
async def get_ticket_messages_api(request):
    try:
        ticket_id = request.match_info.get('ticket_id')
        if not ticket_id:
            return web.json_response({"success": False, "error": "Missing ticket_id"}, status=400)
            
        import database as db
        messages = await db.get_ticket_chat_messages(int(ticket_id))
        return web.json_response({"success": True, "messages": messages})
    except Exception as e:
        logger.error(f"Error getting ticket messages: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Student/Admin API: Reply to a ticket (append to chat history)
async def reply_ticket_message_api(request):
    try:
        ticket_id = request.match_info.get('ticket_id')
        data = await request.json()
        sender = data.get('sender') # 'student' or 'admin'
        sender_name = data.get('sender_name')
        message = data.get('message', '').strip()
        media_file_id = data.get('mediaFileId')
        media_type = data.get('mediaType')
        
        if not ticket_id or not sender or not message:
            return web.json_response({"success": False, "error": "Missing parameters"}, status=400)
            
        import database as db
        
        # Insert message into chat history
        msg_id = await db.add_ticket_chat_message(
            ticket_id=int(ticket_id),
            sender=sender,
            sender_name=sender_name,
            message=message,
            media_file_id=media_file_id,
            media_type=media_type
        )
        
        # Also update the main ticket's admin_reply or status if needed
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            if sender == 'admin':
                await db_conn.execute(
                    "UPDATE question_reports SET admin_reply = ?, reviewed_at = COALESCE(NULLIF(?, ''), datetime('now')) WHERE id = ?",
                    (message, int(ticket_id))
                )
            else:
                # If student replies, set status back to pending/in_progress so admins see it
                async with db_conn.execute("SELECT status FROM question_reports WHERE id = ?", (int(ticket_id),)) as cur:
                    row = await cur.fetchone()
                    if row and row[0] in ['resolved', 'rejected']:
                        await db_conn.execute("UPDATE question_reports SET status = 'pending' WHERE id = ?", (int(ticket_id),))
            await db_conn.commit()
            
        # Send Telegram notification if admin is replying
        if sender == 'admin':
            bot = request.app.get('bot')
            if bot:
                async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                    db_conn.row_factory = aiosqlite.Row
                    async with db_conn.execute("SELECT user_id, report_type FROM question_reports WHERE id = ?", (int(ticket_id),)) as cur:
                        row = await cur.fetchone()
                if row:
                    try:
                        type_labels = {
                            'suggestion': '💡 اقتراحك',
                            'question_error': '🚩 بلاغ الخطأ',
                            'tech': '🔧 مشكلتك التقنية',
                            'other': '✉️ رسالتك'
                        }
                        label = type_labels.get(row["report_type"], "✉️ رسالتك")
                        
                        host = request.host
                        webapp_url = f"https://{host}/ask.html?view=chat&ticket_id={ticket_id}"
                        
                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
                        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💬 فتح المحادثة ", web_app=WebAppInfo(url=webapp_url))]
                        ])
                        
                        await bot.send_message(
                            chat_id=row["user_id"],
                            text=f"✉️ <b>رد جديد من الإدارة على {label} :</b>\n\n<i>\"{message}\"</i>",
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.warning(f"Could not notify student via Telegram: {e}")
                        
        else:
            # Notify admin group or the claimer
            from config import TELEGRAM_SUPPORT_GROUP_ID
            if TELEGRAM_SUPPORT_GROUP_ID:
                bot = request.app.get('bot')
                if bot:
                    try:
                        await bot.send_message(
                            chat_id=int(TELEGRAM_SUPPORT_GROUP_ID),
                            text=f"💬 <b>رد جديد من الطالب على التذكرة #{ticket_id} :</b>\n\n<i>\"{message}\"</i>",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.warning(f"Could not notify admin group: {e}")
                        
        return web.json_response({"success": True, "messageId": msg_id})
    except Exception as e:
        logger.error(f"Error replying to ticket: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Broadcast Message
async def admin_broadcast(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        message_text = data.get('message', '').strip()
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        role = await get_admin_role(user_id)
        if role != "super_admin":
            return web.json_response({"success": False, "error": "Require super_admin role"}, status=403)
            
        if not message_text:
            return web.json_response({"success": False, "error": "Message is empty"}, status=400)
            
        bot = request.app.get('bot')
        if not bot:
            return web.json_response({"success": False, "error": "Bot instance not found"}, status=500)
            
        academic_year = data.get('academicYear')
        if academic_year:
            try:
                academic_year = int(academic_year)
            except ValueError:
                academic_year = None
                
        from database import get_all_user_ids
        users = await get_all_user_ids(academic_year=academic_year)
        
        import asyncio
        async def send_to_all():
            success_count = 0
            for uid in users:
                try:
                    await bot.send_message(chat_id=uid, text=message_text, parse_mode="HTML")
                    success_count += 1
                except Exception as e:
                    logger.error(f"Broadcast failed for {uid}: {e}")
                await asyncio.sleep(0.05)
            logger.info(f"Broadcast finished. Sent to {success_count}/{len(users)} users.")
            
        asyncio.create_task(send_to_all())
            
        return web.json_response({"success": True, "total_users": len(users)})
        
    except Exception as e:
        logger.error(f"Error in broadcast: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: List Questions (Question Bank)
async def admin_questions_list(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        page = int(data.get('page', 1))
        per_page = int(data.get('per_page', 50))
        subject = data.get('subject', '')
        lesson_num = data.get('lessonNum', '')
        source = data.get('source', '')
        search = data.get('search', '')
        chapter_idx = data.get('chapterIdx', '')
        theme_filter = data.get('theme', '')
        subtheme_filter = data.get('sub_theme', '')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        from config import DATABASE_PATH
        import math
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            
            # If chapter_idx is selected, we filter by chapter index in memory using the same heuristic as stats
            if chapter_idx and subject and lesson_num:
                subj_clean = subject.lower().strip()
                if subj_clean == 'aqeeda':
                    subj_clean = 'aqida'
                
                async with db_conn.execute(
                    "SELECT id, subject, course_number, chapter_index, title, content FROM course_chapters WHERE LOWER(TRIM(subject)) IN (?, ?) AND course_number = ?", 
                    (subj_clean, 'aqeeda' if subj_clean == 'aqida' else subj_clean, int(lesson_num))
                ) as cur:
                    ch_rows = await cur.fetchall()
                c_chaps = [dict(ch) for ch in ch_rows]
                c_chaps.sort(key=lambda x: x["chapter_index"])
                
                # Fetch all questions matching subject, lesson, source, and search (without LIMIT/OFFSET)
                base_query = "SELECT * FROM questions WHERE 1=1"
                params = []
                
                base_query += " AND 1=1"
                # Normalize aqida/aqeeda — DB may use either spelling
                subj_variants = [subject]
                if subject.lower() in ('aqida', 'aqeeda'):
                    subj_variants = ['aqida', 'aqeeda']
                placeholders = ','.join('?' * len(subj_variants))
                base_query += f" AND LOWER(subject) IN ({placeholders})"
                params.extend([s.lower() for s in subj_variants])
                
                if lesson_num and str(lesson_num).lower() != 'all':
                    base_query += " AND course_number = ?"
                    params.append(int(lesson_num))
                if source:
                    if source == 'official':
                        base_query += " AND (source IS NULL OR source = '' OR source = 'official' OR source NOT IN ('student_proposal', 'ai_generated', 'generated_by_gemini'))"
                    elif source == 'student_proposal':
                        base_query += " AND source = 'student_proposal'"
                    elif source == 'ai_generated':
                        base_query += " AND source IN ('ai_generated', 'generated_by_gemini')"
                    else:
                        base_query += " AND source = ?"
                        params.append(source)
                        
                if search:
                    base_query += " AND question LIKE ?"
                    params.append(f"%{search}%")
                    
                if theme_filter:
                    base_query += " AND theme = ?"
                    params.append(theme_filter)
                    
                if subtheme_filter:
                    base_query += " AND sub_theme = ?"
                    params.append(subtheme_filter)
                    
                base_query += " ORDER BY id"
                
                async with db_conn.execute(base_query, params) as cur:
                    q_rows = await cur.fetchall()
                all_matching_questions = [dict(r) for r in q_rows]
                
                # Heuristic cleaner
                def clean_words(text):
                    if not text:
                        return set()
                    stop_words = {'le', 'la', 'de', 'en', 'et', 'في', 'من', 'على', 'ان', 'أن', 'هو', 'هي', 'هل'}
                    words = "".join(c if c.isalnum() or c.isspace() else " " for c in text.lower()).split()
                    return {w for w in words if w not in stop_words and len(w) > 2}
                
                if c_chaps:
                    for ch in c_chaps:
                        ch["clean_words"] = clean_words((ch["title"] or "") + " " + (ch.get("content") or ""))

                filtered_questions = []
                target_idx = int(chapter_idx)
                for q in all_matching_questions:
                    matched_idx = None
                    if c_chaps:
                        q_words = clean_words((q["question"] or "") + " " + (q["theme"] or ""))
                        best_ch_idx = None
                        best_score = -1
                        for ch in c_chaps:
                            score = len(q_words.intersection(ch["clean_words"]))
                            if score > best_score:
                                best_score = score
                                best_ch_idx = ch["chapter_index"]
                        
                        if best_ch_idx is not None and best_score > 0:
                            matched_idx = best_ch_idx
                        else:
                            matched_idx = c_chaps[0]["chapter_index"]
                            
                    if matched_idx == target_idx:
                        filtered_questions.append(q)
                
                # Fetch proposers for student proposals in this subset
                for q in filtered_questions:
                    if q.get("source") == "student_proposal":
                        async with db_conn.execute("""
                            SELECT first_name, username, user_id FROM questions_proposees 
                            WHERE question = ? OR (subject = ? AND course_number = ? AND question = ?)
                            LIMIT 1
                        """, (q["question"], q["subject"], q["course_number"], q["question"])) as cur:
                            prop_row = await cur.fetchone()
                            if prop_row:
                                q["proposed_by"] = {
                                    "first_name": prop_row["first_name"],
                                    "username": prop_row["username"],
                                    "user_id": prop_row["user_id"]
                                }
                                
                total_count = len(filtered_questions)
                total_pages = math.ceil(total_count / per_page) if per_page else 1
                
                start_offset = (page - 1) * per_page
                paginated_questions = filtered_questions[start_offset:start_offset + per_page]
                
                return web.json_response({
                    "success": True, 
                    "questions": paginated_questions,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total_count": total_count,
                        "total_pages": total_pages
                    }
                })
            
            # Default behavior (no chapter filter)
            query = "SELECT * FROM questions WHERE 1=1"
            count_query = "SELECT COUNT(*) FROM questions WHERE 1=1"
            params = []
            
            if subject:
                # Normalize aqida/aqeeda — DB may use either spelling
                subj_variants = [subject]
                if subject.lower() in ('aqida', 'aqeeda'):
                    subj_variants = ['aqida', 'aqeeda']
                placeholders = ','.join('?' * len(subj_variants))
                subj_clause = f" AND LOWER(subject) IN ({placeholders})"
                query += subj_clause
                count_query += subj_clause
                params.extend([s.lower() for s in subj_variants])
                
            if lesson_num:
                try:
                    query += " AND course_number = ?"
                    count_query += " AND course_number = ?"
                    params.append(int(lesson_num))
                except ValueError:
                    pass

            if source:
                if source == 'official':
                    src_clause = " AND (source IS NULL OR source = '' OR source = 'official' OR source NOT IN ('student_proposal', 'ai_generated', 'generated_by_gemini'))"
                    query += src_clause
                    count_query += src_clause
                elif source == 'student_proposal':
                    query += " AND source = 'student_proposal'"
                    count_query += " AND source = 'student_proposal'"
                elif source == 'ai_generated':
                    query += " AND source IN ('ai_generated', 'generated_by_gemini')"
                    count_query += " AND source IN ('ai_generated', 'generated_by_gemini')"
                else:
                    query += " AND source = ?"
                    count_query += " AND source = ?"
                    params.append(source)
                
            if search:
                query += " AND question LIKE ?"
                count_query += " AND question LIKE ?"
                params.append(f"%{search}%")
                
            if theme_filter:
                query += " AND theme = ?"
                count_query += " AND theme = ?"
                params.append(theme_filter)
                
            if subtheme_filter:
                query += " AND sub_theme = ?"
                count_query += " AND sub_theme = ?"
                params.append(subtheme_filter)
                
            query += " ORDER BY subject, course_number, id LIMIT ? OFFSET ?"
            
            async with db_conn.execute(count_query, params) as cur:
                total_count = (await cur.fetchone())[0]
                
            params.extend([per_page, (page - 1) * per_page])
            
            async with db_conn.execute(query, params) as cur:
                rows = await cur.fetchall()
                
            questions = [dict(r) for r in rows]
            
            # Fetch proposers for student proposals in this page
            for q in questions:
                if q.get("source") == "student_proposal":
                    async with db_conn.execute("""
                        SELECT first_name, username, user_id FROM questions_proposees 
                        WHERE question = ? OR (subject = ? AND course_number = ? AND question = ?)
                        LIMIT 1
                    """, (q["question"], q["subject"], q["course_number"], q["question"])) as cur:
                        prop_row = await cur.fetchone()
                        if prop_row:
                            q["proposed_by"] = {
                                "first_name": prop_row["first_name"],
                                "username": prop_row["username"],
                                "user_id": prop_row["user_id"]
                            }
                            
            total_pages = math.ceil(total_count / per_page) if per_page else 1
            
        return web.json_response({
            "success": True, 
            "questions": questions,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages
            }
        })
    except Exception as e:
        logger.error(f"Error in admin_questions_list: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def admin_get_themes(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        subject = data.get('subject', '')
        theme = data.get('theme', '')
        
        if not subject:
            return web.json_response({"success": False, "error": "Missing subject"}, status=400)
            
        from config import DATABASE_PATH
        import aiosqlite
        
        subj_variants = [subject]
        if subject.lower() in ('aqida', 'aqeeda'):
            subj_variants = ['aqida', 'aqeeda']
        placeholders = ','.join('?' * len(subj_variants))
            
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            if not theme:
                # Get all unique themes for subject
                query = f"SELECT DISTINCT theme FROM questions WHERE LOWER(subject) IN ({placeholders}) AND theme IS NOT NULL AND theme != '' ORDER BY theme"
                async with db_conn.execute(query, [s.lower() for s in subj_variants]) as cur:
                    rows = await cur.fetchall()
                results = [r['theme'] for r in rows]
                return web.json_response({"success": True, "themes": results})
            else:
                # Get all unique sub_themes for subject and theme
                query = f"SELECT DISTINCT sub_theme FROM questions WHERE LOWER(subject) IN ({placeholders}) AND theme = ? AND sub_theme IS NOT NULL AND sub_theme != '' ORDER BY sub_theme"
                params = [s.lower() for s in subj_variants] + [theme]
                async with db_conn.execute(query, params) as cur:
                    rows = await cur.fetchall()
                results = [r['sub_theme'] for r in rows]
                return web.json_response({"success": True, "sub_themes": results})
    except Exception as e:
        logger.error(f"Error in admin_get_themes: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# --- Curriculum Mapping Endpoints ---

async def get_admin_thematics(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        subject_filter = data.get('subject', None)
        academic_year = data.get('academic_year', None)
        
        from config import DATABASE_PATH
        import aiosqlite
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # Fetch programs
            query_prog = "SELECT * FROM programs"
            params_prog = []
            if subject_filter:
                query_prog += " WHERE subject = ?"
                params_prog.append(subject_filter)
            async with db.execute(query_prog, params_prog) as cursor:
                programs = [dict(r) for r in await cursor.fetchall()]
                
            # Fetch nodes
            if subject_filter and programs:
                prog_ids = [p['id'] for p in programs]
                placeholders = ','.join('?' for _ in prog_ids)
                query_nodes = f"SELECT * FROM thematic_nodes WHERE program_id IN ({placeholders}) ORDER BY level, order_index"
                async with db.execute(query_nodes, prog_ids) as cursor:
                    nodes = [dict(r) for r in await cursor.fetchall()]
            else:
                query_nodes = "SELECT * FROM thematic_nodes ORDER BY level, order_index"
                async with db.execute(query_nodes) as cursor:
                    nodes = [dict(r) for r in await cursor.fetchall()]
                
            # Fetch unassigned_questions
            query_unassigned = "SELECT id, question, subject, course_number, source FROM questions WHERE thematic_node_id IS NULL AND source = 'official'"
            params_unassigned = []
            if subject_filter:
                query_unassigned += " AND subject = ?"
                params_unassigned.append(subject_filter)
            if academic_year:
                query_unassigned += " AND hijra_year = ?"
                params_unassigned.append(int(academic_year))
                
            async with db.execute(query_unassigned, params_unassigned) as cursor:
                unassigned_questions = [dict(r) for r in await cursor.fetchall()]

        return web.json_response({
            "success": True,
            "programs": programs,
            "nodes": nodes,
            "unassigned_questions": unassigned_questions
        })
    except Exception as e:
        logger.error(f"Error in get_admin_thematics: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def get_node_questions(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        node_id = data.get('node_id')
        if not node_id:
            return web.json_response({"success": False, "error": "Missing node_id"}, status=400)
        
        from config import DATABASE_PATH
        import aiosqlite
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            query = """
                WITH RECURSIVE node_tree(id) AS (
                    SELECT id FROM thematic_nodes WHERE id = ?
                    UNION ALL
                    SELECT t.id FROM thematic_nodes t
                    INNER JOIN node_tree nt ON t.parent_id = nt.id
                )
                SELECT id, question, subject, course_number, source 
                FROM questions 
                WHERE thematic_node_id IN node_tree
            """
            async with db.execute(query, (node_id,)) as cursor:
                questions = [dict(r) for r in await cursor.fetchall()]
                
        import json
        return web.json_response({"success": True, "questions": questions}, dumps=lambda obj: json.dumps(obj, ensure_ascii=False))
    except Exception as e:
        import logging
        logging.getLogger('bot').error(f"Error in get_node_questions: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def reorder_admin_thematics(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        source_node_id = data.get("source_node_id")
        target_node_id = data.get("target_node_id")
        level = data.get("level")
        
        from config import DATABASE_PATH
        import aiosqlite
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # 1. Obtenir les infos du target node pour connaitre le contexte (parent_id, program_id)
            async with db.execute("SELECT parent_id, program_id FROM thematic_nodes WHERE id = ?", (target_node_id,)) as cursor:
                target_row = await cursor.fetchone()
            if not target_row:
                return web.json_response({"success": False, "error": "Target node not found"})
                
            parent_id, program_id = target_row
            
            # 2. Obtenir tous les noeuds frères (siblings) ordonnés
            if parent_id is None:
                query = "SELECT id FROM thematic_nodes WHERE program_id = ? AND level = ? AND parent_id IS NULL ORDER BY order_index, title"
                params = (program_id, level)
            else:
                query = "SELECT id FROM thematic_nodes WHERE program_id = ? AND level = ? AND parent_id = ? ORDER BY order_index, title"
                params = (program_id, level, parent_id)
                
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
            sibling_ids = [row[0] for row in rows]
            
            # 3. Réorganiser la liste
            if source_node_id in sibling_ids and target_node_id in sibling_ids:
                sibling_ids.remove(source_node_id)
                target_index = sibling_ids.index(target_node_id)
                # Inserer le source juste avant le target
                sibling_ids.insert(target_index, source_node_id)
                
                # 4. Mettre à jour la base de données
                for idx, node_id in enumerate(sibling_ids):
                    await db.execute("UPDATE thematic_nodes SET order_index = ? WHERE id = ?", (idx, node_id))
                await db.commit()
                return web.json_response({"success": True})
            else:
                return web.json_response({"success": False, "error": "Nodes are not siblings"})
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def toggle_node_visibility(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        node_id = data.get('node_id')
        if not node_id:
            return web.json_response({"success": False, "error": "Missing node_id"}, status=400)
            
        from config import DATABASE_PATH
        import aiosqlite
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT is_active FROM thematic_nodes WHERE id = ?", (node_id,)) as cur:
                row = await cur.fetchone()
                if not row:
                    return web.json_response({"success": False, "error": "Node not found"})
                new_status = 0 if row[0] == 1 else 1
            await db.execute("UPDATE thematic_nodes SET is_active = ? WHERE id = ?", (new_status, node_id))
            await db.commit()
            
        return web.json_response({"success": True, "is_active": new_status})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def save_admin_thematics(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        action = data.get("action")
        
        from config import DATABASE_PATH
        import aiosqlite
        async with aiosqlite.connect(DATABASE_PATH) as db:
            if action == "assign_question":
                question_id = data.get("question_id")
                node_id = data.get("node_id") # Can be None if moving back to Inbox
                await db.execute("UPDATE questions SET thematic_node_id = ? WHERE id = ?", (node_id, question_id))
                await db.commit()
                return web.json_response({"success": True})
                
            elif action == "add_program":
                subject = data.get("subject")
                name = data.get("name")
                async with db.execute("INSERT INTO programs (subject, name) VALUES (?, ?)", (subject, name)) as cursor:
                    await db.commit()
                    return web.json_response({"success": True, "id": cursor.lastrowid})
                    
            elif action == "add_node":
                program_id = data.get("program_id")
                parent_id = data.get("parent_id")
                level = data.get("level")
                title = data.get("title")
                order_index = data.get("order_index", 0)
                
                async with db.execute(
                    "INSERT INTO thematic_nodes (program_id, parent_id, level, title, order_index) VALUES (?, ?, ?, ?, ?)",
                    (program_id, parent_id, level, title, order_index)
                ) as cursor:
                    await db.commit()
                    return web.json_response({"success": True, "id": cursor.lastrowid})
                    
            elif action == "update_node":
                node_id = data.get("node_id")
                title = data.get("title")
                await db.execute("UPDATE thematic_nodes SET title = ? WHERE id = ?", (title, node_id))
                await db.commit()
                return web.json_response({"success": True})
                
            elif action == "delete_node":
                node_id = data.get("node_id")
                # Because of ON DELETE CASCADE, child nodes will also be deleted
                await db.execute("DELETE FROM thematic_nodes WHERE id = ?", (node_id,))
                await db.execute("UPDATE questions SET thematic_node_id = NULL WHERE thematic_node_id = ?", (node_id,))
                await db.commit()
                return web.json_response({"success": True})
                
            else:
                return web.json_response({"success": False, "error": "Invalid action"}, status=400)
                
    except Exception as e:
        logger.error(f"Error in save_admin_thematics: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def get_questions_stats_api(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        from config import DATABASE_PATH
        import aiosqlite
        
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute("SELECT id, subject, course_number, source, question, theme FROM questions") as cur:
                questions_rows = await cur.fetchall()
            
            async with db_conn.execute("SELECT id, subject, course_number, chapter_index, title, content FROM course_chapters") as cur:
                chapters_rows = await cur.fetchall()
                
        questions = [dict(r) for r in questions_rows]
        chapters = [dict(r) for r in chapters_rows]
        
        stats = {}
        for s in ['aqida', 'fiqh', 'sira', 'nahw', 'tajweed']:
            stats[s] = {}
            
        chapters_by_course = {}
        for ch in chapters:
            subj = ch["subject"].lower().strip()
            if subj == 'aqeeda':
                subj = 'aqida'
            if subj not in stats:
                continue
            c_num = ch["course_number"]
            key = (subj, c_num)
            if key not in chapters_by_course:
                chapters_by_course[key] = []
            chapters_by_course[key].append(ch)
            
        def clean_words(text):
            if not text:
                return set()
            stop_words = {'le', 'la', 'de', 'en', 'et', 'في', 'من', 'على', 'ان', 'أن', 'هو', 'هي', 'هل'}
            words = "".join(c if c.isalnum() or c.isspace() else " " for c in text.lower()).split()
            return {w for w in words if w not in stop_words and len(w) > 2}

        # Pre-compute chapter words to speed up heuristic
        for ch in chapters:
            ch["clean_words"] = clean_words((ch["title"] or "") + " " + (ch.get("content") or ""))

        all_courses = set()
        for q in questions:
            subj = q["subject"].lower().strip()
            if subj == 'aqeeda':
                subj = 'aqida'
            if subj not in stats:
                continue
            all_courses.add((subj, q["course_number"]))
            
        for ch in chapters:
            subj = ch["subject"].lower().strip()
            if subj == 'aqeeda':
                subj = 'aqida'
            if subj not in stats:
                continue
            all_courses.add((subj, ch["course_number"]))
            
        for subj, c_num in all_courses:
            c_chaps = chapters_by_course.get((subj, c_num), [])
            c_chaps.sort(key=lambda x: x["chapter_index"])
            
            stats[subj][c_num] = {
                "course_number": c_num,
                "total": 0,
                "official": 0,
                "student_proposal": 0,
                "ai_generated": 0,
                "chapters": [
                    {
                        "chapter_index": ch["chapter_index"],
                        "title": ch["title"],
                        "count": 0,
                        "official": 0,
                        "student_proposal": 0,
                        "ai_generated": 0
                    } for ch in c_chaps
                ]
            }

        for q in questions:
            subj = q["subject"].lower().strip()
            if subj == 'aqeeda':
                subj = 'aqida'
            if subj not in stats:
                continue
            c_num = q["course_number"]
            
            course_data = stats[subj][c_num]
            course_data["total"] += 1
            
            src = q["source"] or ""
            if src == "student_proposal":
                course_data["student_proposal"] += 1
            elif src in ["ai_generated", "generated_by_gemini"]:
                course_data["ai_generated"] += 1
            else:
                course_data["official"] += 1
                
            c_chaps = chapters_by_course.get((subj, c_num), [])
            if c_chaps:
                q_words = clean_words((q["question"] or "") + " " + (q["theme"] or ""))
                best_ch_idx = None
                best_score = -1
                for ch in c_chaps:
                    score = len(q_words.intersection(ch["clean_words"]))
                    if score > best_score:
                        best_score = score
                        best_ch_idx = ch["chapter_index"]
                
                if best_ch_idx is not None and best_score > 0:
                    for ch_stat in course_data["chapters"]:
                        if ch_stat["chapter_index"] == best_ch_idx:
                            ch_stat["count"] += 1
                            if src == "student_proposal":
                                ch_stat["student_proposal"] += 1
                            elif src in ["ai_generated", "generated_by_gemini"]:
                                ch_stat["ai_generated"] += 1
                            else:
                                ch_stat["official"] += 1
                            break
                else:
                    if course_data["chapters"]:
                        course_data["chapters"][0]["count"] += 1
                        if src == "student_proposal":
                            course_data["chapters"][0]["student_proposal"] += 1
                        elif src in ["ai_generated", "generated_by_gemini"]:
                            course_data["chapters"][0]["ai_generated"] += 1
                        else:
                            course_data["chapters"][0]["official"] += 1

        return web.json_response({"success": True, "stats": stats})
    except Exception as e:
        logger.error(f"Error in get_questions_stats_api: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Test Telegram Group ID
async def test_telegram_group(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        group_id_str = data.get('groupId')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        bot = request.app.get('bot')
        if not bot:
            return web.json_response({"success": False, "error": "Bot instance not found"}, status=500)
            
        try:
            group_id = int(group_id_str)
            chat = await bot.get_chat(chat_id=group_id)
            return web.json_response({"success": True, "chat_title": chat.title, "chat_type": chat.type})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)})
            
    except Exception as e:
        logger.error(f"Error testing group: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Resolve a ticket from question_reports
async def resolve_admin_ticket(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        ticket_id = data.get('ticketId')
        admin_reply = data.get('adminReply', '')
        new_status = data.get('status', 'resolved')

        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        from config import DATABASE_PATH
        import database as db
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            # Get student user_id to notify them
            async with db_conn.execute(
                "SELECT user_id, first_name, report_type FROM question_reports WHERE id = ?", (ticket_id,)
            ) as cur:
                row = await cur.fetchone()

            await db_conn.execute(
                "UPDATE question_reports SET status = ?, admin_reply = ?, reviewed_at = COALESCE(NULLIF(?, ''), datetime('now')) WHERE id = ?",
                (new_status, admin_reply, ticket_id)
            )
            await db_conn.commit()

            # Insert message into ticket_chat_messages
            if admin_reply:
                admin_name = "المشرف"
                async with db_conn.execute("SELECT first_name, username FROM admins WHERE telegram_id = ?", (int(user_id),)) as cur:
                    r = await cur.fetchone()
                    if r:
                        admin_name = r["first_name"] or r["username"] or admin_name
                await db.add_ticket_chat_message(
                    ticket_id=int(ticket_id),
                    sender='admin',
                    sender_name=admin_name,
                    message=admin_reply
                )

            # Notify the student via Telegram if reply provided
            if row and admin_reply:
                bot = request.app.get('bot')
                if bot:
                    try:
                        type_labels = {
                            'suggestion': '💡 اقتراحك',
                            'question_error': '🚩 بلاغ الخطأ',
                            'tech': '🔧 مشكلتك التقنية',
                            'other': '✉️ رسالتك'
                        }
                        label = type_labels.get(row["report_type"] or "other", "✉️ رسالتك")
                        
                        # Force https for WebApp compatibility on Telegram
                        host = request.host
                        webapp_url = f"https://{host}/ask.html?view=chat&ticket_id={ticket_id}"
                        
                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
                        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💬 فتح المحادثة ", web_app=WebAppInfo(url=webapp_url))]
                        ])
                        
                        await bot.send_message(
                            chat_id=row["user_id"],
                            text=f"✉️ رد الإدارة على {label}:\n\n<i>\"{admin_reply}\"</i>",
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.warning(f"Could not notify student: {e}")

        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error resolving ticket: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Update ticket report type (Triage)
async def update_ticket_type(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        ticket_id = data.get('ticketId')
        new_type = data.get('reportType')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        if not ticket_id or not new_type:
            return web.json_response({"success": False, "error": "Missing parameters"}, status=400)
            
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute(
                "UPDATE question_reports SET report_type = ? WHERE id = ?",
                (new_type, int(ticket_id))
            )
            await db_conn.commit()
            
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error updating ticket type: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Update ticket tags
async def update_ticket_tags(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        item_id = data.get('itemId')
        item_type = data.get('itemType')
        tags = data.get('tags', [])
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        if not item_id or not item_type:
            return web.json_response({"success": False, "error": "Missing parameters"}, status=400)
            
        table_map = {
            'report': 'chapter_reports',
            'proposal': 'questions_proposees',
            'ticket': 'question_reports'
        }
        
        table_name = table_map.get(item_type)
        if not table_name:
            return web.json_response({"success": False, "error": "Invalid itemType"}, status=400)
            
        from config import DATABASE_PATH
        import json
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute(
                f"UPDATE {table_name} SET tags = ? WHERE id = ?",
                (json.dumps(tags), item_id)
            )
            await db_conn.commit()
            
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error updating ticket tags: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Get all canned responses (templates)
async def get_canned_responses(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        templates = []
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute("SELECT id, title, category, content FROM canned_responses ORDER BY title ASC") as cur:
                async for r in cur:
                    templates.append({
                        "id": r["id"],
                        "title": r["title"],
                        "category": r["category"],
                        "content": r["content"]
                    })
        return web.json_response({"success": True, "templates": templates})
    except Exception as e:
        logger.error(f"Error loading templates: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Save (Create/Update) canned response
async def save_canned_response(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        template_id = data.get('id')
        title = (data.get('title') or '').strip()
        category = data.get('category', 'other')
        content = (data.get('content') or '').strip()
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        if not title or not content:
            return web.json_response({"success": False, "error": "Missing title or content"}, status=400)
            
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            if template_id:
                await db_conn.execute("""
                    UPDATE canned_responses SET title = ?, category = ?, content = ? WHERE id = ?
                """, (title, category, content, int(template_id)))
            else:
                await db_conn.execute("""
                    INSERT INTO canned_responses (title, category, content) VALUES (?, ?, ?)
                """, (title, category, content))
            await db_conn.commit()
            
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error saving template: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Delete canned response
async def delete_canned_response(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        template_id = data.get('id')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        if not template_id:
            return web.json_response({"success": False, "error": "Missing template id"}, status=400)
            
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute("DELETE FROM canned_responses WHERE id = ?", (int(template_id),))
            await db_conn.commit()
            
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Claim a ticket/report/proposal
async def claim_admin_ticket(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        ticket_id = data.get('ticketId')
        item_type = data.get('itemType', 'ticket')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        if not ticket_id:
            return web.json_response({"success": False, "error": "Missing ticketId"}, status=400)
            
        table_map = {
            'ticket': 'question_reports',
            'report': 'chapter_reports',
            'proposal': 'questions_proposees'
        }
        table_name = table_map.get(item_type, 'question_reports')
        
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            admin_name = "مشرف"
            db_conn.row_factory = aiosqlite.Row
            # 1. Try checking admins table first
            async with db_conn.execute("SELECT first_name, username FROM admins WHERE telegram_id = ?", (int(user_id),)) as cur:
                r = await cur.fetchone()
                if r and (r["first_name"] or r["username"]):
                    admin_name = r["first_name"] or r["username"]
            
            # 2. Try checking users table if still generic
            if admin_name == "مشرف" or not admin_name:
                async with db_conn.execute("SELECT first_name, username FROM users WHERE telegram_id = ?", (int(user_id),)) as cur:
                    r = await cur.fetchone()
                    if r and (r["first_name"] or r["username"]):
                        admin_name = r["first_name"] or r["username"]
                        await db_conn.execute(
                            "UPDATE admins SET first_name = ?, username = ? WHERE telegram_id = ?",
                            (r["first_name"] or "", r["username"] or "", int(user_id))
                        )
            
            # 3. Try checking Telegram Bot API if still generic
            if admin_name == "مشرف" or not admin_name:
                bot = request.app.get('bot')
                if bot:
                    try:
                        chat = await bot.get_chat(chat_id=int(user_id))
                        if chat:
                            admin_name = chat.first_name or chat.username or admin_name
                            await db_conn.execute(
                                "UPDATE admins SET first_name = ?, username = ? WHERE telegram_id = ?",
                                (chat.first_name or "", chat.username or "", int(user_id))
                            )
                    except Exception as tg_err:
                        logger.warning(f"Could not retrieve admin chat info from Telegram in claim_admin_ticket: {tg_err}")
            
            from config import TELEGRAM_ADMIN_IDS
            if admin_name == "مشرف" and (int(user_id) in TELEGRAM_ADMIN_IDS or int(user_id) in [2045194295]):
                admin_name = "Super Admin"
                
            db_id = int(ticket_id) if item_type != 'report' else ticket_id
            if table_name == 'question_reports':
                await db_conn.execute(f"""
                    UPDATE {table_name} SET claimed_by = ?, status = 'in_progress', assigned_admin_id = ? WHERE id = ?
                """, (admin_name, int(user_id), db_id))
            else:
                await db_conn.execute(f"""
                    UPDATE {table_name} SET claimed_by = ?, status = 'in_progress' WHERE id = ?
                """, (admin_name, db_id))
            await db_conn.commit()
            
        return web.json_response({"success": True, "claimedBy": admin_name})
    except Exception as e:
        logger.error(f"Error claiming ticket: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: List all admins
async def get_admins_list(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        role = await get_admin_role(user_id)
        if role != "super_admin":
            return web.json_response({"success": False, "error": "Require super_admin role"}, status=403)
            
        admins = []
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute("SELECT telegram_id AS user_id, role, username, first_name, added_by, added_at, allowed_subjects, visible_sections FROM admins ORDER BY added_at DESC") as cur:
                async for r in cur:
                    admins.append(dict(r))

                    
        return web.json_response({"success": True, "admins": admins})
    except Exception as e:
        logger.error(f"Error listing admins: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Add or Update Admin
async def add_admin_user(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        target_id = data.get('targetId')
        target_role = data.get('role', 'moderator')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        role = await get_admin_role(user_id)
        if role != "super_admin":
            return web.json_response({"success": False, "error": "Require super_admin role"}, status=403)
            
        if not target_id:
            return web.json_response({"success": False, "error": "Missing targetId"}, status=400)
            
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute(
                "INSERT INTO admins (telegram_id, role, added_by) VALUES (?, ?, ?) ON CONFLICT(telegram_id) DO UPDATE SET role = excluded.role",
                (int(target_id), target_role, int(user_id))
            )
            await db_conn.commit()
            
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Remove Admin
async def remove_admin_user(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        target_id = data.get('targetId')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        role = await get_admin_role(user_id)
        if role != "super_admin":
            return web.json_response({"success": False, "error": "Require super_admin role"}, status=403)
            
        if not target_id or int(target_id) == int(user_id):
            return web.json_response({"success": False, "error": "Cannot remove yourself or missing targetId"}, status=400)
            
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute("DELETE FROM admins WHERE telegram_id = ?", (int(target_id),))
            await db_conn.commit()
            
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Update admin permissions (subjects + sections)
async def update_admin_permissions(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        target_id = data.get('targetId')
        allowed_subjects = data.get('allowedSubjects')  # None or list like ["aqeeda","fiqh"]
        visible_sections = data.get('visibleSections')  # None or list like ["inbox","questions"]

        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
        role = await get_admin_role(user_id)
        if role != "super_admin":
            return web.json_response({"success": False, "error": "Require super_admin role"}, status=403)
        if not target_id:
            return web.json_response({"success": False, "error": "Missing targetId"}, status=400)

        import json as _json
        subjects_json = _json.dumps(allowed_subjects) if allowed_subjects is not None else None
        sections_json = _json.dumps(visible_sections) if visible_sections is not None else None

        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute(
                "UPDATE admins SET allowed_subjects = ?, visible_sections = ? WHERE telegram_id = ?",
                (subjects_json, sections_json, int(target_id))
            )
            await db_conn.commit()
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error updating admin permissions: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# Admin API: Custom Views — List accessible views for this admin
async def list_custom_views(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        import json as _json
        uid = int(user_id)
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute(
                """SELECT * FROM admin_custom_views ORDER BY position ASC, created_at ASC"""
            ) as cur:
                rows = await cur.fetchall()

        views = []
        for r in rows:
            vis = r['visibility']
            targets = _json.loads(r['target_ids'] or '[]')
            # Include if: private (own), shared (all), targeted (uid in targets)
            if vis == 'private' and r['created_by'] != uid:
                continue
            if vis == 'targeted' and uid not in targets:
                # super_admin sees all targeted
                role = await get_admin_role(user_id)
                if role != 'super_admin':
                    continue
            views.append({
                'id': r['id'],
                'createdBy': r['created_by'],
                'name': r['name'],
                'icon': r['icon'],
                'filters': _json.loads(r['filters'] or '{}'),
                'visibility': vis,
                'targetIds': targets,
                'position': r['position'],
                'isLocked': bool(r['is_locked']),
                'createdAt': r['created_at'],
            })
        return web.json_response({"success": True, "views": views})
    except Exception as e:
        logger.error(f"Error listing custom views: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# Admin API: Custom Views — Save (create or update)
async def save_custom_view(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        role = await get_admin_role(user_id)
        view_id = data.get('id')  # None = create new
        name = data.get('name', 'Vue')
        icon = data.get('icon', '📌')
        filters_obj = data.get('filters', {})
        visibility = data.get('visibility', 'private')
        target_ids = data.get('targetIds', [])
        is_locked = int(data.get('isLocked', False))

        # Only super_admin can create shared/targeted views
        if visibility in ('shared', 'targeted') and role != 'super_admin':
            visibility = 'private'

        import json as _json, uuid as _uuid
        if not view_id:
            view_id = str(_uuid.uuid4())

        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            await db_conn.execute("""
                INSERT INTO admin_custom_views (id, created_by, name, icon, filters, visibility, target_ids, is_locked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    icon = excluded.icon,
                    filters = excluded.filters,
                    visibility = excluded.visibility,
                    target_ids = excluded.target_ids,
                    is_locked = excluded.is_locked
            """, (
                view_id, int(user_id), name, icon,
                _json.dumps(filters_obj),
                visibility,
                _json.dumps(target_ids),
                is_locked
            ))
            await db_conn.commit()
        return web.json_response({"success": True, "id": view_id})
    except Exception as e:
        logger.error(f"Error saving custom view: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# Admin API: Custom Views — Delete
async def delete_custom_view(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        view_id = data.get('id')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        role = await get_admin_role(user_id)
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute("SELECT * FROM admin_custom_views WHERE id = ?", (view_id,)) as cur:
                view = await cur.fetchone()
            if not view:
                return web.json_response({"success": False, "error": "View not found"}, status=404)
            # Only owner or super_admin can delete; locked views need super_admin
            if view['is_locked'] and role != 'super_admin':
                return web.json_response({"success": False, "error": "Vue verrouillée"}, status=403)
            if view['created_by'] != int(user_id) and role != 'super_admin':
                return web.json_response({"success": False, "error": "Non autorisé"}, status=403)
            await db_conn.execute("DELETE FROM admin_custom_views WHERE id = ?", (view_id,))
            await db_conn.commit()
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error deleting custom view: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# Admin API: Custom Views — Reorder
async def reorder_custom_views(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        ordered_ids = data.get('orderedIds', [])  # list of view IDs in desired order
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            for pos, vid in enumerate(ordered_ids):
                await db_conn.execute(
                    "UPDATE admin_custom_views SET position = ? WHERE id = ?", (pos, vid)
                )
            await db_conn.commit()
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error reordering custom views: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# Admin API: Get lesson resources (PDF/Mindmap)
async def get_lesson_resources_api(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        subject = data.get('subject')
        lesson_num = data.get('lessonNum')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        import database as db
        resources = await db.get_lesson_resources(subject, int(lesson_num))
        return web.json_response({
            "success": True, 
            "resources": resources or {"subject": subject, "course_number": int(lesson_num), "mind_map_file_id": None, "summary_file_id": None}
        })
    except Exception as e:
        logger.error(f"Error fetching lesson resources: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Save lesson resources
async def save_lesson_resources_api(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        subject = data.get('subject')
        lesson_num = data.get('lessonNum')
        resource_type = data.get('resourceType') # 'mind_map' or 'summary'
        file_id = data.get('fileId')
        
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)
            
        import database as db
        await db.save_lesson_resources(subject, int(lesson_num), resource_type, file_id)
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error saving lesson resources: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

# Admin API: Get media stats for all subjects/lessons
async def get_media_stats_api(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        subject = data.get('subject', 'aqeeda')

        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        import database as db
        import json as _json
        import os

        # Normalize subject key for transcripts.json
        subject_normalized = subject.lower().strip()

        # Load transcripts.json to get lesson titles
        transcripts_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'transcripts.json')
        lessons_by_num = {}
        if os.path.exists(transcripts_path):
            try:
                with open(transcripts_path, 'r', encoding='utf-8') as f:
                    transcripts = _json.load(f)
                for item in transcripts:
                    item_subject = (item.get('subject') or '').lower().strip()
                    # Normalize: aqeeda = aqeeda, aqida = aqeeda
                    if item_subject in (subject_normalized, subject_normalized.replace('aqida', 'aqeeda')):
                        ln = item.get('lessonNum') or item.get('lesson_num')
                        if ln is not None:
                            lessons_by_num[int(ln)] = item.get('title') or item.get('lesson') or f"درس {ln}"
            except Exception as e:
                logger.warning(f"Could not read transcripts.json: {e}")

        # Get all lessons that have resources in DB for this subject
        resources = await db.get_all_lessons_with_resources(subject_normalized)

        # Merge with transcripts lesson list
        all_lesson_nums = set(lessons_by_num.keys())
        for r in resources:
            all_lesson_nums.add(r['course_number'])

        # Build full detail (include file_ids for display)
        from config import DATABASE_PATH
        import aiosqlite
        lesson_resources_map = {}
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute(
                "SELECT course_number, mind_map_file_id, summary_file_id FROM lesson_resources WHERE subject = ?",
                (subject_normalized,)
            ) as cur:
                rows = await cur.fetchall()
                for row in rows:
                    lesson_resources_map[row['course_number']] = {
                        'mind_map_file_id': row['mind_map_file_id'],
                        'summary_file_id': row['summary_file_id']
                    }

        # Build final sorted list
        lessons_list = []
        for ln in sorted(all_lesson_nums):
            res = lesson_resources_map.get(ln, {})
            lessons_list.append({
                'course_number': ln,
                'title': lessons_by_num.get(ln, f"درس {ln}"),
                'mind_map_file_id': res.get('mind_map_file_id') or '',
                'summary_file_id': res.get('summary_file_id') or '',
                'has_mind_map': bool(res.get('mind_map_file_id')),
                'has_summary': bool(res.get('summary_file_id')),
            })

        # Stats
        mindmaps_ok = sum(1 for l in lessons_list if l['has_mind_map'])
        summaries_ok = sum(1 for l in lessons_list if l['has_summary'])
        mindmaps_missing = len(lessons_list) - mindmaps_ok
        summaries_missing = len(lessons_list) - summaries_ok

        return web.json_response({
            "success": True,
            "lessons": lessons_list,
            "stats": {
                "mindmaps_ok": mindmaps_ok,
                "mindmaps_missing": mindmaps_missing,
                "summaries_ok": summaries_ok,
                "summaries_missing": summaries_missing,
                "total": len(lessons_list)
            }
        })
    except Exception as e:
        logger.error(f"Error in get_media_stats_api: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# ——— Student Practice & Quiz API Endpoints ———

async def api_validate_student(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        student_id = data.get('student_id', '').strip()
        email = data.get('email', '').strip().lower()
        
        if not student_id or len(student_id) not in (6, 7):
            return web.json_response({'valid': False, 'message': ''})
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            if email:
                async with db.execute("SELECT telegram_id, first_name FROM academy_students WHERE student_id = ? AND LOWER(email) = ?", (student_id, email)) as cur:
                    row = await cur.fetchone()
                    if row:
                        telegram_id, first_name = row
                        return web.json_response({'valid': True, 'message': f'أهلاً بك {first_name} ✅'})
                    else:
                        # New / Pending student
                        return web.json_response({'valid': True, 'message': 'سيتم مراجعة الطلب مع الإدارة ⏳'})
            else:
                async with db.execute("SELECT telegram_id, first_name FROM academy_students WHERE student_id = ?", (student_id,)) as cur:
                    row = await cur.fetchone()
                    if row:
                        return web.json_response({'valid': True, 'message': 'رقم مسجل ✅'})
                    else:
                        return web.json_response({'valid': True, 'message': 'رقم جديد (قيد المراجعة) ⏳'})
                
    except Exception as e:
        return web.json_response({'valid': True, 'message': ''})

async def api_link_account(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    import database as db
    from database import log_student_action
    import logging
    _log = logging.getLogger('bot')
    
    bot = request.app.get('bot')

    try:
        data = await request.json()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        student_id_input = data.get('student_id', '').strip()
        source = (data.get('source') or '').strip().upper()
        source_suffix = f" [رابط: {source}]" if source else ""
        
        telegram_id = data.get('telegram_id')
        telegram_first_name = data.get('telegram_first_name', '')
        telegram_last_name = data.get('telegram_last_name', '')
        telegram_username = data.get('telegram_username', '')
        
        init_data = data.get('initData')
        if init_data:
            import urllib.parse
            import json
            try:
                parsed = urllib.parse.parse_qs(init_data)
                user_data = json.loads(parsed['user'][0])
                telegram_id = user_data['id']
                telegram_first_name = user_data.get('first_name', '')
                telegram_last_name = user_data.get('last_name', '')
                telegram_username = user_data.get('username', '')
            except Exception:
                pass
                
        if not telegram_id:
            return web.json_response({'success': False, 'error': 'خطأ في المصادقة مع تيليجرام (Erreur Telegram)'})
            
        telegram_name = f"{telegram_first_name} {telegram_last_name}".strip()
        
        # 1. Upsert users table
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            await db_conn.execute("""
                INSERT INTO users (telegram_id, first_name, last_name, username) 
                VALUES (?, ?, ?, ?) 
                ON CONFLICT(telegram_id) DO UPDATE SET 
                first_name=excluded.first_name, last_name=excluded.last_name, username=excluded.username
            """, (telegram_id, telegram_first_name, telegram_last_name, telegram_username))
            
            # 2. Chercher dans academy_students par email
            student_row = None
            if email:
                async with db_conn.execute("SELECT * FROM academy_students WHERE LOWER(TRIM(email)) = LOWER(TRIM(?))", (email,)) as cur:
                    student_row = await cur.fetchone()
            elif phone:
                async with db_conn.execute("SELECT * FROM academy_students WHERE phone = ?", (phone,)) as cur:
                    student_row = await cur.fetchone()
                    
            if student_row:
                try:
                    student = dict(student_row)
                except Exception:
                    student = dict(zip([c[0] for c in cur.description], student_row))
                p_status = (student.get('payment_status') or 'PAID').upper()
                real_first_name = student.get('first_name') or telegram_first_name
                
                # Cas 1 : L'élève est trouvé et son paiement est validé (PAYÉ)
                if p_status in ['PAID', 'PAYE', 'YES', 'OUI', 'VALIDE', 'ACTIVE', 'COMPLETED']:
                    # Lier le telegram_id
                    await db_conn.execute("UPDATE academy_students SET telegram_id = ?, telegram_username = ? WHERE student_id = ?", (telegram_id, telegram_username, student['student_id']))
                    await db_conn.commit()
                    
                    await log_student_action(student['student_id'], 'LINK_SUCCESS_APPROVED', f"تم تفعيل الحساب وتأكيد الدفع ({student.get('gender')}){source_suffix}", telegram_id=telegram_id, telegram_name=telegram_name, telegram_username=telegram_username)
                    
                    bot = request.app.get('bot')
                    links = await generate_and_send_student_links(bot, telegram_id, student, request.app)
                    
                    folder_link = ""
                    group_desc = ""
                    try:
                        from handlers.auth import resolve_student_folder_link
                        folder_link, group_desc = await resolve_student_folder_link(db_conn, student)
                    except Exception as e_fl:
                        _log.warning(f"Error resolving student folder in api_link_account: {e_fl}")

                    return web.json_response({
                        'success': True,
                        'status': 'approved',
                        'student_id': student['student_id'],
                        'first_name': real_first_name,
                        'gender': student.get('gender') or 'HOMME',
                        'year': student.get('year') or 1,
                        'links': links,
                        'folder_link': folder_link,
                        'group_desc': group_desc,
                        'message': f"مرحباً بك يا {real_first_name}! تم تفعيل حسابك بنجاح ✅"
                    })
                else:
                    # Trouvé mais statut non payé -> En attente
                    await db.add_pending_verification(telegram_id, email, telegram_username, telegram_first_name, phone)
                    await log_student_action(student['student_id'], 'LINK_WAITING_PAYMENT', f"حساب مسجل لكن في صالة الانتظار لتأكيد التحويل - رقم الطالب: {student['student_id']} - البريد: {email}{source_suffix}", telegram_id=telegram_id, telegram_name=telegram_name, telegram_username=telegram_username)
                # 3. Webhook Admin Alert: Send Instant Notification with 1-Click Approval Buttons to Support Group
                from config import TELEGRAM_SUPPORT_GROUP_ID
                if bot and TELEGRAM_SUPPORT_GROUP_ID:
                    try:
                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                        admin_kb = InlineKeyboardMarkup(inline_keyboard=[
                            [
                                InlineKeyboardButton(text="✅ تفعيل فوري (رجال 🧔)", callback_data=f"admin_approve_man_{telegram_id}"),
                                InlineKeyboardButton(text="✅ تفعيل فوري (نساء 🧕)", callback_data=f"admin_approve_woman_{telegram_id}")
                            ],
                            [
                                InlineKeyboardButton(text="💬 فتح تواصل مع الطالب", url=f"tg://user?id={telegram_id}")
                            ]
                        ])
                        admin_alert_text = (
                            f"⚡ <b>تنبيه إداري: تسجيل جديد قيد الانتظار</b> ⏳\n\n"
                            f"👤 <b>الاسم:</b> {telegram_name} (@{telegram_username or 'بدون معرف'})\n"
                            f"📧 <b>البريد:</b> <code>{email or 'غير محدد'}</code>\n"
                            f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>\n"
                            f"🔢 <b>رقم الطالب:</b> <code>{student_id_input or 'غير محدد'}</code>\n"
                            f"🔗 <b>الرابط / المصدر:</b> <code>{source or 'غير محدد'}</code>\n\n"
                            f"🔍 <i>يمكنك التحقق والضغط مباشرة على زر التفعيل لإرسال روابط المجموعات للطالب فوراً:</i>"
                        )
                        await bot.send_message(
                            chat_id=int(TELEGRAM_SUPPORT_GROUP_ID),
                            text=admin_alert_text,
                            reply_markup=admin_kb,
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        _log.error(f"Error sending admin pending alert: {e}")

                    
                    bot = request.app.get('bot')
                    if bot and telegram_id:
                        try:
                            msg_text = """⏳ <b>طلبك قيد المراجعة والمصادقة</b>

تم تسجيل بياناتك وحسابك على تليجرام بنجاح ✅

يقوم فريق الإدارة بمطابقة الدفع والتحويلات البنكية دورياً. <b>ستصلك رسالة تلقائية هنا على تليجرام برابط مجموعتك الخاصة فور المصادقة</b> دون الحاجة لإعادة التسجيل."""
                            await bot.send_message(chat_id=int(telegram_id), text=msg_text, parse_mode='HTML')
                        except Exception as e:
                            _log.error(f"Error sending pending TG message: {e}")

                    return web.json_response({
                        'success': True,
                        'status': 'pending',
                        'first_name': real_first_name,
                        'message': 'طلبك قيد المراجعة لتأكيد التحويل البنكي أو الرسوم. سيصلك رابط الانضمام فور المصادقة ⏳'
                    })
            else:
                # Cas 2 : L'élève n'est pas encore dans l'Excel -> Buffer d'attente
                numeric_sid = 0
                if student_id_input:
                    try:
                        numeric_sid = int(student_id_input)
                    except Exception:
                        numeric_sid = 0
                await db.add_pending_verification(telegram_id, email, telegram_username, telegram_first_name, phone)
                await log_student_action(numeric_sid, 'LINK_WAITING_EXCEL', f"تسجيل جديد في صالة الانتظار لمطابقة الإكسيل - رقم الطالب المدخل: {student_id_input or 'غير محدد'} - البريد: {email}{source_suffix}", telegram_id=telegram_id, telegram_name=telegram_name, telegram_username=telegram_username)
                # 3. Webhook Admin Alert: Send Instant Notification with 1-Click Approval Buttons to Support Group
                from config import TELEGRAM_SUPPORT_GROUP_ID
                if bot and TELEGRAM_SUPPORT_GROUP_ID:
                    try:
                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                        admin_kb = InlineKeyboardMarkup(inline_keyboard=[
                            [
                                InlineKeyboardButton(text="✅ تفعيل فوري (رجال 🧔)", callback_data=f"admin_approve_man_{telegram_id}"),
                                InlineKeyboardButton(text="✅ تفعيل فوري (نساء 🧕)", callback_data=f"admin_approve_woman_{telegram_id}")
                            ],
                            [
                                InlineKeyboardButton(text="💬 فتح تواصل مع الطالب", url=f"tg://user?id={telegram_id}")
                            ]
                        ])
                        admin_alert_text = (
                            f"⚡ <b>تنبيه إداري: تسجيل جديد قيد الانتظار</b> ⏳\n\n"
                            f"👤 <b>الاسم:</b> {telegram_name} (@{telegram_username or 'بدون معرف'})\n"
                            f"📧 <b>البريد:</b> <code>{email or 'غير محدد'}</code>\n"
                            f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>\n"
                            f"🔢 <b>رقم الطالب:</b> <code>{student_id_input or 'غير محدد'}</code>\n"
                            f"🔗 <b>الرابط / المصدر:</b> <code>{source or 'غير محدد'}</code>\n\n"
                            f"🔍 <i>يمكنك التحقق والضغط مباشرة على زر التفعيل لإرسال روابط المجموعات للطالب فوراً:</i>"
                        )
                        await bot.send_message(
                            chat_id=int(TELEGRAM_SUPPORT_GROUP_ID),
                            text=admin_alert_text,
                            reply_markup=admin_kb,
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        _log.error(f"Error sending admin pending alert: {e}")

                
                bot = request.app.get('bot')
                if bot and telegram_id:
                    try:
                        msg_text = (
                            "⏳ <b>طلبك قيد المراجعة والمصادقة</b>\n\n"
                            "تم تسجيل بياناتك وحسابك على تليجرام بنجاح ✅\n\n"
                            "يقوم فريق الإدارة بمطابقة الدفع والتحويلات البنكية دورياً. "
                            "<b>ستصلك رسالة تلقائية هنا على تليجرام برابط مجموعتك الخاصة فور المصادقة</b> دون الحاجة لإعادة التسجيل."
                        )
                        await bot.send_message(chat_id=int(telegram_id), text=msg_text, parse_mode='HTML')
                    except Exception as e:
                        _log.error(f"Error sending pending TG message: {e}")

                return web.json_response({
                    'success': True,
                    'status': 'pending',
                    'first_name': telegram_first_name,
                    'message': 'تم تسجيل طلبك بنجاح! نحن بصدد تأكيد اشتراكك مع الإدارة، وسنرسل لك رابط مجموعتك هنا تلقائياً فور المصادقة ⏳'
                })
                
    except Exception as e:
        _log.error(f"[AUTH] Error in api_link_account: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def get_student_stats(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not user_id:
            return web.json_response({"success": False, "error": "Missing userId"}, status=400)
            
        import database as db
        overall = await db.get_user_overall_stats(int(user_id))
        rems = await db.get_remaining_questions_count_per_subject(int(user_id))
        emojis = await db.get_all_subjects_status_emojis(int(user_id))
        
        # Calculate progression data
        course_progress = []
        detailed_progress = {}
        try:
            course_progress = await db.get_all_progress(int(user_id))
            for sub in ['sira', 'fiqh', 'aqeeda', 'nahw', 'tajweed']:
                lessons_p, themes_p, years_p = await db.get_detailed_subject_progress(int(user_id), sub)
                detailed_progress[sub] = {
                    'lessons': lessons_p,
                    'themes': themes_p,
                    'years': years_p
                }
        except Exception as prog_err:
            logger.error(f"Error calculating progression stats: {prog_err}")

        # Calculate daily streak or default
        user_info = await db.get_user(int(user_id))
        streak = 0
        if user_info:
            from config import DATABASE_PATH
            import aiosqlite
            async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                async with db_conn.execute("""
                    SELECT COUNT(DISTINCT date(answered_at)) FROM quiz_logs WHERE user_id = ?
                """, (int(user_id),)) as cur:
                    row = await cur.fetchone()
                    streak = row[0] if row else 0

        return web.json_response({
            "success": True,
            "overall": overall,
            "remaining": rems,
            "emojis": emojis,
            "streak": streak,
            "preferredName": user_info.get("preferred_name") or user_info.get("first_name") or "طالب" if user_info else "طالب",
            "courseProgress": course_progress,
            "detailedProgress": detailed_progress
        })
    except Exception as e:
        logger.error(f"Error in get_student_stats: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def get_student_quiz_taxonomy(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        subject = data.get('subject')
        
        if not user_id or not subject:
            return web.json_response({"success": False, "error": "Missing userId or subject"}, status=400)
            
        import aiosqlite
        from config import DATABASE_PATH
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # Fetch all active questions for the subject to build the taxonomy tree
            subj_variants = [subject]
            if subject.lower() in ('aqeeda', 'aqida'):
                subj_variants = ['aqeeda', 'aqida']
            
            placeholders = ",".join("?" for _ in subj_variants)
            query = f"SELECT id, course_number, theme, sub_theme, hijra_year, question FROM questions WHERE subject IN ({placeholders}) AND is_active = 1"
            
            async with db.execute(query, subj_variants) as cursor:
                rows = await cursor.fetchall()
                
            questions = []
            for row in rows:
                questions.append({
                    "id": row["id"],
                    "lessonNum": row["course_number"] or 1,
                    "theme": row["theme"] or "مواضيع عامة",
                    "subTheme": row["sub_theme"] or "أساسيات",
                    "hijriYear": row["hijra_year"] or "غير محدد",
                    "title": row["question"][:50] + "..." if row["question"] else "سؤال"
                })
                
        import json
        return web.json_response({"success": True, "questions": questions}, dumps=lambda obj: json.dumps(obj, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"Error in get_student_quiz_taxonomy: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def get_student_quiz_options(request):
    try:
        subject = request.query.get('subject')
        if not subject:
            return web.json_response({"success": False, "error": "Missing subject"}, status=400)
            
        import database as db
        
        lessons = await db.get_available_lessons(subject)
        themes = await db.get_available_themes(subject)
        years = []
        if subject.lower() == 'sira':
            years = await db.get_available_sira_years()
            
        return web.json_response({
            "success": True,
            "lessons": lessons,
            "themes": themes,
            "years": years
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def get_student_quiz_questions(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        subject = data.get('subject')
        course_numbers = data.get('courseNumbers', [])
        source = data.get('source', 'all') # 'all', 'favorites', 'errors'
        mode = data.get('mode', 'lessons')
        limit = int(data.get('limit', 10))
        
        if not user_id:
            return web.json_response({"success": False, "error": "Missing userId"}, status=400)
            
        import database as db
        from config import DATABASE_PATH
        import aiosqlite
        
        questions = []
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            
            if source == 'favorites':
                query = """
                    SELECT q.* FROM user_favorites f
                    JOIN questions q ON f.question_id = q.id
                    WHERE f.user_id = ?
                """
                params = [int(user_id)]
                if subject:
                    query += " AND q.subject = ?"
                    params.append(subject.lower().strip())
                if mode == 'themes' and course_numbers:
                    theme_ids = course_numbers
                    placeholders = ",".join("?" for _ in theme_ids)
                    query_nodes = f"SELECT id FROM thematic_nodes WHERE id IN ({placeholders}) OR parent_id IN ({placeholders})"
                    params_nodes = list(theme_ids) + list(theme_ids)
                    async with db_conn.execute(query_nodes, params_nodes) as cursor:
                        nodes_rows = await cursor.fetchall()
                        node_ids = [r['id'] for r in nodes_rows]
                        
                    if node_ids:
                        node_placeholders = ",".join("?" for _ in node_ids)
                        query += f" AND q.thematic_node_id IN ({node_placeholders})"
                        params.extend(node_ids)
                    else:
                        query += " AND 1=0" # No nodes found
                elif mode == 'years' and course_numbers:
                    placeholders = ",".join("?" for _ in course_numbers)
                    query += f" AND q.hijra_year IN ({placeholders})"
                    params.extend(course_numbers)
                elif course_numbers:
                    placeholders = ",".join("?" for _ in course_numbers)
                    query += f" AND q.course_number IN ({placeholders})"
                    params.extend(course_numbers)
                
                query += " ORDER BY random() LIMIT ?"
                params.append(limit)
                async with db_conn.execute(query, params) as cur:
                    rows = await cur.fetchall()
                    questions = [dict(r) for r in rows]
                    
            elif source == 'errors':
                query = """
                    SELECT q.* FROM user_errors e
                    JOIN questions q ON e.question_id = q.id
                    WHERE e.user_id = ?
                """
                params = [int(user_id)]
                if subject:
                    query += " AND q.subject = ?"
                    params.append(subject.lower().strip())
                if mode == 'themes' and course_numbers:
                    theme_ids = course_numbers
                    placeholders = ",".join("?" for _ in theme_ids)
                    query_nodes = f"SELECT id FROM thematic_nodes WHERE id IN ({placeholders}) OR parent_id IN ({placeholders})"
                    params_nodes = list(theme_ids) + list(theme_ids)
                    async with db_conn.execute(query_nodes, params_nodes) as cursor:
                        nodes_rows = await cursor.fetchall()
                        node_ids = [r['id'] for r in nodes_rows]
                        
                    if node_ids:
                        node_placeholders = ",".join("?" for _ in node_ids)
                        query += f" AND q.thematic_node_id IN ({node_placeholders})"
                        params.extend(node_ids)
                    else:
                        query += " AND 1=0" # No nodes found
                elif mode == 'years' and course_numbers:
                    placeholders = ",".join("?" for _ in course_numbers)
                    query += f" AND q.hijra_year IN ({placeholders})"
                    params.extend(course_numbers)
                elif course_numbers:
                    placeholders = ",".join("?" for _ in course_numbers)
                    query += f" AND q.course_number IN ({placeholders})"
                    params.extend(course_numbers)
                
                query += " ORDER BY random() LIMIT ?"
                params.append(limit)
                async with db_conn.execute(query, params) as cur:
                    rows = await cur.fetchall()
                    questions = [dict(r) for r in rows]
                    
            else:
                query = "SELECT * FROM questions WHERE 1=1"
                params = []
                if subject:
                    query += " AND subject = ?"
                    params.append(subject.lower().strip())
                if mode == 'themes' and course_numbers:
                    theme_ids = course_numbers
                    placeholders = ",".join("?" for _ in theme_ids)
                    query_nodes = f"SELECT id FROM thematic_nodes WHERE id IN ({placeholders}) OR parent_id IN ({placeholders})"
                    params_nodes = list(theme_ids) + list(theme_ids)
                    async with db_conn.execute(query_nodes, params_nodes) as cursor:
                        nodes_rows = await cursor.fetchall()
                        node_ids = [r['id'] for r in nodes_rows]
                        
                    if node_ids:
                        node_placeholders = ",".join("?" for _ in node_ids)
                        query += f" AND thematic_node_id IN ({node_placeholders})"
                        params.extend(node_ids)
                    else:
                        query += " AND 1=0" # No nodes found
                elif mode == 'years' and course_numbers:
                    placeholders = ",".join("?" for _ in course_numbers)
                    query += f" AND hijra_year IN ({placeholders})"
                    params.extend(course_numbers)
                elif course_numbers:
                    # Convert to int or string list safely
                    parsed_courses = [int(x) if str(x).isdigit() else str(x) for x in course_numbers]
                    placeholders = ",".join("?" for _ in parsed_courses)
                    query += f" AND course_number IN ({placeholders})"
                    params.extend(parsed_courses)
                
                # Exclude AI generated if settings say so
                async with db_conn.execute("SELECT value FROM settings WHERE key='disable_ai_for_students'") as cur:
                    row = await cur.fetchone()
                    if row and row[0].lower() == 'true':
                        query += " AND source != 'generated_by_gemini'"
                
                query += " ORDER BY random() LIMIT ?"
                params.append(limit)
                async with db_conn.execute(query, params) as cur:
                    rows = await cur.fetchall()
                    questions = [dict(r) for r in rows]
                
                # Broad fallback: if specific course query returns 0 questions, get any questions for this subject
                if not questions and subject:
                    fb_query = "SELECT * FROM questions WHERE subject = ? ORDER BY random() LIMIT ?"
                    async with db_conn.execute(fb_query, [subject.lower().strip(), limit]) as cur:
                        rows = await cur.fetchall()
                        questions = [dict(r) for r in rows]

        favorites_list = await db.get_user_favorites(int(user_id))
        for q in questions:
            q['correct_choice'] = db.get_correct_choice_letter(q)
            q['is_favorite'] = q['id'] in favorites_list

        import json
        return web.json_response({"success": True, "questions": questions}, dumps=lambda obj: json.dumps(obj, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Error in get_student_quiz_questions: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def submit_student_quiz_answer(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        question_id = data.get('questionId')
        is_correct = bool(data.get('isCorrect'))
        wrong_answer = data.get('wrongAnswer', '')
        
        if not user_id or not question_id:
            return web.json_response({"success": False, "error": "Missing parameters"}, status=400)
            
        import database as db
        
        await db.log_quiz_answer(int(user_id), int(question_id), is_correct)
        await db.update_question_progress(int(user_id), int(question_id), is_correct)
        
        q = await db.get_question_by_id(int(question_id))
        if q:
            subject = q.get('subject', 'fiqh')
            if is_correct:
                await db.remove_error(int(user_id), int(question_id))
            else:
                await db.add_error(int(user_id), int(question_id), subject, wrong_answer)
                
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error in submit_student_quiz_answer: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def toggle_student_favorite(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        question_id = data.get('questionId')
        is_fav = bool(data.get('isFavorite'))
        
        if not user_id or not question_id:
            return web.json_response({"success": False, "error": "Missing parameters"}, status=400)
            
        import database as db
        q = await db.get_question_by_id(int(question_id))
        if not q:
            return web.json_response({"success": False, "error": "Question not found"}, status=404)
            
        subject = q.get('subject', 'fiqh')
        if is_fav:
            success = await db.add_favorite(int(user_id), int(question_id), subject)
        else:
            success = await db.remove_favorite(int(user_id), int(question_id))
            
        return web.json_response({"success": success})
    except Exception as e:
        logger.error(f"Error in toggle_student_favorite: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)



async def api_chat(request):
    try:
        data = await request.json()
        message = data.get('message', '').strip()
        user_id = data.get('user_id')
        
        if not message:
            return web.json_response({"success": False, "error": "Empty message"}, status=400)
            
        import importlib
        import config as cfg_module
        import database as db
        
        importlib.reload(cfg_module)
        api_keys = getattr(cfg_module, "GEMINI_API_KEYS", [])
        if not api_keys and getattr(cfg_module, "GEMINI_API_KEY", ""):
            api_keys = [cfg_module.GEMINI_API_KEY]
            
        if not api_keys:
            return web.json_response({"success": False, "reply": "عذرا، لم يتم تكوين مفتاح API."})
            
        # Retrieve relevant FAQs to ground the AI
        entries = await db.search_faq(message)
        faq_context = ""
        
        if not entries:
            # Fallback in-memory search
            all_faqs = await db.get_faq_entries()
            matches = []
            for faq in all_faqs:
                q = faq.get('question', '').lower()
                a = faq.get('answer', '')
                if message.lower() in q or q in message.lower() or any(w in q for w in message.lower().split() if len(w) > 4):
                    matches.append(f"س: {faq['question']}\nج: {a}")
                    if len(matches) >= 5:
                        break
            if matches:
                faq_context = "\n\nمعلومات رسمية من الأكاديمية قد تساعدك في الإجابة:\n" + "\n---\n".join(matches)
        else:
            matches = [f"س: {faq['question']}\nج: {faq['answer']}" for faq in entries[:5]]
            faq_context = "\n\nمعلومات رسمية من الأكاديمية قد تساعدك في الإجابة:\n" + "\n---\n".join(matches)

        import google.generativeai as genai
        import random
        api_key = random.choice(api_keys)
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-flash-latest')

        # Strict RAG Prompt to prevent abuse and improve UI formatting
        prompt = f"""أنت "المساعد الذكي" لأكاديمية الباجي. مهمتك مساعدة الطلاب بذكاء وود.
التعليمات:
1. لا تقم بالترحيب الطويل، أجب عن السؤال مباشرة لكي تكون المحادثة سريعة وعملية.
2. استخدم HTML للتنسيق بدلاً من Markdown. (مثلاً استخدم <b>نص</b>).
3. إليك سياق المعلومات الأساسية المسموح لك باستخدامها كمرجع:
{faq_context}

4. إذا كان السؤال متوفراً في السياق، أجب بوضوح وإيجاز.
5. إذا كان السؤال يخص الأكاديمية لكنك لا تعرف الإجابة الدقيقة، حاول مساعدته بشكل عام أو اطلب منه توضيح سؤاله أكثر. لا تخبره بفتح تذكرة إلا إذا كان يطلب مساعدة تقنية معقدة جداً أو مالية لا تستطيع حلها.
6. إذا قررت أن المشكلة تتطلب حقاً تدخل الإدارة (تذكرة دعم)، يجب عليك إضافة هذا الزر في نهاية رسالتك لكي يتمكن من فتح التذكرة فعلياً:
<br><br><button class="chip" style="background:#e74c3c; color:#fff; padding:8px 15px; border:none; border-radius:12px; font-weight:bold; cursor:pointer;" onclick="window.location.href='ask.html'">🎫 فتح تذكرة دعم (Créer un ticket)</button>

7. في نهاية إجابتك العادية (إذا لم يفتح تذكرة)، اقترح سؤالين كأزرار تفاعلية لاستكمال المحادثة، بهذا التنسيق:
<br><br>
<button class="chip" style="background:var(--accent); color:#000; margin-top:5px; padding:5px 10px; border:none; border-radius:12px;" onclick="sendAiQuickMessage('السؤال الأول')">السؤال الأول</button>
<button class="chip" style="background:var(--accent); color:#000; margin-top:5px; padding:5px 10px; border:none; border-radius:12px;" onclick="sendAiQuickMessage('السؤال الثاني')">السؤال الثاني</button>

سؤال الطالب: {message}"""

        response = model.generate_content(prompt)
        
        return web.json_response({"success": True, "reply": response.text})
    except Exception as e:
        import logging
        logging.error(f"Error in api_chat: {e}")
        return web.json_response({"success": False, "reply": "عذراً، حدث خطأ أثناء معالجة طلبك."})

async def api_support_rag_check(request):
    try:
        data = await request.json()
        theme = data.get('theme', '')
        subtheme = data.get('subtheme', '')
        msg = data.get('message', '').lower()
        
        if not msg:
            return web.json_response({'found': False})
            
        import database as db
        
        # We will search the SQLite faq_entries table
        entries = await db.search_faq(msg)
        
        if not entries:
            # Try a broader search by just fetching all and filtering in memory
            all_faqs = await db.get_faq_entries()
            matches = []
            for faq in all_faqs:
                q = faq.get('question', '').lower()
                a = faq.get('answer', '')
                if msg in q or q in msg or any(word in q for word in msg.split() if len(word) > 4):
                    matches.append({
                        'question': faq['question'],
                        'answer': a,
                        'story_id': None
                    })
                    if len(matches) >= 3:
                        break
        else:
            matches = []
            for faq in entries[:3]:
                matches.append({
                    'question': faq['question'],
                    'answer': faq['answer'],
                    'story_id': None
                })
        
        if matches:
            return web.json_response({'found': True, 'matches': matches})
        else:
            return web.json_response({'found': False})
    except Exception as e:
        logger.error(f"Error in rag_check: {e}")
        return web.json_response({'found': False})

async def api_admin_get_tickets(request):
    try:
        import database as db
        from aiohttp import web
        tickets = await db.get_all_crm_tickets()
        return web.json_response({'tickets': tickets})
    except Exception as e:
        import traceback
        traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_admin_delete_student(request):
    try:
        user_id = request.match_info.get('id')
        if not user_id:
            return web.json_response({"success": False, "error": "Missing ID"}, status=400)
        import database as db
        await db.delete_user_data(int(user_id))
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Delete student error: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_admin_get_students(request):
    import os, json
    from aiohttp import web
    tickets_file = os.path.join(os.path.dirname(__file__), 'tickets_db.json')
    students = {}
    if os.path.exists(tickets_file):
        try:
            with open(tickets_file, 'r', encoding='utf-8') as f:
                tickets = json.load(f)
                for t in tickets:
                    tid = str(t.get('telegram_id', 'unknown'))
                    if tid not in students:
                        students[tid] = {
                            'telegram_id': tid,
                            'name': t.get('first_name') or t.get('username') or 'طالب',
                            'last_active': t.get('timestamp'),
                            'tickets_count': 1,
                            'total_paid': 'غير متوفر'
                        }
                    else:
                        students[tid]['tickets_count'] += 1
                        if t.get('timestamp') and t.get('timestamp') > students[tid]['last_active']:
                            students[tid]['last_active'] = t.get('timestamp')
        except Exception as e:
            print("Error loading students:", e)
    
    return web.json_response({'students': list(students.values())})

async def api_support(request):
    try:
        content_type = request.content_type if request.content_type else ''
        file_data = None
        file_name = None
        
        if 'multipart/form-data' in content_type:
            reader = await request.multipart()
            data = {}
            async for field in reader:
                if field.name == 'attachment':
                    file_name = field.filename
                    file_data = await field.read()
                else:
                    data[field.name] = await field.text()
            
            theme = data.get('theme')
            subtheme = data.get('subtheme')
            msg = data.get('message')
            telegram_id = data.get('telegram_id')
            username = data.get('username', 'غير معروف')
            first_name = data.get('first_name', 'غير معروف')
            auto_resolved = data.get('auto_resolved') == 'true'
            ai_reply = data.get('ai_reply')
        else:
            data = await request.json()
            theme = data.get('theme')
            subtheme = data.get('subtheme')
            msg = data.get('message')
            telegram_id = data.get('telegram_id')
            username = data.get('username', 'غير معروف')
            first_name = data.get('first_name', 'غير معروف')
            auto_resolved = data.get('auto_resolved', False)
            ai_reply = data.get('ai_reply')
            file_data = data.get('file_data')
            file_name = data.get('file_name')

        import database as db
        
        status = 'resolved' if auto_resolved else 'new'
        ai_topic = 'IA' if auto_resolved else ''
        
        story_id = data.get('story_id')
        if ai_reply and story_id is not None:
            ai_reply += f'<br><br><button onclick="openStoryViewer({story_id})" style="background:linear-gradient(135deg, #FF416C, #FF4B2B); color:white; border:none; padding:8px 16px; border-radius:12px; cursor:pointer; font-family:\'Tajawal\'; font-weight:bold; display:inline-flex; align-items:center; gap:6px;">🎬 عرض التوضيح المباشر (Story)</button>'
        
        db_msg = msg
        if file_name:
            db_msg = msg + f"\n\n[مرفق: {file_name}]"
            
        ticket_id = await db.create_crm_ticket(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            theme=theme,
            subtheme=subtheme,
            message=db_msg,
            status=status,
            is_ghost=auto_resolved,
            ai_topic=ai_topic,
            file_data=file_data,
            file_name=file_name,
            ai_reply=ai_reply
        )
        
        if not auto_resolved:
            import requests
            from config import TELEGRAM_BOT_TOKEN, TELEGRAM_SUPPORT_GROUP_ID
            text = f'🆘 <b>طلب مساعدة / استفسار جديد #{ticket_id}</b>\n\n'
            text += f'👤 <b>الطالب:</b> {first_name} (@{username})\n'
            text += f'🆔 <b>Telegram ID:</b> {telegram_id}\n'
            text += f'📂 <b>القسم:</b> {theme}\n'
            text += f'🔖 <b>التفاصيل:</b> {subtheme}\n\n'
            text += f'📝 <b>الرسالة:</b>\n{msg}\n\n'
            text += f'🔗 للرد، يرجى الدخول إلى لوحة التحكم (Admin Dashboard /federer).'
            
            url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
            payload = {
                'chat_id': TELEGRAM_SUPPORT_GROUP_ID,
                'text': text,
                'parse_mode': 'HTML'
            }
            if file_data:
                files = {'document': (file_name, file_data)}
                payload['caption'] = text
                del payload['text']
                doc_url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument'
                requests.post(doc_url, data=payload, files=files)
            else:
                requests.post(url, json=payload)
        
        from aiohttp import web
        return web.json_response({'success': True, 'ticket_id': ticket_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


MOCK_STUDENTS = {
    "jean.dupont@email.com": {
        "dob": "2000-05-15",
        "first_name": "Jean",
        "last_name": "Dupont",
        "telegram_id": "123456789",
        "telegram_username": "@jeand"
    },
    "test@test.com": {
        "dob": "1999-01-01",
        "first_name": "Élève",
        "last_name": "Test",
        "telegram_id": "987654321",
        "telegram_username": "@elevetest"
    }
}

async def api_login(request: web.Request):
    try:
        data = await request.json()
        email = data.get('email', '').lower()
        dob = data.get('dob', '')
        
        student = MOCK_STUDENTS.get(email)
        if student and student['dob'] == dob:
            # Setting a secure cookie for session could be done here, 
            # for now we return success and let front-end store state.
            return web.json_response({
                'success': True, 
                'user': student
            })
        else:
            return web.json_response({'success': False, 'message': 'Identifiants incorrects.'}, status=401)
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_login(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'login.html'))

async def api_tickets_create(request: web.Request):
    try:
        reader = await request.multipart()
        category = ''
        title = ''
        content = ''
        filename = None
        
        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        while True:
            field = await reader.next()
            if field is None:
                break
            
            if field.name == 'category':
                category = (await field.read()).decode('utf-8')
            elif field.name == 'title':
                title = (await field.read()).decode('utf-8')
            elif field.name == 'content':
                content = (await field.read()).decode('utf-8')
            elif field.name == 'file':
                filename = field.filename
                if filename:
                    # Secure filename
                    import uuid
                    filename = str(uuid.uuid4())[:8] + "_" + filename.replace("/", "").replace("\\", "")
                    file_path = os.path.join(upload_dir, filename)
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await field.read_chunk()
                            if not chunk:
                                break
                            f.write(chunk)
        
        return web.json_response({
            'success': True, 
            'message': 'Ticket créé avec succès.',
            'attachment': filename
        })
    except Exception as e:
        import traceback
        return web.json_response({'success': False, 'error': str(e), 'trace': traceback.format_exc()}, status=500)

async def start_web_server(bot: Bot):
    app = web.Application(middlewares=[cors_middleware], client_max_size=1024**2 * 50)
    app['bot'] = bot
    
    app.router.add_get('/health', lambda r: web.Response(text='OK'))
    app.router.add_get('/', handle_reader)
    app.router.add_get('/index.html', handle_reader)
    app.router.add_get('/link.html', handle_link)
    app.router.add_get('/login.html', handle_login)
    app.router.add_post('/api/login', api_login)
    app.router.add_post('/api/tickets/create', api_tickets_create)
    
    async def handle_tuto(request):
        html_path = os.path.join(DASHBOARD_DIR, 'tuto.html')
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return web.Response(text=content, content_type='text/html')
        except FileNotFoundError:
            return web.Response(text="Tutorial not found", status=404)
            
    async def handle_guide(request):
        html_path = os.path.join(DASHBOARD_DIR, 'guide.html')
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return web.Response(
                text=content, 
                content_type='text/html',
                headers={'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0', 'Pragma': 'no-cache'}
            )
        except FileNotFoundError:
            return web.Response(text="Guide not found", status=404)

    app.router.add_get('/tuto.html', handle_tuto)
    app.router.add_get('/guide.html', handle_guide)
    app.router.add_get('/admin-guide.html', lambda r: web.FileResponse(os.path.join(DASHBOARD_DIR, 'admin-guide.html')))
    app.router.add_get('/admin-guide', lambda r: web.FileResponse(os.path.join(DASHBOARD_DIR, 'admin-guide.html')))
    app.router.add_get('/interactive.html', handle_interactive)
    app.router.add_get('/admin_mindmap.html', handle_admin_mindmap)
    app.router.add_get('/course_slides.html', handle_course_slides)
    app.router.add_get('/course_slides.css', handle_course_slides_css)
    app.router.add_get('/course_slides.js', handle_course_slides_js)
    
    app.router.add_get('/editor', handle_editor)
    app.router.add_get('/editor.html', handle_editor)
    app.router.add_get('/support', handle_support_app)
    app.router.add_get('/support.css', handle_support_css)
    app.router.add_static('/js/', os.path.join(os.path.dirname(__file__), 'dashboard', 'js'))
    app.router.add_static('/diagrams/', os.path.join(DASHBOARD_DIR, 'diagrams'))
    app.router.add_get('/admin', handle_admin)
    app.router.add_get('/admin.html', handle_admin)
    app.router.add_get('/admin-bot', handle_admin_bot)
    app.router.add_get('/admin-bot.html', handle_admin_bot)
    app.router.add_get('/admin-support', handle_admin_support)
    app.router.add_get('/admin-support.html', handle_admin_support)
    app.router.add_get('/admin.css', handle_admin_css)
    app.router.add_get('/admin.js', handle_admin_js)
    app.router.add_get('/admin-late.js', handle_admin_late_js)
    app.router.add_get('/logo_albaji.png', handle_logo_albaji_png)
    app.router.add_get('/logo_albaji.svg', handle_logo_albaji_svg)
    app.router.add_get('/logo.svg', handle_logo_albaji_svg)
    app.router.add_get('/logo.png', handle_logo_albaji_png)
    async def handle_tuto_jpg(request):
        return web.FileResponse(os.path.join(DASHBOARD_DIR, 'tuto.jpg'), headers={'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'})

    async def handle_dossiertelegram_jpg(request):
        return web.FileResponse(os.path.join(DASHBOARD_DIR, 'dossiertelegram.jpg'), headers={'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'})

    async def handle_albaji_preview(request):
        p = os.path.join(DASHBOARD_DIR, 'albaji_preview.jpg')
        if not os.path.exists(p):
            p = os.path.join(DASHBOARD_DIR, 'tuto.jpg')
        return web.FileResponse(p, headers={'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'})

    app.router.add_get('/tuto.mp4', lambda r: web.FileResponse(os.path.join(DASHBOARD_DIR, 'tuto.mp4')))
    app.router.add_get('/tuto.jpg', handle_tuto_jpg)
    app.router.add_get('/dossiertelegram.jpg', handle_dossiertelegram_jpg)
    app.router.add_get('/albaji_preview.jpg', handle_albaji_preview)
    app.router.add_get('/search', handle_search)
    app.router.add_get('/search.html', handle_search)
    app.router.add_get('/transcripts.json', handle_transcripts)
    app.router.add_get('/quran_db.json', handle_quran)

    app.router.add_get('/quiz_journey', handle_quiz_journey)
    app.router.add_get('/quiz_journey.html', handle_quiz_journey)
    app.router.add_get('/quiz_tracker.html', lambda r: web.FileResponse(os.path.join(DASHBOARD_DIR, 'quiz_tracker.html')))
    app.router.add_get('/quiz_mindmap.html', lambda r: web.FileResponse(os.path.join(DASHBOARD_DIR, 'quiz_mindmap.html')))
    app.router.add_get('/quiz_tree.html', lambda r: web.FileResponse(os.path.join(DASHBOARD_DIR, 'quiz_tree.html')))
    app.router.add_get('/quiz_mosaic.html', lambda r: web.FileResponse(os.path.join(DASHBOARD_DIR, 'quiz_mosaic.html')))
    app.router.add_get('/test', handle_test)
    app.router.add_get('/test.html', handle_test)
    app.router.add_get('/reader', handle_reader)
    app.router.add_get('/reader.html', handle_reader)
    app.router.add_get('/reader.js', handle_reader_js)
    app.router.add_get('/exam.js', handle_exam_js)
    app.router.add_get('/quiz.js', handle_quiz_js)
    app.router.add_get('/reader.css', handle_reader_css)
    app.router.add_get('/ask', handle_support)
    app.router.add_post('/api/chat', api_chat)
    app.router.add_post('/api/support/rag_check', api_support_rag_check)
    app.router.add_get('/api/admin/tickets', api_admin_get_tickets)
    register_crm_routes(app)
    app.router.add_get('/api/admin/students', api_admin_get_students)
    app.router.add_delete('/api/admin/students/{id}', api_admin_delete_student)
    app.router.add_post('/api/support', api_support)
    app.router.add_get('/ask.html', handle_support)
    app.router.add_get('/app.html', handle_app)
    app.router.add_get('/api/tickets/student', get_student_tickets)
    
    # Live Radar
    app.router.add_post('/api/presence/ping', api_presence_ping)
    app.router.add_get('/api/admin/presence/live', api_admin_presence_live)
    app.router.add_post('/api/tickets/student', get_student_tickets)
    app.router.add_get('/api/tickets/{ticket_id}/messages', get_ticket_messages_api)
    app.router.add_post('/api/tickets/{ticket_id}/reply', reply_ticket_message_api)
    app.router.add_get('/api/triage/match', handle_triage_match)
    app.router.add_post('/api/triage/match', handle_triage_match)
    app.router.add_post('/report-chapter', report_chapter)
    # Student Practice & Quiz API routes
    app.router.add_post('/api/link_account', api_link_account)
    app.router.add_post('/api/validate_student', api_validate_student)
    app.router.add_get('/admin_gateway.html', handle_admin_gateway)
    app.router.add_get('/admin-gateway.html', handle_admin_gateway)
    app.router.add_get('/admin_gateway', handle_admin_gateway)
    app.router.add_get('/admin-gateway', handle_admin_gateway)
    app.router.add_post('/api/admin/gateway/send_bulk_emails', api_admin_send_bulk_emails)
    app.router.add_get('/api/admin/gateway/email_dispatch_status', api_admin_email_dispatch_status)
    app.router.add_get('/api/track/open', api_track_open)
    app.router.add_get('/api/track/click', api_track_click)
    app.router.add_get('/api/admin/gateway/kpi', api_admin_gateway_kpi)
    app.router.add_get('/api/admin/gateway/home_stats', api_admin_gateway_home_stats)
    app.router.add_get('/api/admin/gateway/export_template', api_admin_gateway_export_template)
    app.router.add_get('/api/admin/gateway/export_all', api_admin_gateway_export_all_students)
    app.router.add_get('/api/admin/gateway/stats', api_admin_gateway_stats)
    app.router.add_get('/api/admin/gateway/students', api_admin_gateway_students)
    app.router.add_post('/api/admin/gateway/bulk_action', api_admin_gateway_bulk_action)
    app.router.add_post('/api/admin/gateway/toggle_exclude', api_admin_gateway_toggle_exclude)
    app.router.add_post('/api/admin/gateway/delete_source', api_admin_gateway_delete_source)
    app.router.add_get('/api/admin/gateway/ghost_visitors', api_admin_gateway_ghost_visitors)
    app.router.add_get('/api/admin/gateway/student_timeline', api_admin_gateway_student_timeline)
    app.router.add_post('/api/admin/gateway/add_crm_note', api_admin_gateway_add_crm_note)
    app.router.add_get('/api/admin/gateway/logs', api_admin_gateway_logs)
    app.router.add_get('/api/admin/gateway/logs/all', api_admin_gateway_logs_all)
    app.router.add_get('/api/admin/gateway/check_member', api_admin_gateway_check_member)
    app.router.add_post('/api/admin/gateway/add_student', api_admin_gateway_add_student)
    app.router.add_post('/api/admin/gateway/archive_student', api_admin_gateway_archive_student)
    app.router.add_post('/api/admin/gateway/import_students', api_admin_gateway_import_students)
    app.router.add_get('/api/admin/gateway/import_logs', api_admin_gateway_import_logs)
    app.router.add_post('/api/admin/gateway/sync_sheets', api_admin_gateway_sync_sheets)
    app.router.add_post('/api/admin/gateway/purge_sheets', api_admin_gateway_purge_sheets)
    app.router.add_post('/api/admin/gateway/export_sheets', api_admin_gateway_export_sheets)
    app.router.add_post('/api/admin/gateway/settings', api_admin_gateway_settings)
    app.router.add_get('/api/admin/gateway/settings', api_admin_gateway_settings_get)
    app.router.add_get('/api/admin/gateway/chat', api_admin_gateway_chat)
    app.router.add_post('/api/admin/gateway/action', api_admin_gateway_action)
    app.router.add_post('/api/admin/gateway/queue_sms', api_admin_gateway_queue_sms)
    app.router.add_get('/api/sms_gateway/poll', api_sms_gateway_poll)
    app.router.add_post('/api/sms_gateway/callback', api_sms_gateway_callback)

    app.router.add_post('/api/gateway/sos', api_gateway_sos)
    app.router.add_post('/api/sos', api_gateway_sos)
    app.router.add_post('/api/gateway/log_open', api_gateway_log_open)
    app.router.add_post('/api/gateway/log_action', api_gateway_log_action)
    app.router.add_get('/api/student/folder_link', api_student_folder_link)
    app.router.add_get('/api/admin/links', api_admin_links_get)
    app.router.add_get('/api/admin/group_settings', api_admin_group_settings_get)
    app.router.add_post('/api/admin/group_settings', api_admin_group_settings_save)
    app.router.add_post('/api/admin/students/import_excel', api_admin_import_excel)
    app.router.add_get('/api/admin/pending_verifications', api_admin_pending_verifications)

    app.router.add_get('/api/admin/sos', api_admin_sos_list)
    app.router.add_post('/api/admin/sos/reply', api_admin_sos_reply)
    app.router.add_post('/api/admin/sos/delete', api_admin_sos_delete)
    app.router.add_delete('/api/admin/sos/{id}', api_admin_sos_delete)
    app.router.add_post('/api/student/stats', get_student_stats)
    app.router.add_post('/api/student/quiz/taxonomy', get_student_quiz_taxonomy)
    app.router.add_get('/api/student/quiz/options', get_student_quiz_options)
    app.router.add_post('/api/student/quiz/setup', get_student_quiz_questions)
    app.router.add_post('/api/student/quiz/submit', submit_student_quiz_answer)
    app.router.add_post('/api/student/dashboard-data', get_student_dashboard_data)
    app.router.add_post('/api/student/favorites/toggle', toggle_student_favorite)
    app.router.add_post('/admin/reports', get_admin_reports)
    app.router.add_post('/admin/dashboard-stats', get_admin_dashboard_stats_api)
    app.router.add_post('/admin/resolve-report', resolve_admin_report)
    app.router.add_post('/admin/edit-chapter', edit_course_chapter)
    app.router.add_post('/admin/save-thematic-blocks', save_lesson_axes)
    app.router.add_post('/admin/question', get_admin_question)
    app.router.add_post('/admin/update-question', update_admin_question)
    app.router.add_post('/admin/delete-question', delete_admin_question)
    app.router.add_post('/admin/delete-bulk-questions', delete_bulk_admin_questions)
    app.router.add_post('/admin/toggle-question-active', toggle_question_active_api)
    app.router.add_post('/admin/proposals', get_admin_proposals)
    app.router.add_post('/admin/resolve-proposal', resolve_admin_proposal)
    app.router.add_post('/admin/update-proposal', update_admin_proposal)
    app.router.add_post('/admin/tickets', get_admin_tickets)
    app.router.add_post('/admin/resolve-ticket', resolve_admin_ticket)
    app.router.add_post('/admin/test-group', test_telegram_group)
    app.router.add_post('/admin/broadcast', admin_broadcast)
    app.router.add_post('/admin/questions-list', admin_questions_list)
    app.router.add_post('/admin/get-themes', admin_get_themes)
    app.router.add_post('/admin/questions/stats', get_questions_stats_api)
    app.router.add_post('/admin/info', get_admin_info)
    app.router.add_post('/admin/settings', get_admin_settings)
    app.router.add_post('/admin/update-setting', update_admin_setting)
    app.router.add_post('/admin/purge-old-tickets', purge_old_tickets)
    app.router.add_post('/admin/students', get_admin_students)
    app.router.add_post('/admin/student-details', get_admin_student_details)
    app.router.add_post('/api/tickets/external', receive_external_ticket)
    app.router.add_post('/admin/list-admins', get_admins_list)
    app.router.add_post('/admin/add-admin', add_admin_user)
    app.router.add_post('/admin/remove-admin', remove_admin_user)
    app.router.add_post('/admin/update-ticket-type', update_ticket_type)
    app.router.add_post('/admin/update-ticket-tags', update_ticket_tags)
    app.router.add_post('/admin/canned-responses', get_canned_responses)
    app.router.add_get('/api/media', get_media)
    app.router.add_post('/admin/canned-responses/save', save_canned_response)
    app.router.add_post('/admin/canned-responses/delete', delete_canned_response)
    app.router.add_post('/admin/tickets/claim', claim_admin_ticket)
    app.router.add_post('/admin/save-full-transcript', save_full_transcript)
    app.router.add_post('/admin/questions/generate-ia', generate_questions_ia)
    app.router.add_post('/admin/questions/save-bulk', save_bulk_questions)
    app.router.add_post('/admin/lesson-resources', get_lesson_resources_api)
    app.router.add_post('/admin/save-lesson-resources', save_lesson_resources_api)
    app.router.add_post('/admin/media/stats', get_media_stats_api)
    # Phase 2 â€” Admin permissions by subject/section
    app.router.add_post('/admin/update-permissions', update_admin_permissions)
    # Phase 3 â€” Shared custom views (DB-backed)
    app.router.add_post('/admin/custom-views/list', list_custom_views)
    app.router.add_post('/admin/custom-views/save', save_custom_view)
    app.router.add_post('/admin/custom-views/delete', delete_custom_view)
    app.router.add_post('/admin/custom-views/reorder', reorder_custom_views)
    app.router.add_post('/admin/thematics', get_admin_thematics)
    app.router.add_post('/admin/thematics/node_questions', get_node_questions)
    app.router.add_post('/admin/thematics/save', save_admin_thematics)
    app.router.add_post('/admin/thematics/reorder', reorder_admin_thematics)

    # Expose web server on PORT environment variable, or fallback to 8080 (to avoid conflicts)
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    logger.info(f"ðŸŒ [Backup Web Server] launched on port {port}")
    await site.start()
    logger.info(f"[Web Server] now accepting connections on port {port}")
    asyncio.create_task(init_static_cache())
    
    while True:
        await asyncio.sleep(3600)


async def auto_sync_sheets_task(bot):
    import asyncio
    from sync_sheets import run_google_sheets_sync
    from config import GOOGLE_SHEET_ID, TELEGRAM_ADMIN_IDS
    # Wait a bit before starting the first sync to allow the bot to initialize
    await asyncio.sleep(60)
    while True:
        if GOOGLE_SHEET_ID:
            try:
                imported, new_count, last_new = await run_google_sheets_sync(GOOGLE_SHEET_ID)
                logger.info(f"[AUTO-SYNC] Successfully synchronized {imported} rows from Google Sheets.")
                
                if new_count > 0 and last_new:
                    message = (
                        f"✅ <b>Nouvelle Inscription !</b>\n\n"
                        f"<b>Nouveaux élèves détectés :</b> {new_count}\n"
                        f"<b>Dernier inscrit :</b> {last_new['name']}\n"
                        f"<b>Numéro étudiant :</b> {last_new['id']}"
                    )
                    for admin_id in TELEGRAM_ADMIN_IDS:
                        try:
                            await bot.send_message(admin_id, message, parse_mode='HTML')
                        except Exception as e:
                            logger.error(f"[AUTO-SYNC] Failed to send notification to {admin_id}: {e}")
                            
            except Exception as e:
                logger.error(f"[AUTO-SYNC] Error during synchronization: {e}")
        # Synchronize every 10 minutes
        await asyncio.sleep(600)

async def night_patrol_task(bot):
    import asyncio
    import aiosqlite
    from config import DATABASE_PATH
    from database import log_student_action
    while True:
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                async with db.execute("SELECT value FROM settings WHERE key = 'night_patrol_enabled'") as cur:
                    row = await cur.fetchone()
                    enabled = row[0] == 'true' if row else False
            
            if enabled:
                logger.info("[PATROL] Démarrage de la patrouille des noms...")
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    async with db.execute("SELECT student_id, first_name, telegram_id FROM academy_students WHERE telegram_id IS NOT NULL") as cur:
                        rows = await cur.fetchall()
                
                for row in rows:
                    student_id, real_first_name, telegram_id = row
                    try:
                        user = await bot.get_chat(telegram_id)
                        current_first_name = user.first_name
# Name enforcement disabled per user request
                    except Exception as e:
                        pass
                    await asyncio.sleep(1)
                logger.info("[PATROL] Patrouille terminée.")
        except Exception as e:
            logger.error(f"[PATROL] Erreur: {e}")
        
        await asyncio.sleep(3600) # Run every hour

async def on_startup(bot: Bot):
    logger.info("Initializing database on startup...")
    asyncio.create_task(night_patrol_task(bot))
    # asyncio.create_task(auto_sync_sheets_task(bot)) # Désactivé car le client n'utilise que Excel maintenant
    await db.init_db()
    logger.info("Database initialized.")
    
    # Inject Default FAQs from website
    try:
        import aiosqlite
        from config import DATABASE_PATH
        faq_data = [
            # Registration & Pricing
            ("التسجيل والأسعار", "عام", "كم تبلغ رسوم التسجيل في الأكاديمية؟", "رسوم التسجيل تبلغ 500 درهم أو 600 درهم حسب الباقة، تُدفع مرة واحدة كل سنة دراسية."),
            ("التسجيل والأسعار", "عام", "كيف يمكنني الدفع؟", "يمكن الدفع عن طريق التحويل البنكي، أو ويسترن يونيون للمقيمين خارج المغرب."),
            ("التسجيل والأسعار", "عام", "هل الدراسة في الأكاديمية عن بعد؟", "نعم، الدراسة في الأكاديمية عن بعد بالكامل 100%."),
            ("التسجيل والأسعار", "عام", "ما هي شروط الانضمام؟", "الرغبة الصادقة في طلب العلم الشرعي، ولا يشترط أي شهادة مسبقة."),
            
            # Curriculum & Study Method
            ("البرنامج الدراسي", "البرنامج", "ما هي مدة الدراسة في الأكاديمية؟", "الدراسة تمتد على 4 سنوات (8 فصول دراسية) من التأسيس إلى الإتقان."),
            ("البرنامج الدراسي", "البرنامج", "كيف يتم تقديم الدروس؟", "تقدم الدروس عبر بث مباشر (لايف) وتبقى مسجلة في المنصة لمشاهدتها في أي وقت."),
            ("البرنامج الدراسي", "البرنامج", "ما هي مستويات الدراسة؟", "هناك 4 مستويات متدرجة: المستوى الأول التأسيس، الثاني البناء، الثالث التمكن، والرابع الإتقان."),
            ("البرنامج الدراسي", "البرنامج", "ماذا يدرس الطالب في المستوى الأول (التأسيس)؟", "مبادئ السيرة، العقيدة، الفقه (العبادات)، النحو، التجويد، التزكية، وحفظ القرآن."),
            ("البرنامج الدراسي", "البرنامج", "ماذا يدرس الطالب في المستوى الثاني (البناء)؟", "توسع في الفقه، العقيدة، النحو، مع مصطلح الحديث وأصول الفقه وحفظ القرآن."),
            ("البرنامج الدراسي", "البرنامج", "ماذا يدرس الطالب في المستوى الثالث (التمكن)؟", "فقه الحديث، قراءة نافع، الصرف، البلاغة، القواعد الفقهية، وحفظ القرآن."),
            ("البرنامج الدراسي", "البرنامج", "ماذا يدرس الطالب في المستوى الرابع (الإتقان)؟", "علوم القرآن، تاريخ التشريع، مقاصد الشريعة، الإلحاد المعاصر، وحفظ القرآن."),
            ("البرنامج الدراسي", "المنهج", "هل الدراسة مبنية على مذهب معين؟", "نعم، الدراسة مؤسسة على المذهب المالكي (من الأساس إلى الإتقان)."),
            ("البرنامج الدراسي", "المواد", "كم عدد المواد التي سيتم دراستها؟", "سيتم دراسة 20 مادة شرعية متنوعة على مدار 4 سنوات."),
            ("البرنامج الدراسي", "الشهادة", "هل هناك شهادة عند التخرج؟", "نعم، يحصل الطالب على شهادة تخرج بعد اجتياز جميع المستويات بنجاح."),
            ("البرنامج الدراسي", "الوقت", "كم أحتاج من الوقت أسبوعياً؟", "ثلاث ساعات أسبوعياً تكفي لمتابعة الدروس والمراجعة."),
            
            # Teachers
            ("هيئة التدريس", "عام", "من هم أساتذة الأكاديمية؟", "نخبة من الأساتذة المجازين، منهم: د. محمد الباجي، ذ. رضوان الشطبي، ذ. عبد الصمد بجيجة، ذ. طارق المكي، د. مصطفى العيساوي، ذ. يوسف بلحسن."),
            ("هيئة التدريس", "البرنامج", "هل الأساتذة مجازون؟", "نعم، جميع الأساتذة مجازون ولهم أسانيد معتبرة."),
            ("المنصة", "عام", "هل يمكنني مشاهدة الدروس من الهاتف؟", "نعم، المنصة مصممة لتعمل بسلاسة على الهاتف أو الحاسوب."),
            ("المنصة", "عام", "ماذا أفعل إذا واجهت مشكلة تقنية؟", "يرجى فتح تذكرة دعم (Support Ticket) وسيقوم الفريق التقني بمساعدتك.")
        ]
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            inserted_count = 0
            for cat, subcat, q, a in faq_data:
                async with conn.execute("SELECT id FROM faq_entries WHERE question = ?", (q,)) as cur:
                    exists = await cur.fetchone()
                if not exists:
                    await conn.execute("""
                        INSERT INTO faq_entries 
                        (category, subcategory, question, answer, views, helpful_votes, not_helpful_votes, is_pinned, created_at, updated_at) 
                        VALUES (?, ?, ?, ?, 0, 0, 0, 0, ?, ?)
                    """, (cat, subcat, q, a, now, now))
                    inserted_count += 1
            if inserted_count > 0:
                await conn.commit()
                logger.info(f"Injected {inserted_count} new default FAQs from albajiacademy.com.")
    except Exception as e:
        logger.error(f"Failed to inject default FAQs: {e}")
    try:
        await db.set_setting("current_instance_id", INSTANCE_ID)
        logger.info(f"Registered instance ID in database settings: {INSTANCE_ID}")
    except Exception as e:
        logger.error(f"Failed to register instance ID in database: {e}")
    
    # 1. Set Chat Menu Button (Persistent Bottom-Left Web App Button!)
    try:
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        import os
        base_url = os.getenv("WEBAPP_BASE_URL", "https://oswah.academy")
        menu_url = f"{base_url}/reader.html?v=dash2"
        if not menu_url.startswith("http"):
            menu_url = f"https://{menu_url}"
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🎓 منصة الطالب",
                web_app=WebAppInfo(url=menu_url)
            )
        )
        logger.info(f"Set persistent chat menu button to {menu_url}")
    except Exception as e:
        logger.error(f"Failed to set chat menu button: {e}")

    # 2. Set Bot Descriptions in Arabic
    welcome_description = (
        "مرحباً بك في منصة الطالب التعليمية! 🎓\n\n"
        "هذا البوت هو رفيقك في دراسة وتكرار الدروس والأسئلة لجميع المواد.\n\n"
        "اضغط على (Start) أودخول المنصة للبدء!"
    )
    welcome_short_description = "منصة الطالب التعليمية لمراجعة المواد والأسئلة. 🎓"
    try:
        await bot.set_my_description(welcome_description)
        await bot.set_my_description(welcome_description, language_code="ar")
        await bot.set_my_short_description(welcome_short_description)
        await bot.set_my_short_description(welcome_short_description, language_code="ar")
    except Exception as e:
        logger.warning(f"Could not set bot description: {e}")


class UsernameTrackerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        import asyncio
        if isinstance(event, Message) and event.from_user and not event.from_user.is_bot:
            asyncio.create_task(self.check_username(event.from_user))
        elif isinstance(event, CallbackQuery) and event.from_user and not event.from_user.is_bot:
            asyncio.create_task(self.check_username(event.from_user))
            
        return await handler(event, data)

    async def check_username(self, user):
        import database as db
        import aiosqlite
        from config import DATABASE_PATH
        
        telegram_id = user.id
        username = user.username or ''
        first_name = user.first_name or ''
        last_name = user.last_name or ''
        
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                db_conn.row_factory = aiosqlite.Row
                async with db_conn.execute("SELECT first_name, last_name, username FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
                    user_row = await cur.fetchone()
                
                if user_row:
                    old_username = user_row['username'] or ''
                    old_first = user_row['first_name'] or ''
                    old_last = user_row['last_name'] or ''
                    
                    changed = False
                    notes = []
                    
                    if old_username != username:
                        notes.append(f"• Pseudo changé : @{old_username or 'Aucun'} ➡️ @{username or 'Aucun'}")
                        changed = True
                    if old_first != first_name:
                        notes.append(f"• Prénom changé : {old_first} ➡️ {first_name}")
                        changed = True
                    if old_last != last_name:
                        notes.append(f"• Nom changé : {old_last} ➡️ {last_name}")
                        changed = True
                        
                    if changed:
                        # Mettre à jour la table users
                        await db_conn.execute(
                            "UPDATE users SET username=?, first_name=?, last_name=? WHERE telegram_id=?", 
                            (username, first_name, last_name, telegram_id)
                        )
                        
                        # Vérifier si c'est un élève lié
                        async with db_conn.execute("SELECT student_id FROM academy_students WHERE telegram_id = ?", (telegram_id,)) as cur2:
                            s = await cur2.fetchone()
                            if s:
                                student_id = s['student_id']
                                note_text = "🔄 الهوية متغيرة في تيليجرام (Changement identite) :\n" + "\n".join(notes)
                                await db_conn.execute(
                                    "INSERT INTO student_logs (student_id, telegram_id, action_type, description, telegram_name, telegram_username) VALUES (?, ?, ?, ?, ?, ?)",
                                    (student_id, telegram_id, "CRM_NOTE", f"[بواسطة: النظام - SYSTEM] [نوع: IDENTITE]\n{note_text}", first_name, username)
                                )
                        await db_conn.commit()
                else:
                    # Inserer le fantôme silencieusement
                    await db_conn.execute(
                        "INSERT INTO users (telegram_id, first_name, last_name, username, created_at) VALUES (?, ?, ?, ?, datetime('now'))", 
                        (telegram_id, first_name, last_name, username)
                    )
                    await db_conn.commit()
        except Exception as e:
            import logging
            logging.getLogger('bot').error(f"UsernameTrackerMiddleware error: {e}")


class AccessCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            
        if user_id:
            from handlers.admin import is_admin
            is_adm = is_admin(user_id)
            
            # Check Maintenance Mode
            maint_active = await db.get_setting("maintenance_mode", "False")
            if maint_active == "True" and not is_adm:
                maint_msg = await db.get_setting("maintenance_message", "ðŸš§ Ø§Ù„Ø¨Ùˆت ÙÙŠ Ùˆضع Ø§Ù„ØµÙŠØ§Ù†ة Ù…Ø¤Ù‚ØªØ§Ù‹. Ø³ÙŠØ¹Ùˆد Ù‚Ø±ÙŠØ¨Ø§Ù‹ Ø¨Ø¥Ø°Ù† Ø§Ù„Ù„Ù‡.")
                if isinstance(event, Message):
                    await event.answer(maint_msg, parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer(maint_msg, show_alert=True)
                return
                
            # Check Ban
            is_banned = await db.is_user_banned(user_id)
            if is_banned and not is_adm:
                ban_text = "ðŸš« <b>ØªÙ…ت Ø¨Ù†جاح Ù…Ø¹Ø§Ù„جة Ø­Ø³Ø§Ø¨Ùƒ. Ù‡ذا Ø§Ù„حساب Ù…Ø­Ø¸Ùˆر Ø­Ø§Ù„ÙŠØ§Ù‹ Ù…Ù† Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„Ø¨Ùˆت. ÙŠØ±Ø¬Ù‰ Ø§Ù„ØªÙˆØ§ØµÙ„ Ù…ع Ø§Ù„إدارة Ù„Ù„Ù…ساعدة.</b>"
                if isinstance(event, Message):
                    await event.answer(ban_text, parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer(ban_text, show_alert=True)
                return
                
        return await handler(event, data)

# ====================================================
# LIVE RADAR BACKEND
# ====================================================
import time

ACTIVE_USERS = {}

async def active_users_cleanup_task():
    while True:
        try:
            now = time.time()
            stale_keys = []
            for uid, data in ACTIVE_USERS.items():
                if now - data.get('last_seen', 0) > 30:
                    stale_keys.append(uid)
            for uid in stale_keys:
                del ACTIVE_USERS[uid]
        except Exception as e:
            logger.error(f"[Radar] Cleanup error: {e}")
        await asyncio.sleep(10)

async def api_presence_ping(request):
    try:
        data = await request.json()
        uid = data.get('user_id', 0)
        if uid:
            ACTIVE_USERS[uid] = {
                'name': data.get('name', 'Anonyme'),
                'page': data.get('page', 'Inconnu'),
                'last_seen': time.time()
            }
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_admin_presence_live(request):
    try:
        now = time.time()
        live = []
        for uid, data in ACTIVE_USERS.items():
            live.append({
                'user_id': uid,
                'name': data['name'],
                'page': data['page'],
                'duration': int(now - data.get('last_seen', 0))
            })
        return web.json_response({'success': True, 'active_users': live})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def main():
    try:
        import database as db
        import aiosqlite
        from config import DATABASE_PATH
        if hasattr(db, 'ensure_email_and_score_columns'):
            await db.ensure_email_and_score_columns()
        if hasattr(db, 'ensure_click_tracking_table'):
            await db.ensure_click_tracking_table()

        # --- MIGRATIONS AUTOMATIQUES ---
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            try:
                await db_conn.execute("ALTER TABLE academy_students ADD COLUMN source_file TEXT")
                print("Added source_file column to academy_students")
            except Exception:
                pass
            try:
                await db_conn.execute("ALTER TABLE academy_students ADD COLUMN excluded INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                await db_conn.execute("ALTER TABLE academy_students ADD COLUMN sms_sent INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                await db_conn.execute("ALTER TABLE academy_students ADD COLUMN sms_sent_at TEXT")
                print("Added excluded column to academy_students")
            except Exception:
                pass
            try:
                await db_conn.execute("ALTER TABLE crm_tickets ADD COLUMN conversation TEXT")
                await db_conn.execute("ALTER TABLE crm_tickets ADD COLUMN has_attachment INTEGER DEFAULT 0")
                await db_conn.execute("ALTER TABLE crm_tickets ADD COLUMN file_data TEXT")
                await db_conn.execute("ALTER TABLE crm_tickets ADD COLUMN file_name TEXT")
            except Exception:
                pass
            # --- INDEX DE PERFORMANCE SQLITE ---
            try:
                await db_conn.execute("CREATE INDEX IF NOT EXISTS idx_students_telegram_id ON academy_students(telegram_id)")
                await db_conn.execute("CREATE INDEX IF NOT EXISTS idx_students_magic_token ON academy_students(magic_token)")
                await db_conn.execute("CREATE INDEX IF NOT EXISTS idx_students_email ON academy_students(email)")
                await db_conn.execute("CREATE INDEX IF NOT EXISTS idx_students_phone ON academy_students(phone)")
                await db_conn.execute("CREATE INDEX IF NOT EXISTS idx_students_excluded ON academy_students(excluded)")
                await db_conn.execute("CREATE INDEX IF NOT EXISTS idx_student_logs_sid ON student_logs(student_id)")
                await db_conn.execute("CREATE INDEX IF NOT EXISTS idx_student_logs_tg ON student_logs(telegram_id)")
            except Exception as e:
                print("Index creation warning:", e)
            await db_conn.commit()
        # -------------------------------

            
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            # 1. Guarantee official folder link in group_settings
            await db_conn.execute("""
                CREATE TABLE IF NOT EXISTS group_settings (
                    id INTEGER PRIMARY KEY,
                    general_channel_id TEXT,
                    men_group_id TEXT,
                    women_group_id TEXT,
                    folder_link TEXT,
                    updated_at TEXT
                )
            """)
            # 1. Guarantee official folder link in group_settings
            try:
                await db_conn.execute("""
                    INSERT INTO group_settings (key, value)
                    VALUES ('folder_link', 'https://t.me/addlist/Yw-eXYtl1BVkYTdk')
                    ON CONFLICT(key) DO UPDATE SET value = 'https://t.me/addlist/Yw-eXYtl1BVkYTdk'
                """)
            except Exception: pass
            
            # 2. Guarantee Houssam Bouddou is always seeded and visible in table
            try:
                await db_conn.execute("""
                    INSERT INTO academy_students (student_id, first_name, last_name, email, phone, gender, payment_status, email_sent, is_active, created_at)
                    VALUES ('104820', 'Houssam', 'Bouddou', 'h.bouddou@gmail.com', '+33668959911', 'HOMME', 'PAID', 1, 1, COALESCE(NULLIF(?, ''), datetime('now')))
                    ON CONFLICT(student_id) DO UPDATE SET first_name = 'Houssam', last_name = 'Bouddou', email = 'h.bouddou@gmail.com', phone = '+33668959911', gender = 'HOMME', payment_status = 'PAID'
                """)
            except Exception: pass
            
            await db_conn.commit()
            logger.info("Auto-seeded group_settings and test student 104820 in database.")
    except Exception as e:
        logger.error(f"Startup DB migration warning: {e}")
        
    asyncio.create_task(active_users_cleanup_task())
    
    bot = None
    if TELEGRAM_BOT_TOKEN:
        try:
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
        except Exception as e:
            logger.error(f"Failed to create Bot instance: {e}")
            
    web_server_coro = start_web_server(bot)
    
    if bot:
        dp = Dispatcher(storage=MemoryStorage())
        dp.message.outer_middleware(UsernameTrackerMiddleware())
        dp.callback_query.outer_middleware(UsernameTrackerMiddleware())
        dp.message.outer_middleware(AccessCheckMiddleware())
        dp.callback_query.outer_middleware(AccessCheckMiddleware())
        dp.include_router(auth_router)
        dp.include_router(csat_router)
        dp.startup.register(on_startup)
        
        async def run_bot_polling():
            logger.info("Starting Telegram Bot polling loop...")
            while True:
                try:
                    await bot.delete_webhook(drop_pending_updates=True)
                    logger.info("Polling successfully started and active.")
                    await dp.start_polling(bot, handle_signals=False)
                except Exception as e:
                    logger.error(f"Telegram polling error: {e}")
                    await asyncio.sleep(5)
                    
        await asyncio.gather(web_server_coro, run_bot_polling(), return_exceptions=True)
    else:
        logger.warning("No TELEGRAM_BOT_TOKEN provided. Running Web Server independently.")
        await web_server_coro



async def get_student_dashboard_data(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not user_id:
            return web.json_response({"success": False, "error": "Missing userId"}, status=400)
            
        import database as db
        global_stats = await db.get_student_global_stats(user_id)
        radar = await db.get_student_global_radar(user_id)
        
        # For the interactive map, we can return the progress of the default subject (e.g., fiqh)
        # or we can let the client fetch it via another call. Let's send fiqh and sira to start.
        fiqh_lessons, _, _ = await db.get_detailed_subject_progress(user_id, 'fiqh')
        sira_lessons, _, _ = await db.get_detailed_subject_progress(user_id, 'sira')
        
        map_data = {
            "fiqh": fiqh_lessons,
            "sira": sira_lessons
        }
        
        return web.json_response({
            "success": True,
            "global_stats": global_stats,
            "radar": radar,
            "map_data": map_data
        })
    except Exception as e:
        logger.error(f"Error in get_student_dashboard_data: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)




async def api_support_reply(request):
    try:
        data = await request.json()
        ticket_id = data.get('ticket_id')
        message = data.get('message')
        telegram_id = data.get('telegram_id')
        admin_name = data.get('admin_name', 'Admin')
        
        if not ticket_id or not message or not telegram_id:
             from aiohttp import web
             return web.json_response({'success': False, 'error': 'Missing parameters'}, status=400)
             
        import database as db
        await db.add_crm_ticket_reply(int(ticket_id), 'admin', message, admin_name)
        
        # Send message to user via Telegram
        bot = request.app.get('bot')
        if bot:
            try:
                text = f"📬 <b>رد جديد من إدارة الأكاديمية (تذكرة #{ticket_id})</b>\n\n👤 <b>من:</b> {admin_name}\n💬 <b>الرد:</b>\n{message}\n\nيمكنك مراجعة المحادثة وتقييم الخدمة عبر صندوق الرسائل في التطبيق."
                await bot.send_message(chat_id=int(telegram_id), text=text, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Error sending TG notification to student: {e}")
        
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_ticket_student_reply(request):
    try:
        ticket_id = request.match_info.get('id')
        data = await request.json()
        message = data.get('message', '').strip()
        telegram_id = data.get('telegram_id')
        first_name = data.get('first_name', 'الطالب')
        username = data.get('username', '')
        file_data = data.get('file_data')
        file_name = data.get('file_name')
        
        if not ticket_id or (not message and not file_data):
            from aiohttp import web
            return web.json_response({'success': False, 'error': 'Missing parameters'}, status=400)
            
        import database as db
        await db.add_crm_ticket_reply(int(ticket_id), 'student', message, first_name, file_data=file_data, file_name=file_name)
        
        # Forward follow-up to support group
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_SUPPORT_GROUP_ID
        import requests
        text = f"💬 <b>رد إضافي من الطالب على التذكرة #{ticket_id}</b>\n\n"
        text += f"👤 <b>الطالب:</b> {first_name} (@{username})\n"
        text += f"🆔 <b>Telegram ID:</b> {telegram_id}\n\n"
        text += f"📝 <b>الرد:</b>\n{message}\n\n"
        text += f"🔗 للرد، يرجى الدخول إلى لوحة التحكم (/federer)."
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': TELEGRAM_SUPPORT_GROUP_ID, 'text': text, 'parse_mode': 'HTML'})
        
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_ticket_rate(request):
    try:
        ticket_id = request.match_info.get('id')
        data = await request.json()
        rating = data.get('rating', 5)
        feedback = data.get('feedback', '')
        
        if not ticket_id:
            from aiohttp import web
            return web.json_response({'success': False, 'error': 'Missing ticket id'}, status=400)
            
        import database as db
        await db.rate_crm_ticket(int(ticket_id), int(rating), feedback)
        
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

    except Exception as e:
        import traceback
        traceback.print_exc()
        from aiohttp import web
async def api_admin_assign_ticket(request):
    try:
        data = await request.json()
        ticket_id = data.get('ticket_id')
        admin_name = data.get('admin_name', 'Admin')
        if not ticket_id:
             from aiohttp import web
             return web.json_response({'success': False, 'error': 'Missing parameters'}, status=400)
             
        import database as db
        await db.assign_crm_ticket(ticket_id, admin_name)
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_admin_resolve_ticket(request):
    try:
        data = await request.json()
        ticket_id = data.get('ticket_id')
        if not ticket_id:
             from aiohttp import web
             return web.json_response({'success': False, 'error': 'Missing parameters'}, status=400)
             
        import database as db
        await db.update_crm_ticket_status(ticket_id, 'resolved')
        
        # CSAT : Envoyer une demande de notation a l'eleve via Telegram
        try:
            bot = request.app['bot']
            ticket = await db.get_crm_ticket(ticket_id)
            if ticket and ticket.get('telegram_id'):
                telegram_id = ticket['telegram_id']
                admin_name = ticket.get('assigned_to') or 'equipe support'
                csat_text = (
                    f"\u2705 \u062a\u0645 \u062d\u0644 \u0645\u0634\u0643\u0644\u062a\u0643 \u0628\u0646\u062c\u0627\u062d!\n\n"
                    f"\u062a\u0648\u0644\u0651\u0649 \u0630\u0644\u0643: *{admin_name}*\n\n"
                    f"\u0643\u064a\u0641 \u062a\u0642\u064a\u0651\u0645 \u062c\u0648\u062f\u0629 \u0627\u0644\u062f\u0639\u0645 \u0627\u0644\u0630\u064a \u062a\u0644\u0642\u064a\u062a\u0647\u061f"
                )
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                csat_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="\u2b50", callback_data=f"csat_{ticket_id}_1"),
                    InlineKeyboardButton(text="\u2b50\u2b50", callback_data=f"csat_{ticket_id}_2"),
                    InlineKeyboardButton(text="\u2b50\u2b50\u2b50", callback_data=f"csat_{ticket_id}_3"),
                    InlineKeyboardButton(text="\u2b50\u2b50\u2b50\u2b50", callback_data=f"csat_{ticket_id}_4"),
                    InlineKeyboardButton(text="\u2b50\u2b50\u2b50\u2b50\u2b50", callback_data=f"csat_{ticket_id}_5"),
                ]])
                await bot.send_message(
                    chat_id=int(telegram_id),
                    text=csat_text,
                    parse_mode="Markdown",
                    reply_markup=csat_keyboard
                )
        except Exception as csat_err:
            print(f"[CSAT] Erreur envoi CSAT: {csat_err}")
        
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

def register_crm_routes(app):
    app.router.add_post('/api/support/reply', api_support_reply)
    app.router.add_post('/api/tickets/{id}/reply', api_ticket_student_reply)
    app.router.add_post('/api/tickets/{id}/rate', api_ticket_rate)
    app.router.add_post('/api/admin/assign', api_admin_assign_ticket)
    app.router.add_post('/api/admin/resolve', api_admin_resolve_ticket)
    app.router.add_post('/api/admin/draft_reply', api_admin_draft_reply)
    app.router.add_get('/api/admin/student_profile', api_admin_student_profile)
    # FAQ routes
    app.router.add_get('/api/faq', api_faq_get)
    app.router.add_post('/api/faq/add', api_faq_add)
    app.router.add_post('/api/faq/{id}/update', api_faq_update)
    app.router.add_delete('/api/faq/{id}', api_faq_delete)
    app.router.add_post('/api/faq/{id}/view', api_faq_view)
    app.router.add_post('/api/faq/{id}/vote', api_faq_vote)
    app.router.add_get('/api/faq/analytics', api_faq_analytics)
    app.router.add_get('/api/faq/suggestions', api_faq_suggestions_get)
    app.router.add_post('/api/faq/suggestions/{id}/approve', api_faq_suggestion_approve)
    app.router.add_post('/api/faq/suggestions/{id}/reject', api_faq_suggestion_reject)
    app.router.add_post('/api/faq/suggest', api_faq_suggest_student)
    app.router.add_post('/api/faq/suggest_from_ticket', api_faq_suggest_from_ticket)
    app.router.add_post('/api/tickets/{id}/reopen', api_ticket_reopen)
    app.router.add_post('/api/tickets/{id}/messages/edit', api_ticket_message_edit)

async def api_admin_draft_reply(request):
    try:
        data = await request.json()
        ticket_id = data.get('ticket_id')
        if not ticket_id:
             from aiohttp import web
             return web.json_response({'success': False, 'error': 'Missing parameters'}, status=400)
             
        import database as db
        ticket = await db.get_crm_ticket(ticket_id)
        if not ticket:
             from aiohttp import web
             return web.json_response({'success': False, 'error': 'Ticket not found'}, status=404)
             
        msg = ticket.get('message', '')
        
        # Use existing RAG search logic if available
        try:
            matches = await db.search_similar_triage(msg, use_ai=True)
            if matches and len(matches) > 0:
                best_match = matches[0]
                answer = best_match.get('ai_answer') or best_match.get('answer') or best_match.get('content')
                if answer:
                    draft = f"?????? {ticket.get('first_name', '????')},\n\n{answer}\n\n????? ?? ???? ??? ??????!"
                    from aiohttp import web
                    return web.json_response({'success': True, 'draft': draft})
        except Exception as e:
            print("Draft RAG error:", e)
            
        # Fallback basic draft
        draft = f"?????? {ticket.get('first_name', '????')},\n\n????? ??????? ???? ????? '{ticket.get('theme', '????????')}'.\n\n[???? ??? ???]"
        from aiohttp import web
        return web.json_response({'success': True, 'draft': draft})
    except Exception as e:
        import traceback
        traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_admin_student_profile(request):
    try:
        telegram_id = request.query.get('telegram_id')
        if not telegram_id:
             from aiohttp import web
             return web.json_response({'success': False, 'error': 'Missing parameters'}, status=400)
             
        import database as db
        from config import DATABASE_PATH
        import aiosqlite
        
        tid_int = int(telegram_id)
        profile = {
            'telegram_id': telegram_id,
            'name': 'غير معروف',
            'username': '',
            'email': 'غير مسجل',
            'phone': 'غير مسجل',
            'join_date': 'غير متوفر',
            'status': 'نشط',
            'payment_status': 'غير محدد',
            'recent_tickets': []
        }
        
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            
            # 1. Look in academy_students
            async with db_conn.execute("SELECT first_name, last_name, email, phone, telegram_username, payment_status, is_active, created_at FROM academy_students WHERE telegram_id = ?", (tid_int,)) as cur:
                row = await cur.fetchone()
                if row:
                    fname = row["first_name"] or ""
                    lname = row["last_name"] or ""
                    profile['name'] = f"{fname} {lname}".strip() or "طالب"
                    profile['username'] = row["telegram_username"] or ""
                    profile['email'] = row["email"] or "غير مسجل"
                    profile['phone'] = row["phone"] or "غير مسجل"
                    profile['join_date'] = row["created_at"] or "غير متوفر"
                    profile['status'] = "نشط" if row["is_active"] else "غير نشط"
                    profile['payment_status'] = row["payment_status"] or "مدفوع"

            # 2. If not found, look in users table
            if profile['name'] == 'غير معروف':
                try:
                    async with db_conn.execute("SELECT first_name, username, created_at FROM users WHERE telegram_id = ?", (tid_int,)) as cur:
                        row = await cur.fetchone()
                        if row:
                            profile['name'] = row["first_name"] or "طالب"
                            profile['username'] = row["username"] or ""
                            profile['join_date'] = row["created_at"] or "غير متوفر"
                except Exception:
                    pass

            # 3. Get recent tickets
            async with db_conn.execute("SELECT id, theme, subtheme, status, timestamp, rating FROM crm_tickets WHERE telegram_id = ? ORDER BY timestamp DESC LIMIT 3", (tid_int,)) as cur:
                tickets_rows = await cur.fetchall()
                profile['recent_tickets'] = [dict(r) for r in tickets_rows]
                
        from aiohttp import web
        return web.json_response({'success': True, 'profile': profile})
    except Exception as e:
        import traceback
        traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

    except Exception as e:
        logger.error(f"[API] Error in api_analytics_track: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def api_faq_analytics_stats(request):
    """GET /api/faq/analytics/stats - Admin fetches analytics data"""
    try:
        stats = {
            "top_searches": [],
            "zero_results": [],
            "tab_clicks": {"faq": 0, "new": 0, "inbox": 0}
        }
        
        # 1. Top searches (last 7 days)
        async with db.execute("""
            SELECT keyword, COUNT(*) as cnt 
            FROM faq_analytics 
            WHERE event_type = 'search' AND keyword != '' 
            GROUP BY keyword ORDER BY cnt DESC LIMIT 10
        """) as cur:
            stats["top_searches"] = [{"keyword": row[0], "count": row[1]} for row in await cur.fetchall()]
            
        # 2. Zero-result searches
        async with db.execute("""
            SELECT keyword, COUNT(*) as cnt 
            FROM faq_analytics 
            WHERE event_type = 'search' AND keyword != '' AND has_results = 0 
            GROUP BY keyword ORDER BY cnt DESC LIMIT 10
        """) as cur:
            stats["zero_results"] = [{"keyword": row[0], "count": row[1]} for row in await cur.fetchall()]
            
        # 3. Tab clicks
        async with db.execute("""
            SELECT tab_name, COUNT(*) as cnt 
            FROM faq_analytics 
            WHERE event_type = 'tab_click' AND tab_name != '' 
            GROUP BY tab_name
        """) as cur:
            for row in await cur.fetchall():
                tab_name = row[0]
                if tab_name in stats["tab_clicks"]:
                    stats["tab_clicks"][tab_name] = row[1]
                    
        return web.json_response({"success": True, "stats": stats})
    except Exception as e:
        logger.error(f"[API] Error in api_faq_analytics_stats: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def api_faq_get(request):
    """GET /api/faq?category=&subcategory=&search= - List FAQ entries."""
    try:
        import database as db
        category = request.rel_url.query.get('category', None)
        subcategory = request.rel_url.query.get('subcategory', None)
        search = request.rel_url.query.get('search', None)
        from aiohttp import web
        if search:
            entries = await db.search_faq(search)
        else:
            entries = await db.get_faq_entries(category=category, subcategory=subcategory)
        categories = await db.get_faq_categories()
        return web.json_response({'success': True, 'entries': entries, 'categories': categories})
    except Exception as e:
        import traceback; traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def api_faq_add(request):
    """POST /api/faq/add - Admin adds a new FAQ entry."""
    try:
        data = await request.json()
        import database as db
        from aiohttp import web
        q = data.get('question', '').strip()
        a = data.get('answer', '').strip()
        cat = data.get('category', '').strip()
        subcat = data.get('subcategory', '').strip()
        ticket_id = data.get('source_ticket_id', None)
        if not q or not a or not cat:
            return web.json_response({'success': False, 'error': 'question, answer et category sont requis'}, status=400)
        new_id = await db.add_faq_entry(cat, q, a, subcategory=subcat, source_ticket_id=ticket_id)
        return web.json_response({'success': True, 'id': new_id})
    except Exception as e:
        import traceback; traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def api_faq_update(request):
    """POST /api/faq/{id}/update - Admin edits a FAQ entry."""
    try:
        faq_id = int(request.match_info.get('id'))
        data = await request.json()
        import database as db
        from aiohttp import web
        await db.update_faq_entry(
            faq_id,
            category=data.get('category'),
            subcategory=data.get('subcategory'),
            question=data.get('question'),
            answer=data.get('answer'),
            is_pinned=data.get('is_pinned')
        )
        return web.json_response({'success': True})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def api_faq_delete(request):
    """DELETE /api/faq/{id} - Admin deletes a FAQ entry."""
    try:
        faq_id = int(request.match_info.get('id'))
        import database as db
        await db.delete_faq_entry(faq_id)
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def api_faq_view(request):
    """POST /api/faq/{id}/view - Student viewed a FAQ entry."""
    try:
        faq_id = int(request.match_info.get('id'))
        data = await request.json()
        telegram_id = data.get('telegram_id', None)
        import database as db
        await db.log_faq_view(faq_id, telegram_id=telegram_id)
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def api_faq_vote(request):
    """POST /api/faq/{id}/vote - Student votes helpful or not."""
    try:
        faq_id = int(request.match_info.get('id'))
        data = await request.json()
        helpful = bool(data.get('helpful', True))
        telegram_id = data.get('telegram_id', None)
        import database as db
        await db.vote_faq_helpful(faq_id, helpful, telegram_id=telegram_id)
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def api_faq_analytics(request):
    """GET /api/faq/analytics - Admin gets FAQ usage stats."""
    try:
        import database as db
        analytics = await db.get_faq_analytics()
        from aiohttp import web
        return web.json_response({'success': True, 'data': analytics})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def api_faq_suggestions_get(request):
    """GET /api/faq/suggestions - Admin gets pending FAQ suggestions."""
    try:
        import database as db
        suggestions = await db.get_faq_suggestions(status='pending')
        from aiohttp import web
        return web.json_response({'success': True, 'suggestions': suggestions})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def api_faq_suggestion_approve(request):
    """POST /api/faq/suggestions/{id}/approve - Admin approves a suggestion."""
    try:
        suggestion_id = int(request.match_info.get('id'))
        import database as db
        new_id = await db.approve_faq_suggestion(suggestion_id)
        from aiohttp import web
        return web.json_response({'success': True, 'new_faq_id': new_id})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def api_faq_suggestion_reject(request):
    """POST /api/faq/suggestions/{id}/reject - Admin rejects a suggestion."""
    try:
        suggestion_id = int(request.match_info.get('id'))
        import database as db
        await db.reject_faq_suggestion(suggestion_id)
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

# ====================================================
# END FAQ API ROUTES
# ====================================================



async def api_faq_suggest_student(request):
    try:
        data = await request.json()
        question = data.get('question', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', 'عام')
        telegram_id = data.get('telegram_id', '')
        student_name = data.get('student_name', 'طالب')
        
        if not question:
            from aiohttp import web
            return web.json_response({'success': False, 'error': 'Missing question'}, status=400)
            
        import database as db
        sid = await db.add_student_faq_suggestion(question, description, category, telegram_id, student_name)
        from aiohttp import web
        return web.json_response({'success': True, 'suggestion_id': sid})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_faq_suggest_from_ticket(request):
    try:
        data = await request.json()
        ticket_id = data.get('ticket_id')
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        category = data.get('category', 'عام')
        admin_name = data.get('admin_name', 'Admin')
        
        if not question or not answer:
            from aiohttp import web
            return web.json_response({'success': False, 'error': 'Missing parameters'}, status=400)
            
        import database as db
        sid = await db.add_admin_faq_from_ticket(ticket_id, question, answer, category, admin_name)
        from aiohttp import web
        return web.json_response({'success': True, 'suggestion_id': sid})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_ticket_reopen(request):
    try:
        ticket_id = int(request.match_info.get('id'))
        import database as db
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_SUPPORT_GROUP_ID
        import requests
        
        ok = await db.reopen_crm_ticket(ticket_id)
        if not ok:
            from aiohttp import web
            return web.json_response({'success': False, 'error': 'Ticket not found'}, status=404)
            
        ticket = await db.get_crm_ticket(ticket_id)
        if ticket and TELEGRAM_SUPPORT_GROUP_ID:
            try:
                msg = '🔄 <b>إعادة فتح التذكرة #TK-' + str(ticket_id) + '</b>\n\n👤 <b>الطالب:</b> ' + str(ticket.get('first_name', 'طالب')) + ' (@' + str(ticket.get('username', '')) + ')\n📌 <b>القسم:</b> ' + str(ticket.get('theme', '')) + '\n\nيرجى المتابعة من Dashboard المشرفين (/federer).'
                requests.post('https://api.telegram.org/bot' + str(TELEGRAM_BOT_TOKEN) + '/sendMessage', json={
                    'chat_id': TELEGRAM_SUPPORT_GROUP_ID,
                    'text': msg,
                    'parse_mode': 'HTML'
                })
            except Exception as notify_err:
                print('Reopen notify error:', notify_err)
                
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def api_ticket_message_edit(request):
    try:
        ticket_id = int(request.match_info.get('id'))
        data = await request.json()
        message_index = int(data.get('message_index', 0))
        new_text = data.get('text', '').strip()
        role = data.get('role', 'student')
        
        if not new_text:
            from aiohttp import web
            return web.json_response({'success': False, 'error': 'Missing text'}, status=400)
            
        import database as db
        ok = await db.edit_crm_ticket_message(ticket_id, message_index, new_text, role)
        from aiohttp import web
        return web.json_response({'success': ok})
    except Exception as e:
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)




async def api_admin_group_settings_get(request: web.Request):
    import database as db
    settings = await db.get_group_settings()
    return web.json_response({"success": True, "settings": settings})

async def api_admin_group_settings_save(request: web.Request):
    import database as db
    try:
        data = await request.json()
        general = data.get('general_channel_id', '')
        men = data.get('men_group_id', '')
        women = data.get('women_group_id', '')
        await db.save_group_settings(general, men, women)
        return web.json_response({"success": True, "message": "تم حفظ إعدادات المجموعات بنجاح"})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_admin_import_excel(request: web.Request):
    import database as db
    import logging
    _log = logging.getLogger('bot')
    try:
        data = await request.json()
        records = data.get('records', [])
        if not records:
            return web.json_response({"success": False, "error": "No records provided"}, status=400)
            
        stats = await db.import_students_excel(records)
        
        # Réveil automatique de la file d'attente (Pending Buffer)
        bot = request.app.get('bot')
        pending_list = await db.get_pending_verifications('waiting')
        dispatched_count = 0
        
        if pending_list and bot:
            from config import DATABASE_PATH
            import aiosqlite
            async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                db_conn.row_factory = aiosqlite.Row
                for p in pending_list:
                    p_email = (p.get('email') or '').strip().lower()
                    p_tg = p.get('telegram_id')
                    if not p_email or not p_tg:
                        continue
                    
                    async with db_conn.execute("SELECT * FROM academy_students WHERE LOWER(email) = ? AND payment_status = 'PAID'", (p_email,)) as cur:
                        student_row = await cur.fetchone()
                        
                    if student_row:
                        student_dict = dict(student_row)
                        # Associer le telegram_id s'il ne l'était pas
                        await db_conn.execute("UPDATE academy_students SET telegram_id = ? WHERE LOWER(email) = ?", (p_tg, p_email))
                        await db_conn.commit()
                        
                        # Générer et envoyer les liens uniques
                        await generate_and_send_student_links(bot, p_tg, student_dict, request.app)
                        dispatched_count += 1
                        
        stats["dispatched_pending"] = dispatched_count
        return web.json_response({"success": True, "stats": stats})
    except Exception as e:
        _log.error(f"[EXCEL] Error in api_admin_import_excel: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_admin_pending_verifications(request: web.Request):
    import database as db
    pending = await db.get_pending_verifications('waiting')
    return web.json_response({"success": True, "pending": pending})

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
