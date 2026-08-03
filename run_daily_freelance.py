"""
run_daily_freelance.py — Master daily script.

Daily routine (every day):
  1. Search Mostaql for new projects → bid on up to 3
  2. Search Nafezly for new projects → bid on up to 3
  3. Find recent n8n Community posts → reply to 1-2 (technical or showcase)

Weekly routine (Sunday only, controlled by --weekly flag):
  1. Create a portfolio piece on Nafezly (requires user-supplied image)
  2. Create a portfolio piece on Mostaql (requires user-supplied image)
  3. Create a Nafezly service page

This script is the BRAIN (decides) + HANDS (executes). The user supervises
and approves via the engine's /review endpoint.

Usage:
  python run_daily_freelance.py                   # daily run
  python run_daily_freelance.py --dry-run         # generate but don't post
  python run_daily_freelance.py --only mostaql    # only one platform
  python run_daily_freelance.py --weekly          # include weekly portfolio
  python run_daily_freelance.py --status          # show last run summary
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("[run_daily_freelance] requests not installed", file=sys.stderr)
    sys.exit(1)

WORKSPACE = Path(__file__).parent.resolve()
ENGINE_URL = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")
PROFILE_FILE = WORKSPACE / "salim_profile.json"

STATE_FILE = WORKSPACE / "daily_freelance_state.json"

DAILY_QUOTAS = {
    "mostaql_bids": 3,
    "nafezly_bids": 3,
    "n8n_replies": 2,
}

DAILY_KEYWORDS = {
    "mostaql": ["n8n", "أتمتة", "بوت تلقرام", "بوت واتساب", "API", "Python"],
    "nafezly": ["n8n", "أتمتة", "بوت", "API", "Python", "Make.com", "Zapier"],
}


def load_profile() -> dict:
    if PROFILE_FILE.exists():
        return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    return {}


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"last_run": None, "history": [], "today": {}}


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def engine_health() -> bool:
    try:
        r = requests.get(f"{ENGINE_URL}/health", timeout=10)
        return r.ok
    except Exception:
        return False


def engine_bid_generate(platform: str, project: dict) -> dict | None:
    """Call engine /api/bid/generate."""
    try:
        r = requests.post(
            f"{ENGINE_URL}/api/bid/generate",
            json={
                "platform": platform,
                "project_title": project.get("title", ""),
                "project_description": project.get("description", ""),
                "budget": project.get("budget", ""),
                "client_name": project.get("client_name", ""),
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"  engine bid gen failed: {e}")
        return None


def engine_n8n_reply(thread_title: str, thread_context: str,
                     thread_url: str = "", thread_author: str = "") -> dict | None:
    """Call engine /api/n8n/reply."""
    try:
        r = requests.post(
            f"{ENGINE_URL}/api/n8n/reply",
            json={
                "thread_title": thread_title,
                "thread_context": thread_context,
                "thread_url": thread_url,
                "thread_author": thread_author,
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"  engine n8n reply gen failed: {e}")
        return None


def engine_hunt_event(kind: str, payload: dict) -> bool:
    """Notify engine of a hunt event."""
    try:
        r = requests.post(
            f"{ENGINE_URL}/api/hunt_event",
            json={"kind": kind, "payload": payload,
                  "ts": datetime.now().isoformat()},
            timeout=10,
        )
        return r.ok
    except Exception:
        return False


def check_quota(state: dict, kind: str) -> int:
    """How many of `kind` are still allowed today."""
    today = state.get("today", {})
    if today.get("date") != today_key():
        today = {"date": today_key()}
        state["today"] = today
    used = today.get(kind, 0)
    limit = DAILY_QUOTAS.get(kind, 0)
    return max(0, limit - used)


def increment_quota(state: dict, kind: str):
    today = state.get("today", {})
    if today.get("date") != today_key():
        today = {"date": today_key()}
        state["today"] = today
    today[kind] = today.get(kind, 0) + 1
    state["today"] = today


def run_mostaql(state: dict, dry_run: bool) -> list:
    """Mostaql: search + bid."""
    from post_arabic_bids import run_platform
    remaining = check_quota(state, "mostaql_bids")
    if remaining <= 0:
        log(f"[Mostaql] Daily quota exhausted (3/3)")
        return []
    log(f"\n{'='*60}\n  MOSTAQL — daily run (quota: {remaining}/3)\n{'='*60}")
    keywords = DAILY_KEYWORDS["mostaql"][:3]  # rotate top 3
    result = run_platform("mostaql", keywords, top_n=remaining, dry_run=dry_run)
    n_posted = sum(1 for r in result["results"] if r.get("ok"))
    for _ in range(n_posted):
        increment_quota(state, "mostaql_bids")
    engine_hunt_event("daily_mostaql_run", {"posted": n_posted, "dry_run": dry_run})
    return result["results"]


def run_nafezly(state: dict, dry_run: bool) -> list:
    """Nafezly: search + bid."""
    from post_arabic_bids import run_platform
    remaining = check_quota(state, "nafezly_bids")
    if remaining <= 0:
        log(f"[Nafezly] Daily quota exhausted (3/3)")
        return []
    log(f"\n{'='*60}\n  NAFEZLY — daily run (quota: {remaining}/3)\n{'='*60}")
    keywords = DAILY_KEYWORDS["nafezly"][:3]
    result = run_platform("nafezly", keywords, top_n=remaining, dry_run=dry_run)
    n_posted = sum(1 for r in result["results"] if r.get("ok"))
    for _ in range(n_posted):
        increment_quota(state, "nafezly_bids")
    engine_hunt_event("daily_nafezly_run", {"posted": n_posted, "dry_run": dry_run})
    return result["results"]


def run_n8n_community(state: dict, dry_run: bool) -> list:
    """n8n Community: post replies."""
    remaining = check_quota(state, "n8n_replies")
    if remaining <= 0:
        log(f"[n8n Community] Daily quota exhausted (2/2)")
        return []
    log(f"\n{'='*60}\n  N8N COMMUNITY — daily run (quota: {remaining}/2)\n{'='*60}")
    # n8n replies use fixed drafts for now (less risk than auto-gen)
    from post_n8n_replies import main as post_n8n_main
    # For dry-run, we just preview; for real, we run post_n8n_replies
    if dry_run:
        log("  DRY-RUN: would post replies (see post_n8n_replies.py --dry-run)")
        return [{"ok": "dry-run"}]
    # Run the actual script
    try:
        # post_n8n_replies has its own __main__; we'll call its internal function
        # For simplicity, just call the script as a subprocess
        import subprocess
        proc = subprocess.run(
            [sys.executable, str(WORKSPACE / "post_n8n_replies.py"),
             "--one", "1"],  # post only 1 per day
            capture_output=True, text=True, timeout=180,
        )
        log(f"  post_n8n_replies.py exit: {proc.returncode}")
        if proc.stdout:
            log(f"  stdout: {proc.stdout[-500:]}")
        if proc.stderr:
            log(f"  stderr: {proc.stderr[-500:]}")
        ok = proc.returncode == 0
        increment_quota(state, "n8n_replies")
        engine_hunt_event("daily_n8n_run", {"ok": ok, "dry_run": False})
        return [{"ok": ok}]
    except Exception as e:
        log(f"  n8n reply run error: {e}")
        return [{"ok": False, "error": str(e)}]


def run_weekly_portfolio(state: dict, dry_run: bool) -> dict:
    """Weekly: create portfolio pieces (mostly manual, requires images)."""
    log(f"\n{'='*60}\n  WEEKLY PORTFOLIO/SERVICE CREATION\n{'='*60}")
    log("  This requires USER input (cover image, screenshots).")
    log("  Skipping auto-execution. Open these URLs:")
    log("    https://nafezly.com/portfolio/create")
    log("    https://nafezly.com/service/create")
    log("    https://mostaql.com/portfolio/create")
    log("  See: create_portfolio.py --weekly for the actual workflow.")
    return {"status": "skipped", "reason": "requires manual image upload"}


def main():
    ap = argparse.ArgumentParser(description="Daily freelance routine")
    ap.add_argument("--dry-run", action="store_true",
                    help="Generate bids but don't actually post")
    ap.add_argument("--only", choices=["mostaql", "nafezly", "n8n"],
                    help="Run only one platform")
    ap.add_argument("--weekly", action="store_true",
                    help="Include weekly portfolio/service creation")
    ap.add_argument("--status", action="store_true",
                    help="Show last run summary and exit")
    args = ap.parse_args()

    log(f"Daily Freelance Runner — {today_key()}")
    log(f"Engine: {ENGINE_URL}")

    state = load_state()

    if args.status:
        log("\n=== Last Run State ===")
        log(json.dumps(state, indent=2, ensure_ascii=False))
        return

    if not engine_health():
        log("WARNING: Engine not reachable. AI generation will fail.")
        log("Continuing anyway for dry-run or local-only operations.")

    profile = load_profile()
    if not profile:
        log("WARNING: salim_profile.json not found. AI will use generic identity.")

    summary = {"date": today_key(), "dry_run": args.dry_run,
               "mostaql": [], "nafezly": [], "n8n": [], "weekly": None}

    try:
        if args.only in (None, "mostaql"):
            summary["mostaql"] = run_mostaql(state, args.dry_run)
        if args.only in (None, "nafezly"):
            summary["nafezly"] = run_nafezly(state, args.dry_run)
        if args.only in (None, "n8n"):
            summary["n8n"] = run_n8n_community(state, args.dry_run)
        if args.weekly:
            summary["weekly"] = run_weekly_portfolio(state, args.dry_run)
    except KeyboardInterrupt:
        log("\nInterrupted by user")
    finally:
        # Append to history
        state.setdefault("history", []).append(summary)
        state["last_run"] = today_key()
        save_state(state)

    log("\n" + "=" * 60)
    log("  Daily Run Summary")
    mostaql_ok = sum(1 for r in summary["mostaql"] if r.get("ok"))
    nafezly_ok = sum(1 for r in summary["nafezly"] if r.get("ok"))
    n8n_ok = sum(1 for r in summary["n8n"] if r.get("ok"))
    log(f"  Mostaql bids: {mostaql_ok}")
    log(f"  Nafezly bids: {nafezly_ok}")
    log(f"  n8n replies:  {n8n_ok}")

    # Send Telegram notification (free, no limits)
    try:
        sys.path.insert(0, str(WORKSPACE))
        from telegram_notifier import notify_daily_digest, notify_error
        digest = {
            "date": today_key(),
            "mostaql_bids": mostaql_ok,
            "nafezly_bids": nafezly_ok,
            "n8n_replies": n8n_ok,
            "errors": [r.get("error", "") for r in (summary["mostaql"] + summary["nafezly"] + summary["n8n"]) if not r.get("ok") and r.get("error")][:5],
            "next_steps": [
                "Open /review for human approval before any post" if not args.dry_run else "Dry-run mode — nothing was posted",
            ],
        }
        if not args.dry_run and (mostaql_ok + nafezly_ok + n8n_ok) > 0:
            notify_daily_digest(digest)
            log("  Telegram digest sent")
        elif not args.dry_run:
            log("  (skipped Telegram — nothing posted)")
    except Exception as e:
        log(f"  Telegram notify failed: {e}")
    log("=" * 60)
    log("State saved to daily_freelance_state.json")


if __name__ == "__main__":
    main()
