import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from telegram_notifier import notify

notify(f'📅 Weekly Review - {datetime.now().strftime("%Y-%m-%d")}\n\nReminder: Create portfolio pieces manually:\n- Nafezly portfolio\n- Mostaql portfolio  \n- Nafezly service page\n\nSee create_portfolio.py for workflow.')