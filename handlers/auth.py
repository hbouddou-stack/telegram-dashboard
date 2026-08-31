import os
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
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
