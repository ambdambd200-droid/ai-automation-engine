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

notify('🤖 Telegram Controller started on GitHub Actions\nRun ID: ' + os.environ.get('GITHUB_RUN_ID', 'unknown'))