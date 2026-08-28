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
    all_lessons = await load_lessons_from_db()
    root_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'transcripts.json')
    dash_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'transcripts.json')
    try:
        with open(root_path, 'w', encoding='utf-8') as f:
            json.dump(all_lessons, f, ensure_ascii=False)
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

# â”€â”€â”€ INSTANCE LOCK (anti-fantÃ´me) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PID_FILE = os.path.join(os.path.dirname(__file__), ".bot.pid")

def _kill_existing_instance():
    """Tue toute instance prÃ©cÃ©dente du bot avant de dÃ©marrer."""
    if not os.path.exists(PID_FILE):
        return
    try:
        with open(PID_FILE, "r") as f:
            old_pid = int(f.read().strip())
        if old_pid == os.getpid():
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

async def handle_logo_png(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'logo.png'))

async def handle_tuto_jpg(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'tuto.jpg'))

async def handle_dossiertelegram_jpg(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'dossiertelegram.jpg'))

async def handle_support(request):
    return web.FileResponse(os.path.join(DASHBOARD_DIR, 'ask.html'))

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
            async with db.execute("SELECT COUNT(*) FROM academy_students") as cur:
                total = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM academy_students WHERE telegram_id IS NOT NULL") as cur:
                linked = (await cur.fetchone())[0]
            async with db.execute("SELECT value FROM settings WHERE key = 'night_patrol_enabled'") as cur:
                row = await cur.fetchone()
                patrol_enabled = row[0] == 'true' if row else False
        return web.json_response({'success': True, 'stats': {'total': total, 'linked': linked, 'patrol_enabled': patrol_enabled}})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_students(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT s.student_id, s.first_name, s.email, s.telegram_id, s.year, s.gender, s.dob,
                       u.first_name as tg_first_name, u.last_name as tg_last_name
                FROM academy_students s
                LEFT JOIN users u ON u.telegram_id = s.telegram_id
                ORDER BY s.first_name ASC
            """) as cur:
                students = [dict(row) for row in await cur.fetchall()]
        return web.json_response({'success': True, 'students': students})
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
                async with db.execute("SELECT action_type, description, timestamp, telegram_id, telegram_name FROM student_logs WHERE telegram_id = ? OR student_id = ? ORDER BY id DESC LIMIT 50", (tid, student_id)) as cur:
                    logs = [dict(row) for row in await cur.fetchall()]
            else:
                async with db.execute("SELECT action_type, description, timestamp, telegram_id, telegram_name FROM student_logs WHERE student_id = ? ORDER BY id DESC LIMIT 50", (student_id,)) as cur:
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
                SELECT sl.action_type, sl.description, sl.timestamp, sl.telegram_id, sl.telegram_name,
                       COALESCE(s.first_name, 'ID:'||sl.student_id) as first_name,
                       u.first_name as tg_first_name, u.last_name as tg_last_name,
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
        data = await request.json()
        email = data.get('email', '').strip().lower()
        dob = data.get('dob', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        student_id = data.get('student_id', '').strip()
        
        if not email or not dob:
            return web.json_response({'success': False, 'error': 'L\'email et la date de naissance sont requis.'})
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT student_id FROM academy_students WHERE email = ?", (email,)) as cur:
                exists = await cur.fetchone()
                if exists:
                    await db.execute("""
                        UPDATE academy_students 
                        SET dob = ?, first_name = ?, last_name = ?
                        WHERE email = ?
                    """, (dob, first_name, last_name, email))
                else:
                    if student_id:
                        await db.execute("""
                            INSERT INTO academy_students (student_id, email, dob, first_name, last_name, year, gender)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (student_id, email, dob, first_name, last_name, '1', 'homme'))
                    else:
                        await db.execute("""
                            INSERT INTO academy_students (email, dob, first_name, last_name, year, gender)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (email, dob, first_name, last_name, '1', 'homme'))
            await db.commit()
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_gateway_import_students(request: web.Request):
    try:
        import aiosqlite
        import openpyxl
        import io
        from config import DATABASE_PATH
        reader = await request.multipart()
        field = await reader.next()
        if not field or field.name != 'file':
            return web.json_response({'success': False, 'error': 'Aucun fichier trouve'})
        
        file_data = await field.read()
        wb = openpyxl.load_workbook(io.BytesIO(file_data))
        sheet = wb.active
        
        headers = [cell.value for cell in sheet[1]]
        def get_col_idx(name):
            for i, h in enumerate(headers):
                if h and name.lower() in str(h).lower():
                    return i
            return None
            
        email_idx = get_col_idx('email') or get_col_idx('mail') or get_col_idx('courriel')
        dob_idx = get_col_idx('dob') or get_col_idx('naissance') or get_col_idx('birth') or get_col_idx('date') or get_col_idx('تاريخ')
        fn_idx = get_col_idx('first') or get_col_idx('prenom') or get_col_idx('prénom') or get_col_idx('اسم')
        ln_idx = get_col_idx('last') or get_col_idx('nom') or get_col_idx('لقب')
        year_idx = get_col_idx('year') or get_col_idx('annee') or get_col_idx('année') or get_col_idx('level') or get_col_idx('niveau')
        gender_idx = get_col_idx('gender') or get_col_idx('genre') or get_col_idx('sexe')

        if email_idx is None: email_idx = 0
        if dob_idx is None: dob_idx = 1
        if fn_idx is None: fn_idx = 2
        if ln_idx is None: ln_idx = 3
        if year_idx is None: year_idx = 4
        if gender_idx is None: gender_idx = 5
        
        imported = 0
        async with aiosqlite.connect(DATABASE_PATH) as db:
            for row in list(sheet.iter_rows(min_row=2)):
                if len(row) <= max(email_idx, dob_idx):
                    continue
                email = str(row[email_idx].value or '').strip().lower()
                dob = str(row[dob_idx].value or '').strip()
                if not email or not dob:
                    continue
                    
                first_name = str(row[fn_idx].value or '').strip() if fn_idx < len(row) else ''
                last_name = str(row[ln_idx].value or '').strip() if ln_idx < len(row) else ''
                year = str(row[year_idx].value or '').strip() if year_idx < len(row) else '1'
                gender = str(row[gender_idx].value or '').strip().lower() if gender_idx < len(row) else 'homme'
                
                async with db.execute("SELECT student_id FROM academy_students WHERE email = ?", (email,)) as cur:
                    exists = await cur.fetchone()
                    if exists:
                        await db.execute("""
                            UPDATE academy_students 
                            SET dob = ?, first_name = ?, last_name = ?, year = ?, gender = ? 
                            WHERE email = ?
                        """, (dob, first_name, last_name, year, gender, email))
                    else:
                        await db.execute("""
                            INSERT INTO academy_students (email, dob, first_name, last_name, year, gender)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (email, dob, first_name, last_name, year, gender))
                imported += 1
            await db.commit()
            
        return web.json_response({'success': True, 'count': imported})
    except Exception as e:
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
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        first_name = data.get('first_name', '')
        
        if not telegram_id:
            return web.json_response({'success': True, 'skipped': 'No telegram_id'})
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT student_id, first_name FROM academy_students WHERE telegram_id = ?", (telegram_id,)) as cur:
                row = await cur.fetchone()
                if row:
                    student_id = row[0]
                    student_name = row[1]
                    await db.execute(
                        "INSERT INTO student_logs (student_id, action_type, description) VALUES (?, ?, ?)",
                        (student_id, 'APP_OPENED', f"فتح الطالب {student_name} التطبيق بنجاح")
                    )
                else:
                    await db.execute(
                        "INSERT INTO student_logs (student_id, action_type, description) VALUES (?, ?, ?)",
                        (0, 'APP_OPENED_UNLINKED', f"تم فتح التطبيق من قبل مستخدم غير مرتبط (الاسم في تيليجرام: {first_name})")
                    )
            await db.commit()
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_gateway_log_action(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        action_type = data.get('action_type', 'TUTO_OPENED')
        first_name = data.get('first_name', '')
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            if telegram_id:
                async with db.execute("SELECT student_id, first_name FROM academy_students WHERE telegram_id = ?", (telegram_id,)) as cur:
                    row = await cur.fetchone()
                    if row:
                        await db.execute("INSERT INTO student_logs (student_id, action_type, description) VALUES (?, ?, ?)", 
                                         (row[0], action_type, f"فتح الطالب {row[1]} دليل معرف الطالب"))
                    else:
                        await db.execute("INSERT INTO student_logs (student_id, action_type, description) VALUES (?, ?, ?)", 
                                         (0, action_type, f"فتح مستخدم غير مرتبط دليل معرف الطالب (الاسم في تيليجرام: {first_name})"))
            else:
                await db.execute("INSERT INTO student_logs (student_id, action_type, description) VALUES (?, ?, ?)", 
                                 (0, action_type, "فتح مستخدم مجهول دليل معرف الطالب"))
            await db.commit()
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

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
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("INSERT INTO gateway_sos (email_tentative, message, telegram_id, dob_tentative, student_id_tentative) VALUES (?, ?, ?, ?, ?)", (email, message, telegram_id, dob, student_id))
            await db.commit()
        
        # Notify admins via Telegram
        try:
            from config import TELEGRAM_ADMIN_IDS
            admin_notif = (
                f"🆘 <b>Nouveau SOS Liaison !</b>\n\n"
                f"📧 <b>Email saisi :</b> {email or 'N/A'}\n"
                f"🪪 <b>Matricule :</b> {student_id or 'N/A'}\n"
                f"💬 <b>Message :</b>\n{message}\n\n"
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
                    f"<b>محتوى الرسالة:</b>\n<i>{message}</i>\n\n"
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
            async with db.execute("SELECT * FROM gateway_sos ORDER BY id DESC LIMIT 50") as cur:
                sos_list = [dict(row) for row in await cur.fetchall()]
        return web.json_response({'success': True, 'sos_list': sos_list})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

async def api_admin_sos_reply(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        sos_id = data.get('sos_id')
        reply_message = data.get('reply_message')
        telegram_id = data.get('telegram_id') # To send back if available, otherwise just mark closed
        
        if telegram_id:
            try:
                bot = request.app['bot']
                await bot.send_message(int(telegram_id), f"<b>🛠️ Réponse du Support Académie</b>\n\n{reply_message}", parse_mode="HTML")
            except Exception as e:
                print(f"Error sending SOS reply to student {telegram_id}: {e}")
                
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("UPDATE gateway_sos SET status = 'closed' WHERE id = ?", (sos_id,))
            await db.commit()
        return web.json_response({'success': True})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)})

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

