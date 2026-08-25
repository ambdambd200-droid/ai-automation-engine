import os
import sys

sys.path.insert(0, '.')

from telegram_notifier import notify

notify('🤖 Telegram Controller started on GitHub Actions\nRun ID: ' + os.environ.get('GITHUB_RUN_ID', 'unknown'))