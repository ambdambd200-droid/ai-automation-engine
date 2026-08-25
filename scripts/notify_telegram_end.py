import os
import sys

sys.path.insert(0, '.')

from telegram_notifier import notify

status = '✅ Completed' if os.environ.get('JOB_STATUS') == 'success' else '⚠️ Timed out (restarting)'
notify(f'🤖 Telegram Controller: {status}\nRun: {os.environ.get("GITHUB_RUN_ID", "unknown")}\nNext run in ~5 hours')