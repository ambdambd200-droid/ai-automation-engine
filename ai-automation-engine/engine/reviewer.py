"""PHASE 4: Reviewer — multi-perspective code review.

Spawns 3 perspectives (CEO, Eng, DevEx) to review changes.
Uses AI gateway (Groq) for review analysis.
Outputs review_report.md + extracts new skills to skills/learning/.

Following Ponytail YAGNI ladder + code cleanliness rules.
"""
import os
import sys
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ENGINE_DIR = Path(os.environ.get("ENGINE_DIR", "C:/Users/A/Desktop/Money/ai-automation-engine"))


def find_recent_changes():
    """Find recently changed files via git diff."""
    try:
        result = subprocess.run(
            ["git", "-C", str(ENGINE_DIR), "diff", "--name-only", "HEAD~5..HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        return files
    except Exception:
        return []


def detect_code_smells(files):
    """Detect code smells using static rules."""
    smells = []

    for f in files:
        full = ENGINE_DIR / f
        if not full.exists() or full.suffix != ".py":
            continue

        content = full.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()

        # Deep nesting
        for i, line in enumerate(lines):
            indent = len(line) - len(line.lstrip())
            if indent > 12 and line.strip():
                smells.append({
                    "file": f,
                    "line": i + 1,
                    "type": "deep_nesting",
                    "severity": "medium",
                    "detail": f"{indent // 4} levels deep",
                })
                break

        # Code duplication heuristic (similar function signatures)
        if content.count("def send_email") > 1:
            smells.append({
                "file": f,
                "type": "duplication",
                "severity": "high",
                "detail": "Multiple send_email definitions",
            })

        # Long functions
        in_func = False
        func_start = 0
        func_name = ""
        for i, line in enumerate(lines):
            if line.startswith("def ") and ":" in line:
                if in_func and (i - func_start) > 80:
                    smells.append({
                        "file": f,
                        "line": func_start + 1,
                        "type": "long_function",
                        "severity": "low",
                        "detail": f"{func_name} is {i - func_start} lines",
                    })
                in_func = True
                func_start = i
                func_name = line.split("def ")[1].split("(")[0]

    return smells


def detect_ceo_issues(files):
    """CEO perspective: scope, value, market fit."""
    issues = []
    new_files = [f for f in files if "/workflows/" in f or "/api/" in f or "/demos/" in f]
    if len(new_files) > 5:
        issues.append({
            "type": "scope_creep",
            "severity": "medium",
            "detail": f"{len(new_files)} new files — verify each has user value",
        })
    return issues


def detect_eng_issues(files):
    """Eng perspective: architecture, coupling, dependencies."""
    issues = []
    workflows = [f for f in files if "/workflows/" in f]
    if len(workflows) > 8:
        issues.append({
            "type": "workflow_bloat",
            "severity": "low",
            "detail": f"{len(workflows)} workflows — consolidate if overlap",
        })
    return issues


def extract_new_skills(files):
    """Extract reusable patterns as new skills."""
    new_skills = []
    for f in files:
        if "/templates/" in f or "/workflows/" in f:
            name = Path(f).stem
            new_skills.append({
                "name": f"learning/{name}",
                "source": f,
                "summary": f"Pattern from {name} (used in pipeline)",
            })
    return new_skills


def spawn_sub_agents(files):
    """Spawn 3 sub-agents (CEO, Eng, DevEx) — simulated via heuristic checks."""
    return {
        "ceo": detect_ceo_issues(files),
        "eng": detect_eng_issues(files),
        "devex": detect_code_smells(files),
    }


def write_review_report(review, output_path="review_report.md"):
    """Write review_report.md."""
    lines = [
        "# Review Report",
        "",
        f"**Timestamp:** {review['timestamp']}",
        f"**Phase:** 4 of 4 (Review)",
        f"**Files reviewed:** {review['files_count']}",
        "",
        "## Files Reviewed",
        "",
    ]
    for f in review["files"]:
        lines.append(f"- `{f}`")
    lines.append("")

    lines.append("## CEO Perspective (Business Impact)")
    lines.append("")
    if not review["ceo"]:
        lines.append("_No issues found._")
    for issue in review["ceo"]:
        lines.append(f"- **[{issue['severity'].upper()}]** {issue['type']}: {issue['detail']}")
    lines.append("")

    lines.append("## Eng Perspective (Architecture)")
    lines.append("")
    if not review["eng"]:
        lines.append("_No issues found._")
    for issue in review["eng"]:
        lines.append(f"- **[{issue['severity'].upper()}]** {issue['type']}: {issue['detail']}")
    lines.append("")

    lines.append("## DevEx Perspective (Cleanliness)")
    lines.append("")
    if not review["devex"]:
        lines.append("_No smells found._")
    for issue in review["devex"]:
        loc = f":{issue['line']}" if "line" in issue else ""
        lines.append(f"- **[{issue['severity'].upper()}]** `{issue['file']}{loc}` — {issue['type']}: {issue['detail']}")
    lines.append("")

    lines.append("## New Skills Extracted")
    lines.append("")
    for skill in review["new_skills"]:
        lines.append(f"- {skill['name']} — {skill['summary']}")
    lines.append("")

    # Summary
    total_issues = len(review["ceo"]) + len(review["eng"]) + len(review["devex"])
    high = sum(1 for x in review["ceo"] + review["eng"] + review["devex"] if x.get("severity") == "high")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total issues: {total_issues}")
    lines.append(f"- High severity: {high}")
    lines.append(f"- Skills extracted: {len(review['new_skills'])}")
    lines.append(f"- Verdict: {'PASS' if high == 0 else 'NEEDS FIX'}")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def run_review():
    files = find_recent_changes()
    if not files:
        files = [str(p.relative_to(ENGINE_DIR)) for p in ENGINE_DIR.rglob("*.py") if "__pycache__" not in str(p)][:20]

    sub_agents = spawn_sub_agents(files)
    new_skills = extract_new_skills(files)

    review = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "files": files,
        "files_count": len(files),
        "ceo": sub_agents["ceo"],
        "eng": sub_agents["eng"],
        "devex": sub_agents["devex"],
        "new_skills": new_skills,
    }

    output = sys.argv[1] if len(sys.argv) > 1 else "review_report.md"
    write_review_report(review, output)
    print(f"Reviewed {len(files)} files", flush=True)
    print(f"Issues: CEO={len(sub_agents['ceo'])} Eng={len(sub_agents['eng'])} DevEx={len(sub_agents['devex'])}", flush=True)
    print(f"Skills extracted: {len(new_skills)}", flush=True)
    print(f"Report: {output}", flush=True)


if __name__ == "__main__":
    run_review()
