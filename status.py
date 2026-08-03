"""Status Dashboard — queries engine + shows current state.

Usage:
    python status.py          # one-time
    python status.py --watch  # refresh every 30s
"""
import os
import sys
import time
import json
import requests
from datetime import datetime

ENGINE_URL = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def fetch_status():
    """Fetch all status from engine."""
    status = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "engine_online": False,
        "workflows": [],
        "task_types": [],
        "pending_contacts": 0,
        "recent_executions": [],
        "hunt_events": [],
    }

    try:
        r = requests.get(f"{ENGINE_URL}/health", timeout=5)
        status["engine_online"] = r.status_code == 200
    except Exception:
        return status

    try:
        r = requests.get(f"{ENGINE_URL}/workflows", timeout=5)
        status["workflows"] = r.json().get("workflows", [])
    except Exception:
        pass

    try:
        r = requests.get(f"{ENGINE_URL}/api/task-types", timeout=5)
        status["task_types"] = r.json().get("task_types", [])
    except Exception:
        pass

    try:
        r = requests.get(f"{ENGINE_URL}/api/contacts?pending=true", timeout=5)
        status["pending_contacts"] = len(r.json().get("contacts", []))
    except Exception:
        pass

    try:
        r = requests.get(f"{ENGINE_URL}/executions?limit=5", timeout=5)
        status["recent_executions"] = [
            {"workflow": e["workflow"], "status": e["status"]}
            for e in r.json().get("executions", [])
        ]
    except Exception:
        pass

    try:
        r = requests.get(f"{ENGINE_URL}/api/hunt_events?limit=10", timeout=5)
        status["hunt_events"] = r.json().get("events", [])
    except Exception:
        pass

    return status


def display(status):
    """Pretty-print status."""
    print("\n" + "=" * 60)
    print(f"  AI Automation Engine — Status Dashboard")
    print(f"  {status['timestamp']}")
    print("=" * 60)

    online = status["engine_online"]
    mark = "ONLINE" if online else "OFFLINE"
    print(f"\n  Engine: {mark}")

    print(f"\n  Workflows ({len(status['workflows'])}):")
    for wf in status["workflows"]:
        print(f"    - {wf}")

    print(f"\n  Task Types ({len(status['task_types'])}):")
    for tt in status["task_types"]:
        print(f"    - {tt}")

    print(f"\n  Pending Reviews: {status['pending_contacts']}")

    if status["recent_executions"]:
        print(f"\n  Recent Executions:")
        for e in status["recent_executions"]:
            mark = "OK" if e["status"] == "completed" else "FAIL"
            print(f"    [{mark}] {e['workflow']}")

    if status["hunt_events"]:
        print(f"\n  Recent Hunt Events:")
        for e in status["hunt_events"][:5]:
            print(f"    - {e.get('item_type', '?')}: {e.get('recipient', '?')[:40]}")

    print("\n" + "=" * 60 + "\n")


def main():
    watch = "--watch" in sys.argv
    interval = 30

    if watch:
        log(f"Watching {ENGINE_URL} every {interval}s (Ctrl+C to stop)")
        try:
            while True:
                status = fetch_status()
                display(status)
                time.sleep(interval)
        except KeyboardInterrupt:
            log("Stopped")
    else:
        status = fetch_status()
        display(status)


if __name__ == "__main__":
    main()
