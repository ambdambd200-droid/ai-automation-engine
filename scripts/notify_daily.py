import os
import sys
import json

sys.path.insert(0, '.')

from telegram_notifier import notify

status = '✅ SUCCESS' if os.environ.get('RUN_STATUS') == '0' else '❌ FAILED'
notify(f'{status} Daily Freelance Run\nGitHub Actions: {os.environ.get("GITHUB_RUN_NUMBER")}\nCommit: {os.environ.get("GITHUB_SHA", "")[:8]}')