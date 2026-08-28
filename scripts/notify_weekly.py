import sys
import os

# Add both the script's parent directory (repo root) and current working directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
cwd = os.getcwd()

for path in [repo_root, cwd]:
    if path not in sys.path:
        sys.path.insert(0, path)

from datetime import datetime
from telegram_notifier import notify

notify(f'📅 Weekly Review - {datetime.now().strftime("%Y-%m-%d")}\n\nReminder: Create portfolio pieces manually:\n- Nafezly portfolio\n- Mostaql portfolio  \n- Nafezly service page\n\nSee create_portfolio.py for workflow.')