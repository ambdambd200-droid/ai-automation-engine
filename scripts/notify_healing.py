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

from healing_orchestrator import get_orchestrator
from telegram_notifier import notify

platform = os.environ.get('HEAL_PLATFORM', 'all')
platforms = ['mostaql', 'nafezly', 'n8n'] if platform == 'all' else [platform]

for p in platforms:
    try:
        orch = get_orchestrator(p)
        stats = orch.get_stats()
        msg = f'🔧 Healing Check: {p}\nCalls: {stats.get("total_calls",0)}\nHealed: {stats.get("healing_successes",0)}/{stats.get("healing_attempts",0)}'
        notify(msg)
    except Exception as e:
        from telegram_notifier import notify_error
        notify_error(f'Healing Check Failed: {p}\nError: {e}')