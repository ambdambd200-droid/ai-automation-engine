import sys
import os

# Add both the script's parent directory (repo root) and current working directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
cwd = os.getcwd()

for path in [repo_root, cwd]:
    if path not in sys.path:
        sys.path.insert(0, path)

import os
import sys

from telegram_notifier import notify

status = '✅ Completed' if os.environ.get('JOB_STATUS') == 'success' else '⚠️ Timed out (restarting)'
notify(f'🤖 Telegram Controller: {status}\nRun: {os.environ.get("GITHUB_RUN_ID", "unknown")}\nNext run in ~5 hours')