async def api_admin_gateway_action(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    from database import log_student_action
    try:
        data = await request.json()
        action = data.get('action')
        student_id = data.get('student_id')
        if action == 'unlink':
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("UPDATE academy_students SET telegram_id = NULL WHERE student_id = ?", (student_id,))
                await db.commit()
            await log_student_action(student_id, 'MANUAL_UNLINK', 'L\'administrateur a dissocié le compte manuellement.')
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
        content = content.replace('<head>', '<head>' + script)
        
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
        valid_models = ['gemini-flash-lite-latest', 'gemini-1.5-flash', 'gemini-1.5-flash-latest',
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
                status_label = "âœ… ØªÙ… Ù‚Ø¨ÙˆÙ„ Ø³Ø¤Ø§Ù„Ùƒ Ø§Ù„Ù…Ù‚ترح ÙˆØ¥Ø¶Ø§ÙØªÙ‡ Ù„Ù„Ø£Ø³Ø¦Ù„ة Ø§Ù„Ø±Ø³Ù…ÙŠة Ø¨Ø§Ù„Ø£ÙƒØ§Ø¯ÙŠÙ…ÙŠة!"
                if rejection_reason and action == 'approved':
                    status_label += f"\nðŸ’¬ ØªØ¹Ù„ÙŠÙ‚ Ø§Ù„إدارة: {rejection_reason}"
                elif action != 'approved':
                    status_label = f"âŒ Ø¹Ø°Ø±Ø§Ù‹ØŒ ØªÙ… Ø±Ùض Ø³Ø¤Ø§Ù„Ùƒ Ø§Ù„Ù…Ù‚ترح.\nðŸ’¬ Ø§Ù„سبب: {rejection_reason}"
                    
                notif = (
                    f"ðŸ“£ <b>ØªØ­Ø¯ÙŠث Ø¨Ø®ØµÙˆص Ù…Ù‚ØªØ±Ø­Ùƒ Ù„Ø£Ø³Ø¦Ù„ة Ø§Ù„Ù…راجعة (Ø§Ù„Ø¨Ùˆت Ø§Ù„Ø¨Ø¯ÙŠÙ„)</b>\n"
                    f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                    f"Ø§Ù„Ø³Ø¤Ø§Ù„: <i>\"{proposal['question']}\"</i>\n\n"
                    f"{status_label}\n"
                    f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                    f"Ø´ÙƒØ±Ø§Ù‹ Ù„Ù…Ø³Ø§Ù‡Ù…ØªÙƒ ÙÙŠ Ø¨Ù†اء Ø§Ù„Ø£ÙƒØ§Ø¯ÙŠÙ…ÙŠة!"
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
            
        from config import DATABASE_PATH
        tickets = []
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            db_conn.row_factory = aiosqlite.Row
            async with db_conn.execute("SELECT id, report_type, notes, urgency, status, admin_reply, created_at, media_file_id, media_type FROM question_reports WHERE user_id = ? ORDER BY created_at DESC", (int(telegram_id),)) as cur:
                async for r in cur:
                    tickets.append({
                        "id": r["id"],
                        "reportType": r["report_type"],
                        "notes": r["notes"],
                        "urgency": r["urgency"],
                        "status": r["status"],
                        "adminReply": r["admin_reply"] or "",
                        "createdAt": r["created_at"],
                        "mediaFileId": r["media_file_id"] or "",
                        "mediaType": r["media_type"] or ""
                    })
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
                    "UPDATE question_reports SET admin_reply = ?, reviewed_at = datetime('now') WHERE id = ?",
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
                            'suggestion': 'ðŸ’¡ Ø§Ù‚ØªØ±Ø§Ø­Ùƒ',
                            'question_error': 'ðŸš© Ø¨Ù„اغ Ø§Ù„خطأ',
                            'tech': 'ðŸ”§ Ù…Ø´ÙƒÙ„ØªÙƒ Ø§Ù„ØªÙ‚Ù†ÙŠة',
                            'other': 'ðŸ“© Ø±Ø³Ø§Ù„تك'
                        }
                        label = type_labels.get(row["report_type"], "ðŸ“© Ø±Ø³Ø§Ù„تك")
                        
                        host = request.host
                        webapp_url = f"https://{host}/support.html?view=chat&ticket_id={ticket_id}"
                        
                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
                        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="ðŸ’¬ Ùتح Ø§Ù„Ù…حادثة ", web_app=WebAppInfo(url=webapp_url))]
                        ])
                        
                        await bot.send_message(
                            chat_id=row["user_id"],
                            text=f"ðŸ“¬ <b>رد Ø¬Ø¯ÙŠد Ù…Ù† Ø§Ù„إدارة Ø¹Ù„Ù‰ {label} :</b>\n\n<i>\"{message}\"</i>",
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
                            text=f"ðŸ’¬ <b>رد Ø¬Ø¯ÙŠد Ù…Ù† Ø§Ù„Ø·Ø§Ù„ب Ø¹Ù„Ù‰ Ø§Ù„ØªØ°Ùƒرة #{ticket_id} :</b>\n\n<i>\"{message}\"</i>",
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
                # Normalize aqida/aqeeda â€” DB may use either spelling
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
                    stop_words = {'le', 'la', 'de', 'en', 'et', 'ÙÙŠ', 'Ù…Ù†', 'Ø¹Ù„Ù‰', 'Ø§Ù†', 'Ø£Ù†', 'Ù‡Ùˆ', 'Ù‡ÙŠ', 'Ù‡Ù„'}
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
                # Normalize aqida/aqeeda â€” DB may use either spelling
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
            
            # 2. Obtenir tous les noeuds frÃ¨res (siblings) ordonnÃ©s
            if parent_id is None:
                query = "SELECT id FROM thematic_nodes WHERE program_id = ? AND level = ? AND parent_id IS NULL ORDER BY order_index, title"
                params = (program_id, level)
            else:
                query = "SELECT id FROM thematic_nodes WHERE program_id = ? AND level = ? AND parent_id = ? ORDER BY order_index, title"
                params = (program_id, level, parent_id)
                
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
            sibling_ids = [row[0] for row in rows]
            
            # 3. RÃ©organiser la liste
            if source_node_id in sibling_ids and target_node_id in sibling_ids:
                sibling_ids.remove(source_node_id)
                target_index = sibling_ids.index(target_node_id)
                # Inserer le source juste avant le target
                sibling_ids.insert(target_index, source_node_id)
                
                # 4. Mettre Ã  jour la base de donnÃ©es
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
            stop_words = {'le', 'la', 'de', 'en', 'et', 'ÙÙŠ', 'Ù…Ù†', 'Ø¹Ù„Ù‰', 'Ø§Ù†', 'Ø£Ù†', 'Ù‡Ùˆ', 'Ù‡ÙŠ', 'Ù‡Ù„'}
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
                "UPDATE question_reports SET status = ?, admin_reply = ?, reviewed_at = datetime('now') WHERE id = ?",
                (new_status, admin_reply, ticket_id)
            )
            await db_conn.commit()

            # Insert message into ticket_chat_messages
            if admin_reply:
                admin_name = "Ø§Ù„إدارة"
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
                            'suggestion': 'ðŸ’¡ Ø§Ù‚ØªØ±Ø§Ø­Ùƒ',
                            'question_error': 'ðŸš© Ø¨Ù„اغ Ø§Ù„خطأ',
                            'tech': 'ðŸ”§ Ù…Ø´ÙƒÙ„ØªÙƒ Ø§Ù„ØªÙ‚Ù†ÙŠة',
                            'other': 'ðŸ“© Ø±Ø³Ø§Ù„تك'
                        }
                        label = type_labels.get(row["report_type"] or "other", "ðŸ“© Ø±Ø³Ø§Ù„تك")
                        
                        # Force https for WebApp compatibility on Telegram
                        host = request.host
                        webapp_url = f"https://{host}/support.html?view=chat&ticket_id={ticket_id}"
                        
                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
                        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="ðŸ’¬ Ùتح Ø§Ù„Ù…حادثة ", web_app=WebAppInfo(url=webapp_url))]
                        ])
                        
                        await bot.send_message(
                            chat_id=row["user_id"],
                            text=f"ðŸ“¬ رد Ø§Ù„إدارة Ø¹Ù„Ù‰ {label}:\n\n<i>\"{admin_reply}\"</i>",
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
            admin_name = "Ù…Ø´Ø±Ù"
            db_conn.row_factory = aiosqlite.Row
            # 1. Try checking admins table first
            async with db_conn.execute("SELECT first_name, username FROM admins WHERE telegram_id = ?", (int(user_id),)) as cur:
                r = await cur.fetchone()
                if r and (r["first_name"] or r["username"]):
                    admin_name = r["first_name"] or r["username"]
            
            # 2. Try checking users table if still generic
            if admin_name == "Ù…Ø´Ø±Ù" or not admin_name:
                async with db_conn.execute("SELECT first_name, username FROM users WHERE telegram_id = ?", (int(user_id),)) as cur:
                    r = await cur.fetchone()
                    if r and (r["first_name"] or r["username"]):
                        admin_name = r["first_name"] or r["username"]
                        await db_conn.execute(
                            "UPDATE admins SET first_name = ?, username = ? WHERE telegram_id = ?",
                            (r["first_name"] or "", r["username"] or "", int(user_id))
                        )
            
            # 3. Try checking Telegram Bot API if still generic
            if admin_name == "Ù…Ø´Ø±Ù" or not admin_name:
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
            if admin_name == "Ù…Ø´Ø±Ù" and (int(user_id) in TELEGRAM_ADMIN_IDS or int(user_id) in [2045194295]):
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


# Admin API: Custom Views â€” List accessible views for this admin
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


# Admin API: Custom Views â€” Save (create or update)
async def save_custom_view(request):
    try:
        data = await request.json()
        user_id = data.get('userId')
        if not await check_admin(user_id):
            return web.json_response({"success": False, "error": "Access denied"}, status=403)

        role = await get_admin_role(user_id)
        view_id = data.get('id')  # None = create new
        name = data.get('name', 'Vue')
        icon = data.get('icon', 'ðŸ“Œ')
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


# Admin API: Custom Views â€” Delete
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
                return web.json_response({"success": False, "error": "Vue verrouillÃ©e"}, status=403)
            if view['created_by'] != int(user_id) and role != 'super_admin':
                return web.json_response({"success": False, "error": "Non autorisÃ©"}, status=403)
            await db_conn.execute("DELETE FROM admin_custom_views WHERE id = ?", (view_id,))
            await db_conn.commit()
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error deleting custom view: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)


