import os
import aiohttp
from aiohttp import web
import sys

DASHBOARD_DIR = os.path.join(os.path.dirname(os.path.abspath('telegram-bot-backup/main.py')), '..', 'dashboard')
editor_path = os.path.join(DASHBOARD_DIR, 'editor.html')

print(f"DASHBOARD_DIR: {DASHBOARD_DIR}")
print(f"editor.html path: {editor_path}")
print(f"Exists: {os.path.exists(editor_path)}")
