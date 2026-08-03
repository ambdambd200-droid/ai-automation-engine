"""
check_deps.py — Dependency version checker.

Compares installed packages against requirements.txt and reports
out-of-date or missing packages. Run periodically to catch dependency drift.

USAGE:
  python check_deps.py                    # Check all deps
  python check_deps.py --update           # pip install --upgrade outdated
  python check_deps.py --check-playwright # Verify Playwright browsers installed
"""

import subprocess
import sys
import re
from pathlib import Path

WORKSPACE = Path(__file__).parent.resolve()
REQUIREMENTS = WORKSPACE / "ai-automation-engine" / "requirements.txt"


def get_installed() -> dict:
    """Return {package_name: version} for all installed packages."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=json"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"  ⚠ pip list failed: {result.stderr[:200]}")
        return {}
    import json
    return {pkg["name"].lower(): pkg["version"] for pkg in json.loads(result.stdout)}


def parse_requirements(path: Path) -> list:
    """Return list of (package_name, version_spec) from a requirements file."""
    deps = []
    if not path.exists():
        return deps
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Split on ==, >=, <=, ~=, !=
        match = re.match(r"([a-zA-Z0-9_.-]+)\s*([><=!~]+\s*[\d.*]+)?", line)
        if match:
            name = match.group(1).lower()
            spec = match.group(2) or ""
            deps.append((name, spec.strip()))
    return deps


def check_playwright() -> bool:
    """Check if Playwright browsers are installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--dry-run"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            print("  ✅ Playwright browsers: OK")
            return True
    except Exception:
        pass
    # Fallback: check ms-playwright directory
    playwright_dirs = list(Path.home().glob("AppData/Local/ms-playwright/*"))
    if playwright_dirs:
        browsers = [d.name for d in playwright_dirs]
        print(f"  ✅ Playwright browsers: {len(browsers)} installed ({', '.join(browsers[:3])}...)")
        return True
    print("  ⚠ Playwright browsers: NOT FOUND (run `playwright install chromium`)")
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Dependency version checker")
    parser.add_argument("--update", action="store_true", help="Upgrade outdated packages")
    parser.add_argument("--check-playwright", action="store_true", help="Verify Playwright browsers")
    args = parser.parse_args()

    print("=" * 50)
    print("  DEPENDENCY CHECK")
    print("=" * 50)
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Requirements: {REQUIREMENTS}")
    print()

    if args.check_playwright:
        check_playwright()
        return

    installed = get_installed()
    if not installed:
        print("  ⚠ Could not get installed packages.")
        return

    deps = parse_requirements(REQUIREMENTS)
    if not deps:
        print(f"  ⚠ No requirements found in {REQUIREMENTS}")
        return

    print(f"  {'Package':<25} {'Required':<15} {'Installed':<15} {'Status'}")
    print(f"  {'-'*25} {'-'*15} {'-'*15} {'-'*10}")

    outdated = []
    missing = []
    for name, spec in deps:
        installed_ver = installed.get(name)
        if installed_ver is None:
            missing.append(name)
            print(f"  {name:<25} {spec:<15} {'—':<15} ❌ MISSING")
            continue
        status = "✅"
        if spec:
            # Simple version check — if spec says ==X.Y, check it
            eq_match = re.match(r"==\s*([\d.]+)", spec)
            if eq_match and installed_ver != eq_match.group(1):
                status = "⚠ DIFF"
                outdated.append((name, eq_match.group(1), installed_ver))
        print(f"  {name:<25} {spec:<15} {installed_ver:<15} {status}")

    print()

    if missing:
        print(f"  ❌ {len(missing)} missing package(s): {', '.join(missing)}")
        if args.update:
            print("  Installing missing packages...")
            subprocess.run([sys.executable, "-m", "pip", "install", *missing], timeout=120)
            print("  ✅ Installed.")
    else:
        print("  ✅ All requirements packages installed.")

    if outdated:
        print(f"  ⚠ {len(outdated)} package(s) have version differences.")
        if args.update:
            for name, req_ver, cur_ver in outdated:
                print(f"    Upgrading {name} {cur_ver} → {req_ver}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", f"{name}=={req_ver}"],
                    timeout=120,
                )
            print("  ✅ Upgraded.")
    else:
        print("  ✅ All versions match requirements.")

    print()
    check_playwright()


if __name__ == "__main__":
    main()