# Admin API: Custom Views â€” Reorder
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


# â”€â”€â”€ Student Practice & Quiz API Endpoints â”€â”€â”€


async def api_validate_student(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        data = await request.json()
        student_id = data.get('student_id', '').strip()
        email = data.get('email', '').strip().lower()
        
        if not student_id or len(student_id) != 6:
            return web.json_response({'valid': False, 'message': ''})
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            if email:
                async with db.execute("SELECT telegram_id, first_name FROM academy_students WHERE student_id = ? AND LOWER(email) = ?", (student_id, email)) as cur:
                    row = await cur.fetchone()
                    if not row:
                        return web.json_response({'valid': False, 'message': 'البيانات غير متطابقة'})
                    
                    telegram_id, first_name = row
                    if telegram_id:
                        return web.json_response({'valid': True, 'message': f'أهلاً بك {first_name}! (مربوط مسبقاً)'})
                    return web.json_response({'valid': True, 'message': f'أهلاً بك {first_name} ✅'})
            else:
                async with db.execute("SELECT telegram_id FROM academy_students WHERE student_id = ?", (student_id,)) as cur:
                    row = await cur.fetchone()
                    if not row:
                        return web.json_response({'valid': False, 'message': 'الرقم غير مسجل'})
                    
                    telegram_id = row[0]
                    if telegram_id:
                        return web.json_response({'valid': True, 'message': 'رقم صحيح ✅ (مربوط مسبقاً)'})
                    return web.json_response({'valid': True, 'message': 'رقم صحيح ✅'})
                
    except Exception as e:
        return web.json_response({'valid': False, 'message': ''})

async def api_link_account(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    from database import log_student_action
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    try:
        data = await request.json()
        email = data.get('email', '').strip().lower()
        dob = data.get('dob', '').strip()
        student_id_input = data.get('student_id', '').strip()
        
        telegram_id = data.get('telegram_id')
        telegram_first_name = data.get('telegram_first_name', '')
        telegram_last_name = ''
        
        init_data = data.get('initData')
        if init_data:
            import urllib.parse
            import json
            parsed = urllib.parse.parse_qs(init_data)
            user_data = json.loads(parsed['user'][0])
            telegram_id = user_data['id']
            telegram_first_name = user_data.get('first_name', '')
            telegram_last_name = user_data.get('last_name', '')
            
        if not telegram_id:
            return web.json_response({'success': False, 'error': 'خطأ في المصادقة مع تيليجرام (Erreur Telegram)'})
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            errors = {}
            telegram_name = f"{telegram_first_name} {telegram_last_name}".strip()
            
            # Upsert user info
            await db.execute("""
                INSERT INTO users (telegram_id, first_name, last_name) 
                VALUES (?, ?, ?) 
                ON CONFLICT(telegram_id) DO UPDATE SET 
                first_name=excluded.first_name, last_name=excluded.last_name
            """, (telegram_id, telegram_first_name, telegram_last_name))
            
            # Check Email
            async with db.execute("SELECT student_id, dob, first_name FROM academy_students WHERE LOWER(TRIM(email)) = LOWER(TRIM(?))", (email,)) as cur1:
                row1 = await cur1.fetchone()
                if not row1:
                    errors['email'] = 'البريد الإلكتروني غير مسجل.'
                    await db.execute("INSERT INTO student_logs (student_id, telegram_id, telegram_name, action_type, description) VALUES (?, ?, ?, ?, ?)", (0, telegram_id, telegram_name, 'LINK_FAILED', f"محاولة ربط ببريد إلكتروني غير مسجل: {email}"))
                else:
                    db_student_id = row1[0]
                    db_dob = row1[1]
                    real_first_name = row1[2]

                    # Check DOB
                    if db_dob != dob:
                        errors['dob'] = 'تاريخ الميلاد غير صحيح.'
                        await db.execute("INSERT INTO student_logs (student_id, telegram_id, telegram_name, action_type, description) VALUES (?, ?, ?, ?, ?)", (db_student_id, telegram_id, telegram_name, 'LINK_FAILED', f"محاولة ربط فاشلة: تاريخ الميلاد غير صحيح ({dob})"))
                        
                    # Check Student ID
                    if str(db_student_id) != str(student_id_input):
                        errors['student_id'] = 'رقم الطالب غير صحيح.'
                        await db.execute("INSERT INTO student_logs (student_id, telegram_id, telegram_name, action_type, description) VALUES (?, ?, ?, ?, ?)", (db_student_id, telegram_id, telegram_name, 'LINK_FAILED', f"محاولة ربط فاشلة: الرقم الدراسي غير صحيح ({student_id_input})"))
            
            if errors:
                await db.commit()
                return web.json_response({'success': False, 'errors': errors})
                
            # All Good: fetch full data
            async with db.execute("SELECT telegram_id, gender, year FROM academy_students WHERE student_id = ?", (db_student_id,)) as cur2:
                row2 = await cur2.fetchone()
                existing_tg = row2[0]
                gender = str(row2[1]).lower() if row2[1] else 'homme'
                year = str(row2[2]) if row2[2] else '1'
                
                if existing_tg:
                    if existing_tg != telegram_id:
                        await db.execute("INSERT INTO student_logs (student_id, telegram_id, telegram_name, action_type, description) VALUES (?, ?, ?, ?, ?)", (db_student_id, telegram_id, telegram_name, 'LINK_FAILED', f"محاولة ربط بحساب تيليجرام آخر"))
                        await db.commit()
                        return web.json_response({'success': False, 'error': 'هذا الحساب مرتبط بالفعل بحساب تيليجرام آخر (Compte déjà lié à un autre Telegram).'})
                
                # Check setting for forced telegram name
                async with db.execute("SELECT value FROM settings WHERE key = 'force_telegram_name'") as cur_set:
                    force_row = await cur_set.fetchone()
                    force_name = True if force_row and force_row[0] == 'true' else False
                
                if force_name and telegram_first_name and real_first_name.lower() not in telegram_first_name.lower():
                    await db.execute("INSERT INTO student_logs (student_id, telegram_id, telegram_name, action_type, description) VALUES (?, ?, ?, ?, ?)", (db_student_id, telegram_id, telegram_name, 'LINK_FAILED', f'محاولة ربط فاشلة: اسم تيليجرام غير مطابق: "{telegram_first_name}" (المتوقع: "{real_first_name}")'))
                    await db.commit()
                    return web.json_response({
                        'success': False, 
                        'error': f'عذراً، اسمك في تيليجرام "{telegram_first_name}" لا يطابق اسمك المسجل "{real_first_name}". يرجى تعديله في إعدادات تيليجرام.'
                    }, status=403)
                        
                # Link account
                if not existing_tg:
                    await db.execute("UPDATE academy_students SET telegram_id = ? WHERE student_id = ?", (telegram_id, db_student_id))
                    await db.execute("INSERT INTO student_logs (student_id, telegram_id, telegram_name, action_type, description) VALUES (?, ?, ?, ?, ?)", (db_student_id, telegram_id, telegram_name, 'ACCOUNT_LINKED', f"تم ربط حساب تيليجرام بنجاح"))
                    await db.commit()
                    
                    # SEND WELCOME MESSAGE VIA TELEGRAM
                    display_name = telegram_first_name if telegram_first_name else real_first_name
                    welcome_msg = (
                        f"أهلاً بك {display_name} في أكاديمية الباجي.\\n\\n"
                        f"تم التحقق من هويتك بنجاح (رقم الطالب: {db_student_id}).\\n"
                        f"يمكنك الآن الوصول إلى جميع قنوات الأكاديمية والمجموعات الدراسية مباشرة عبر المجلد الرسمي الذي قمت بإضافته.\\n\\n"
                        f"هل كانت عملية الدخول سهلة بالنسبة لك؟"
                    )
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="👍 نعم، كانت سهلة", callback_data="feedback_easy"),
                            InlineKeyboardButton(text="👎 واجهت صعوبة", callback_data="feedback_hard")
                        ]
                    ])
                    try:
                        await bot.send_message(telegram_id, welcome_msg, reply_markup=kb)
                    except Exception as e:
                        pass
                    
                return web.json_response({'success': True, 'first_name': real_first_name})
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
            "preferredName": user_info.get("preferred_name") or user_info.get("first_name") or "Ø·Ø§Ù„ب" if user_info else "Ø·Ø§Ù„ب",
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


