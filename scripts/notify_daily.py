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
import json

from telegram_notifier import notify

status = '✅ SUCCESS' if os.environ.get('RUN_STATUS') == '0' else '❌ FAILED'
notify(f'{status} Daily Freelance Run\nGitHub Actions: {os.environ.get("GITHUB_RUN_NUMBER")}\nCommit: {os.environ.get("GITHUB_SHA", "")[:8]}')