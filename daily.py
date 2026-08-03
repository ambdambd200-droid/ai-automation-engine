"""
Daily routine runner — FREE, no API costs.

Runs the full daily routine in one command:
  1. Engine health check
  2. Gmail reply check
  3. (Optional) Generate follow-up drafts for 5+ day old applications
  4. (Optional) Open Working Nomads / WWR for new job search

Run:
  python daily.py
"""

import subprocess
import sys
from datetime import datetime
import os

PYTHON = r"C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe"
WORKSPACE = r"C:\Users\A\Desktop\Money"
ENGINE_DIR = r"C:\Users\A\Desktop\Money\ai-automation-engine"


def step(title, cmd, cwd=None):
    print()
    print("=" * 60)
    print(f"STEP: {title}")
    print("=" * 60)
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=60
        )
        print(result.stdout)
        if result.stderr:
            print(f"[stderr]: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] Step took >60s, skipping.")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def main():
    print("#" * 60)
    print(f"# DAILY ROUTINE — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#" * 60)

    # 1. Engine health
    step("Engine health check", "curl -s http://127.0.0.1:5000/health")

    # 2. Gmail reply check
    step("Gmail reply check", f'"{PYTHON}" gmail_check.py', cwd=WORKSPACE)

    # 3. Learn — convert any sent items into reusable skills
    step("Skill autosave (turn sent items into skills)",
         f'"{PYTHON}" hunt.py --learn', cwd=WORKSPACE)

    print()
    print("=" * 60)
    print("MANUAL STEPS (you do these)")
    print("=" * 60)
    print()
    print("1. Open Application_Pipeline.md, update status based on Gmail results")
    print("2. If 5+ days since any 'Sent' app, draft follow-up using Template C")
    print("3. Open Working Nomads or We Work Remotely")
    print("4. Find 1 new matching job, add to Job_Queue.md")
    print("5. (Mon/Wed/Fri) Publish scheduled LinkedIn post from LinkedIn_Posts_Series.md")
    print()
    print("Reminder: ASK before sending any email or posting publicly.")
    print("See Protocols.md for full rules.")


if __name__ == "__main__":
    main()
