"""Deploy Hook helper — trigger Render deploys from CLI.

After setting up the Deploy Hook in Render dashboard (Settings -> Deploy Hook),
save the URL as RENDER_DEPLOY_HOOK env var.

Usage:
    set RENDER_DEPLOY_HOOK=https://api.render.com/deploy/srv-xxx?key=yyy
    python deploy.py
"""
import os
import sys
import requests

HOOK_URL = os.environ.get("RENDER_DEPLOY_HOOK", "").strip()


def deploy():
    if not HOOK_URL:
        print("ERROR: RENDER_DEPLOY_HOOK not set.", file=sys.stderr)
        print("Setup steps:", file=sys.stderr)
        print("  1. Open Render dashboard -> your service -> Settings", file=sys.stderr)
        print("  2. Find 'Deploy Hook' section", file=sys.stderr)
        print("  3. Copy the URL", file=sys.stderr)
        print("  4. Set: setx RENDER_DEPLOY_HOOK '<url>' (Windows)", file=sys.stderr)
        sys.exit(1)

    print(f"Triggering deploy via hook: {HOOK_URL[:80]}...")
    resp = requests.post(HOOK_URL, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:200]}")
    sys.exit(0 if resp.status_code in (200, 201, 202) else 1)


if __name__ == "__main__":
    deploy()