async def api_support_rag_check(request):
    try:
        data = await request.json()
        theme = data.get('theme', '')
        subtheme = data.get('subtheme', '')
        msg = data.get('message', '').lower()
        
        # Load FAQ DB
        import json
        import os
        faq_path = os.path.join(os.path.dirname(__file__), 'faq_db.json')
        if os.path.exists(faq_path):
            with open(faq_path, 'r', encoding='utf-8') as f:
                faq_data = json.load(f)
                
            if theme in faq_data:
                # Basic exact/keyword match for MVP
                for question, answer in faq_data[theme].items():
                    # Simple heuristic: if subtheme is in question or any word overlaps heavily
                    if question in subtheme or subtheme in question:
                        return web.json_response({'found': True, 'answer': answer})
                    
                    # Or if words from message overlap with question
                    words = msg.split()
                    if len(words) > 0 and sum(1 for w in words if w in question.lower()) >= 2:
                        return web.json_response({'found': True, 'answer': answer})
        
        return web.json_response({'found': False})
    except Exception as e:
        logger.error(f"Error in rag_check: {e}")
        return web.json_response({'found': False})

async def api_support(request):
    try:
        data = await request.json()
        theme = data.get('theme')
        subtheme = data.get('subtheme')
        msg = data.get('message')
        telegram_id = data.get('telegram_id')
        username = data.get('username', 'غير معروف')
        first_name = data.get('first_name', 'غير معروف')

        import requests
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_SUPPORT_GROUP_ID
        
        text = f'🆘 <b>طلب مساعدة / استفسار جديد</b>\n\n'
        text += f'👤 <b>الطالب:</b> {first_name} (@{username})\n'
        text += f'🆔 <b>Telegram ID:</b> {telegram_id}\n'
        text += f'📂 <b>القسم:</b> {theme}\n'
        text += f'🔖 <b>التفاصيل:</b> {subtheme}\n\n'
        text += f'📝 <b>الرسالة:</b>\n{msg}'
        
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        payload = {
            'chat_id': TELEGRAM_SUPPORT_GROUP_ID,
            'text': text,
            'parse_mode': 'HTML'
        }
        requests.post(url, json=payload)
        
        from aiohttp import web
        return web.json_response({'success': True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        from aiohttp import web
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def start_web_server(bot: Bot):
    app = web.Application(middlewares=[cors_middleware])
    app['bot'] = bot
    
    app.router.add_get('/', handle_reader)
    app.router.add_get('/index.html', handle_reader)
    app.router.add_get('/link.html', handle_link)
    app.router.add_get('/interactive.html', handle_interactive)
    app.router.add_get('/admin_mindmap.html', handle_admin_mindmap)
    app.router.add_get('/course_slides.html', handle_course_slides)
    app.router.add_get('/course_slides.css', handle_course_slides_css)
    app.router.add_get('/course_slides.js', handle_course_slides_js)
    
    app.router.add_get('/editor', handle_editor)
    app.router.add_get('/editor.html', handle_editor)
    app.router.add_get('/admin', handle_admin)
    app.router.add_get('/admin.html', handle_admin)
    app.router.add_get('/admin-bot', handle_admin_bot)
    app.router.add_get('/admin-bot.html', handle_admin_bot)
    app.router.add_get('/admin-support', handle_admin_support)
    app.router.add_get('/admin-support.html', handle_admin_support)
    app.router.add_get('/admin.css', handle_admin_css)
    app.router.add_get('/admin.js', handle_admin_js)
    app.router.add_get('/admin-late.js', handle_admin_late_js)
    app.router.add_get('/logo.png', handle_logo_png)
    app.router.add_get('/tuto.jpg', handle_tuto_jpg)
    app.router.add_get('/dossiertelegram.jpg', handle_dossiertelegram_jpg)
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
    app.router.add_post('/api/support/rag_check', api_support_rag_check)
    app.router.add_post('/api/support', api_support)
    app.router.add_get('/ask.html', handle_support)
    app.router.add_get('/api/tickets/student', get_student_tickets)
    app.router.add_post('/api/tickets/student', get_student_tickets)
    app.router.add_get('/api/tickets/{ticket_id}/messages', get_ticket_messages_api)
    app.router.add_post('/api/tickets/{ticket_id}/reply', reply_ticket_message_api)
    app.router.add_get('/api/triage/match', handle_triage_match)
    app.router.add_post('/api/triage/match', handle_triage_match)
    app.router.add_post('/report-chapter', report_chapter)
    # Student Practice & Quiz API routes
    app.router.add_post('/api/link_account', api_link_account)
    app.router.add_post('/api/validate_student', api_validate_student)
    app.router.add_get('/admin-gateway.html', handle_admin_gateway)
    app.router.add_get('/api/admin/gateway/stats', api_admin_gateway_stats)
    app.router.add_get('/api/admin/gateway/students', api_admin_gateway_students)
    app.router.add_get('/api/admin/gateway/logs', api_admin_gateway_logs)
    app.router.add_get('/api/admin/gateway/logs/all', api_admin_gateway_logs_all)
    app.router.add_get('/api/admin/gateway/check_member', api_admin_gateway_check_member)
    app.router.add_post('/api/admin/gateway/add_student', api_admin_gateway_add_student)
    app.router.add_post('/api/admin/gateway/import_students', api_admin_gateway_import_students)
    app.router.add_post('/api/admin/gateway/settings', api_admin_gateway_settings)
    app.router.add_get('/api/admin/gateway/settings', api_admin_gateway_settings_get)
    app.router.add_get('/api/admin/gateway/chat', api_admin_gateway_chat)
    app.router.add_post('/api/admin/gateway/action', api_admin_gateway_action)
    app.router.add_post('/api/gateway/sos', api_gateway_sos)
    app.router.add_post('/api/gateway/log_open', api_gateway_log_open)
    app.router.add_post('/api/gateway/log_action', api_gateway_log_action)
    app.router.add_get('/api/admin/links', api_admin_links_get)
    app.router.add_get('/api/admin/sos', api_admin_sos_list)
    app.router.add_post('/api/admin/sos/reply', api_admin_sos_reply)
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
                        if current_first_name and real_first_name.lower() not in current_first_name.lower():
                            await log_student_action(student_id, 'NAME_VIOLATION_DETECTED', f'Prénom actuel: {current_first_name}')
                            try:
                                await bot.send_message(telegram_id, f'⚠️ Attention ! Ton prénom Telegram actuel est "{current_first_name}". Tu dois impérativement utiliser ton vrai prénom "{real_first_name}". Merci de le modifier dans tes paramètres Telegram.')
                            except Exception:
                                pass
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
    await db.init_db()
    logger.info("Database initialized.")
    try:
        await db.set_setting("current_instance_id", INSTANCE_ID)
        logger.info(f"Registered instance ID in database settings: {INSTANCE_ID}")
    except Exception as e:
        logger.error(f"Failed to register instance ID in database: {e}")
    
    # 1. Set Chat Menu Button (Persistent Bottom-Left Web App Button!)
    try:
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        base_url = get_webapp_base_url()
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

async def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN is missing! Exiting...")
        return

    # Initialize bot and dispatcher
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Start Web Server FIRST and wait for it to bind to port
    # This ensures Railway health checks pass before Telegram polling starts
    async def _web_server_with_logging():
        try:
            await start_web_server(bot)
        except Exception as e:
            logger.critical(f"[Web Server] FATAL ERROR: {e}", exc_info=True)
    
    web_task = asyncio.ensure_future(_web_server_with_logging())
    await asyncio.sleep(3)  # Give web server 3 seconds to bind to port
    
    dp = Dispatcher(storage=MemoryStorage())

    # Register middlewares
    dp.message.outer_middleware(AccessCheckMiddleware())
    dp.callback_query.outer_middleware(AccessCheckMiddleware())

    # Include handlers
    dp.include_router(auth_router)
    
    
    
    
    
    
    

    # Register startup hook
    dp.startup.register(on_startup)

    # â”€â”€â”€ RAILWAY ZERO-DOWNTIME CONFLICT RESOLUTION â”€â”€â”€
    logger.info(f"DÃ©marrage de l'instance courante avec ID: {INSTANCE_ID}")
    
    async def watch_for_new_instance():
        while True:
            await asyncio.sleep(5)
            try:
                from config import DATABASE_PATH
                if not os.path.exists(DATABASE_PATH):
                    continue
                async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                    async with db_conn.execute("SELECT value FROM settings WHERE key = 'current_instance_id'") as cur:
                        row = await cur.fetchone()
                        if row and row[0] and row[0] != INSTANCE_ID:
                            logger.warning(f"ðŸš¨ NOUVELLE INSTANCE DÃ‰TECTÃ‰E ({row[0]}). ArrÃªt du polling pour Ã©viter les conflits Telegram !")
                            await dp.stop_polling()
                            break
            except Exception:
                pass
        
    asyncio.create_task(watch_for_new_instance())
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    logger.info("Starting Telegram Backup Bot polling...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        
    # Keep web server alive even if polling stops (Railway conflict)
    while True:
        await asyncio.sleep(3600)




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

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")

