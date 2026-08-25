import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import sys

from telegram_notifier import notify

notify('🤖 Telegram Controller started on GitHub Actions\nRun ID: ' + os.environ.get('GITHUB_RUN_ID', 'unknown'))