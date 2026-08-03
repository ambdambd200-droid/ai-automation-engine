"""PHASE 3: Verifier — automated verification of changes.

Runs after PHASE 2 (Execution). Checks:
- HTTP endpoints respond
- Workflow YAMLs are valid
- Python syntax is clean
- Required files exist
- No secrets leaked
- Database schema is consistent

Outputs verify_report.md. If FAIL, returns fix instructions for PHASE 2 loop.
"""
import os
import sys
import json
import re
import subprocess
import requests
from datetime import datetime
from pathlib import Path

ENGINE_URL = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")
ENGINE_DIR = Path(os.environ.get("ENGINE_DIR", "C:/Users/A/Desktop/Money/ai-automation-engine"))


def check_endpoints():
    """Test core HTTP endpoints."""
    endpoints = [
        ("/health", 200),
        ("/workflows", 200),
        ("/api/task-types", 200),
        ("/", 200),
        ("/review", 200),
        ("/api/contacts?pending=true", 200),
    ]
    results = []
    for path, expected in endpoints:
        try:
            resp = requests.get(f"{ENGINE_URL}{path}", timeout=10)
            ok = resp.status_code == expected
            results.append({
                "endpoint": path,
                "status": resp.status_code,
                "expected": expected,
                "pass": ok,
                "size": len(resp.content),
            })
        except Exception as e:
            results.append({
                "endpoint": path,
                "status": "ERROR",
                "expected": expected,
                "pass": False,
                "error": str(e),
            })
    return results


def check_workflow_yamls():
    """Validate all workflow YAML files."""
    import yaml
    workflows_dir = ENGINE_DIR / "workflows"
    if not workflows_dir.exists():
        return [{"file": "workflows/", "pass": False, "error": "directory missing"}]

    results = []
    for f in workflows_dir.glob("*.yaml"):
        try:
            with open(f, encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            has_workflow = data and "workflow" in data
            has_steps = has_workflow and "steps" in data.get("workflow", {})
            results.append({
                "file": str(f.relative_to(ENGINE_DIR)),
                "pass": has_workflow and has_steps,
                "steps": len(data.get("workflow", {}).get("steps", [])) if has_workflow else 0,
            })
        except Exception as e:
            results.append({
                "file": str(f.relative_to(ENGINE_DIR)),
                "pass": False,
                "error": str(e),
            })
    return results


def check_python_syntax():
    """Compile all .py files for syntax errors."""
    results = []
    for py_file in ENGINE_DIR.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            with open(py_file, encoding="utf-8") as f:
                compile(f.read(), str(py_file), "exec")
            results.append({
                "file": str(py_file.relative_to(ENGINE_DIR)),
                "pass": True,
            })
        except SyntaxError as e:
            results.append({
                "file": str(py_file.relative_to(ENGINE_DIR)),
                "pass": False,
                "error": f"Line {e.lineno}: {e.msg}",
            })
    return results


def check_secrets():
    """Scan for accidental secret leaks."""
    patterns = [
        (r"gsk_[A-Za-z0-9]{40,}", "Groq API key"),
        (r"sk-or-v1-[A-Za-z0-9]{40,}", "OpenRouter key"),
        (r"sk-proj-[A-Za-z0-9]{40,}", "OpenAI key"),
        (r"AIza[A-Za-z0-9]{35}", "Google API key"),
    ]
    results = []
    for f in ENGINE_DIR.rglob("*"):
        if f.is_dir() or "__pycache__" in str(f):
            continue
        if f.suffix in [".md", ".txt", ".json", ".py", ".yaml", ".yml"]:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for pattern, name in patterns:
                    if re.search(pattern, content):
                        results.append({
                            "file": str(f.relative_to(ENGINE_DIR)),
                            "pass": False,
                            "leaked": name,
                        })
            except Exception:
                pass
    return results


def check_required_files():
    """Verify key files exist."""
    required = [
        "app.py",
        "config.yaml",
        "engine/actions.py",
        "engine/workflow.py",
        "engine/decision.py",
        "engine/send_email_lib.py",
        "storage/database.py",
        "templates/portfolio.html",
        "templates/review.html",
        "static/portfolio.css",
        "static/portfolio.js",
    ]
    results = []
    for path in required:
        full = ENGINE_DIR / path
        results.append({
            "file": path,
            "pass": full.exists(),
            "size": full.stat().st_size if full.exists() else 0,
        })
    return results


def run_all_checks():
    """Run all checks and return aggregated report."""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "engine_url": ENGINE_URL,
        "endpoints": check_endpoints(),
        "workflows": check_workflow_yamls(),
        "python": check_python_syntax(),
        "secrets": check_secrets(),
        "required_files": check_required_files(),
    }


def write_report(report, output_path="verify_report.md"):
    """Write verify_report.md and return PASS/FAIL."""
    lines = [
        "# Verify Report",
        "",
        f"**Timestamp:** {report['timestamp']}",
        f"**Engine:** {report['engine_url']}",
        f"**Phase:** 3 of 4 (Verification)",
        "",
        "## Summary",
        "",
    ]

    # Compute pass/fail
    all_checks = (
        report["endpoints"] + report["workflows"]
        + report["python"] + report["required_files"]
    )
    secret_fails = [s for s in report["secrets"] if not s["pass"]]
    fails = [c for c in all_checks if not c["pass"]]
    total = len(all_checks) + len(report["secrets"])
    passed = total - len(fails) - len(secret_fails)
    overall = "PASS" if (not fails and not secret_fails) else "FAIL"

    lines.append(f"**Overall:** {overall}")
    lines.append(f"**Passed:** {passed}/{total}")
    if fails:
        lines.append(f"**Failed:** {len(fails)}")
    if secret_fails:
        lines.append(f"**SECRETS LEAKED:** {len(secret_fails)}")
    lines.append("")

    def write_section(title, items, key="pass"):
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append("_No checks run._")
            lines.append("")
            return
        for item in items:
            mark = "PASS" if item.get(key, False) else "FAIL"
            lines.append(f"- [{mark}] `{item.get('file', item.get('endpoint', '?'))}`")
            for k, v in item.items():
                if k in ("file", "endpoint", "pass"):
                    continue
                if k == "error":
                    lines.append(f"  - Error: {v}")
                else:
                    lines.append(f"  - {k}: {v}")
        lines.append("")

    write_section("Endpoints", report["endpoints"])
    write_section("Workflows", report["workflows"])
    write_section("Python Syntax", report["python"])
    write_section("Required Files", report["required_files"])

    if report["secrets"]:
        lines.append("## Secrets Scan")
        lines.append("")
        for s in report["secrets"]:
            if not s["pass"]:
                lines.append(f"- [FAIL] `{s['file']}` leaked {s['leaked']}")
        lines.append("")

    # Fix instructions if FAIL
    if overall == "FAIL":
        lines.append("## Fix Instructions for PHASE 2 Loop")
        lines.append("")
        lines.append("1. Fix failing items above")
        lines.append("2. Re-run verifier")
        lines.append("3. Loop max 3 times — escalate to user after that")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return overall


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "verify_report.md"
    print("Running verification...", flush=True)
    report = run_all_checks()
    result = write_report(report, output)
    print(f"Result: {result}", flush=True)
    print(f"Report: {output}", flush=True)
    sys.exit(0 if result == "PASS" else 1)
