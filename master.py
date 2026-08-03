"""Master Orchestrator — runs the full automation stack end-to-end.

Usage:
    python master.py                    # run all
    python master.py --bid-only         # just generate Arabic bids
    python master.py --n8n-only         # just generate n8n replies
    python master.py --contacts         # check review queue + send approved
    python master.py --status           # show engine status
    python master.py --smoke            # run smoke test
    python master.py --verify           # run PHASE 3 verifier
    python master.py --review           # run PHASE 4 reviewer
    python master.py --all              # everything
"""
import os
import sys
import subprocess
from datetime import datetime

ROOT = "C:/Users/A/Desktop/Money"
ENGINE_DIR = f"{ROOT}/ai-automation-engine"
PYTHON = "C:/Users/A/AppData/Local/Programs/Python/Python312/python.exe"


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_step(name, cmd, cwd=None):
    log(f"--- {name} ---")
    try:
        result = subprocess.run(
            [PYTHON] + cmd,
            cwd=cwd or ROOT,
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            log(f"  {name}: OK")
            if result.stdout:
                for line in result.stdout.splitlines()[-5:]:
                    log(f"    {line}")
            return True
        else:
            log(f"  {name}: FAILED (exit {result.returncode})")
            if result.stderr:
                for line in result.stderr.splitlines()[-5:]:
                    log(f"    {line}")
            return False
    except Exception as e:
        log(f"  {name}: ERROR: {e}")
        return False


def status():
    log("--- Status Dashboard ---")
    return run_step("status", ["status.py"])


def smoke():
    log("--- Smoke Test ---")
    return run_step("smoke", ["smoke_test.py"])


def verify():
    log("--- Verifier (PHASE 3) ---")
    return run_step("verify", [f"{ENGINE_DIR}/engine/verifier.py", "verify_report.md"],
                    cwd=ENGINE_DIR)


def review():
    log("--- Reviewer (PHASE 4) ---")
    return run_step("review", [f"{ENGINE_DIR}/engine/reviewer.py", "review_report.md"],
                    cwd=ENGINE_DIR)


def pipeline(task):
    log("--- Pipeline (PHASE 1-4) ---")
    return run_step("pipeline", ["pipeline.py", task])


def bid_runner(platform="both", search="automation", top=3):
    log(f"--- Arabic Bid Runner ({platform}) ---")
    return run_step("bid_runner",
                    ["arabic_bid_runner.py", "--platform", platform,
                     "--search", search, "--top", str(top)])


def main():
    args = sys.argv[1:]
    if not args or "--all" in args:
        results = [
            status(),
            smoke(),
            verify(),
            review(),
        ]
    else:
        results = []
        if "--status" in args:
            results.append(status())
        if "--smoke" in args:
            results.append(smoke())
        if "--verify" in args:
            results.append(verify())
        if "--review" in args:
            results.append(review())
        if "--bid-only" in args:
            results.append(bid_runner())
        if "--n8n-only" in args:
            results.append(bid_runner("nafezly", "n8n"))
        if "--pipeline" in args:
            task = " ".join(a for a in args[1:] if not a.startswith("--"))
            results.append(pipeline(task))

    passed = sum(results)
    total = len(results)
    log(f"=== Results: {passed}/{total} passed ===")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
