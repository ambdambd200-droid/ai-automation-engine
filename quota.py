"""
quota.py — Daily quota tracker for freelance actions.

Single source of truth for "how many of X can I do today". Wraps any
send action with a check + increment. Reset happens automatically at
midnight (local time).

Why this exists:
- hunt.py, send_applications.py, post_forum_replies.py all had their own
  counter logic in hunt_state.json
- This module centralizes the rules so any script can ask "can I do X?"
  in one line

Usage:
    from quota import can_send, record_sent, get_remaining, reset_all

    if not can_send("mostaql_bids"):
        print("Daily limit reached for mostaql_bids")
        return
    send_bid(...)
    record_sent("mostaql_bids")
    print(f"Remaining today: {get_remaining('mostaql_bids')}")

CLI:
    python quota.py --status        # show all quotas + remaining
    python quota.py --reset         # reset today's counters (testing only)
    python quota.py --set mostaql_bids 5   # override a quota (testing only)
"""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(os.environ.get("MONEY_HOME", r"C:\Users\A\Desktop\Money"))
STATE_FILE = WORKSPACE / "hunt_state.json"

# Default daily quotas. Override per-environment with env vars like
# QUOTA_MOSTAQL_BIDS=5
DEFAULT_QUOTAS = {
    "replies": 10,           # email_reply
    "followups": 5,          # email_followup
    "mostaql_bids": 3,       # mostaql_bid
    "nafezly_bids": 3,       # nafezly_bid
    "forum_replies": 3,      # forum_reply (n8n Community)
    "upwork_applies": 5,     # upwork proposals
    "linkedin_connects": 20, # connection requests
    "emails_sent": 15,       # catch-all for any other email
}


def _load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"last_run": None, "sent_emails": [], "sent_bids": [],
            "sent_replies": [], "sent_followups": [], "replied_ids": [],
            "daily_counters": {}, "completed_phases": []}


def _save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _today_key():
    return date.today().isoformat()


def _get_counters(state):
    dc = state.setdefault("daily_counters", {})
    if dc.get("date") != _today_key():
        dc = {"date": _today_key(), "counts": {}}
        state["daily_counters"] = dc
    return dc.setdefault("counts", {})


def _quota_limit(action):
    env_key = f"QUOTA_{action.upper()}"
    if env_key in os.environ:
        try:
            return int(os.environ[env_key])
        except ValueError:
            pass
    return DEFAULT_QUOTAS.get(action, 999)


def can_send(action):
    """Return True if there's still quota for this action today."""
    state = _load_state()
    counters = _get_counters(state)
    used = counters.get(action, 0)
    return used < _quota_limit(action)


def record_sent(action, marker=""):
    """Increment the counter. Returns the new count."""
    state = _load_state()
    counters = _get_counters(state)
    counters[action] = counters.get(action, 0) + 1
    if marker:
        # Log to the appropriate sent_* list
        if action in ("replies", "followups", "emails_sent"):
            key = {
                "replies": "sent_replies",
                "followups": "sent_followups",
                "emails_sent": "sent_emails",
            }[action]
            state.setdefault(key, []).append(marker)
        elif action in ("mostaql_bids", "nafezly_bids", "forum_replies", "upwork_applies"):
            state.setdefault("sent_bids", []).append(f"{action}:{marker[:50]}")
    _save_state(state)
    return counters[action]


def get_remaining(action):
    state = _load_state()
    counters = _get_counters(state)
    used = counters.get(action, 0)
    return max(0, _quota_limit(action) - used)


def get_all_remaining():
    return {a: get_remaining(a) for a in DEFAULT_QUOTAS}


def reset_all():
    """Testing only — clears today's counters."""
    state = _load_state()
    state["daily_counters"] = {"date": _today_key(), "counts": {}}
    _save_state(state)


def show_status():
    state = _load_state()
    dc = state.get("daily_counters", {})
    print(f"\n  Daily quotas — {dc.get('date', '(no run today)')}")
    print(f"  {'Action':<20} {'Used':>6} {'Limit':>6} {'Remaining':>10}")
    print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*10}")
    counters = dc.get("counts", {}) if dc.get("date") == _today_key() else {}
    for action, limit in DEFAULT_QUOTAS.items():
        used = counters.get(action, 0)
        remaining = max(0, limit - used)
        marker = "FULL" if remaining == 0 else ""
        print(f"  {action:<20} {used:>6} {limit:>6} {remaining:>10} {marker}")
    print()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="quota.py — daily quota tracker")
    p.add_argument("--status", action="store_true", help="Show all quotas")
    p.add_argument("--reset", action="store_true", help="[testing] Reset today's counters")
    p.add_argument("--set", nargs=2, metavar=("ACTION", "LIMIT"),
                   help="[testing] Override a quota limit (e.g. --set mostaql_bids 5)")
    p.add_argument("--check", help="Check if action can be sent (prints True/False)")
    args = p.parse_args()

    if args.status:
        show_status()
    elif args.reset:
        reset_all()
        print("  Reset complete.")
    elif args.set:
        action, limit = args.set
        os.environ[f"QUOTA_{action.upper()}"] = limit
        print(f"  Set {action} = {limit} (env var only, not persistent)")
        show_status()
    elif args.check:
        print("  True" if can_send(args.check) else "  False")
    else:
        show_status()
