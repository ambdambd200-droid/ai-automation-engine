"""
skill_manager.py — Lightweight skills library for the Money/ workspace.

A "skill" is a reusable template + learned pattern. Skills let hunt.py (and
any other script) reuse what worked before instead of regenerating from
scratch with the AI. Skills live as plain JSON files in Money/skills/.

Why this exists:
  - Reduce AI API calls (skill matches short-circuit AI generation)
  - Persist what worked (manual review of sent items becomes a skill)
  - Make the system learn over time without external DB

Skill JSON format:
  {
    "name": "string",
    "type": "arabic_bid|email_reply|email_followup|forum_reply",
    "language": "ar|en",
    "tags": ["n8n", "automation", ...],
    "template": "the reusable text",
    "rules": ["rule 1", "rule 2", ...],
    "examples": [{"input": "...", "output": "..."}],
    "uses": 0,                       # counter
    "last_used": "ISO date",         # tracking
    "created": "ISO date",
    "version": 1
  }

Public API:
  list_skills(type=None) -> list of dict
  get_skill(name) -> dict | None
  find_best_skill(type, context_keywords) -> dict | None
  save_skill(name, payload) -> bool
  record_use(skill_name) -> bool
  learn_from_sent(item) -> dict | None   # convert a sent item into a skill
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKILLS_DIR = Path(__file__).resolve().parent
INDEX_FILE = SKILLS_DIR / "index.json"


def _load_index() -> dict:
    if not INDEX_FILE.exists():
        return {"version": 1, "skills": {}, "updated": _now()}
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "skills": {}, "updated": _now()}


def _save_index(idx: dict) -> None:
    idx["updated"] = _now()
    INDEX_FILE.write_text(
        json.dumps(idx, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _skill_path(name: str) -> Path:
    return SKILLS_DIR / name / f"{name.split('/')[-1]}.json"


def list_skills(skill_type: Optional[str] = None) -> list:
    idx = _load_index()
    skills = list(idx.get("skills", {}).values())
    if skill_type:
        skills = [s for s in skills if s.get("type") == skill_type]
    return skills


def get_skill(name: str) -> Optional[dict]:
    """Load a skill by its path (e.g. 'arabic_bid/mostaql')."""
    path = SKILLS_DIR / f"{name}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_skill(name: str, payload: dict) -> bool:
    """Save a skill. `name` is the path like 'arabic_bid/mostaql' or 'learning/learned_xxx'."""
    file_path = SKILLS_DIR / f"{name}.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    payload.setdefault("created", _now())
    payload["version"] = payload.get("version", 1) + 1
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    idx = _load_index()
    idx.setdefault("skills", {})[name] = {
        "name": payload.get("name", name),
        "type": payload.get("type"),
        "language": payload.get("language"),
        "tags": payload.get("tags", []),
        "uses": payload.get("uses", 0),
        "last_used": payload.get("last_used"),
        "version": payload["version"],
        "source": payload.get("source"),
    }
    _save_index(idx)
    return True


def record_use(name: str) -> bool:
    """Increment a skill's use counter."""
    skill = get_skill(name)
    if not skill:
        return False
    skill["uses"] = skill.get("uses", 0) + 1
    skill["last_used"] = _now()
    file_path = SKILLS_DIR / f"{name}.json"
    file_path.write_text(
        json.dumps(skill, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    idx = _load_index()
    if name in idx.get("skills", {}):
        idx["skills"][name]["uses"] = skill["uses"]
        idx["skills"][name]["last_used"] = skill["last_used"]
        _save_index(idx)
    return True


def find_best_skill(
    skill_type: str,
    context_keywords: Optional[list] = None,
) -> Optional[dict]:
    """Find a skill by type + keyword match. Returns the highest-scoring skill
    with the full template loaded (not just the index entry).

    Scoring:
      +3 for each tag match
      +1 for each word match in context_keywords
      +1 if the skill's language matches the context
    """
    keywords = [k.lower() for k in (context_keywords or []) if k]
    idx = _load_index()
    candidates_meta = [
        meta for meta in idx.get("skills", {}).values()
        if meta.get("type") == skill_type
    ]
    if not candidates_meta:
        return None
    best = None
    best_score = 0
    for meta in candidates_meta:
        full = get_skill(meta["name"])
        if not full:
            continue
        score = 0
        tags = [t.lower() for t in full.get("tags", [])]
        for k in keywords:
            for t in tags:
                if k in t or t in k:
                    score += 3
        for k in keywords:
            kw = k.lower()
            for t in tags:
                if kw in t or t in kw:
                    score += 1
        if score > best_score:
            best = full
            best_score = score
    if best_score == 0 and candidates_meta:
        candidates_full = [
            get_skill(m["name"]) for m in candidates_meta
        ]
        candidates_full = [c for c in candidates_full if c]
        if candidates_full:
            best = max(candidates_full, key=lambda s: s.get("uses", 0))
    return best


def apply_skill(
    skill: dict,
    variables: Optional[dict] = None,
    use_ai_polish: bool = True,
) -> Optional[str]:
    """Apply a skill template by substituting {var} placeholders.

    If use_ai_polish is True, the filled template is sent through
    keyhub_client.ai_generate for a light polish. Returns the final text
    or None on failure.
    """
    if not skill:
        return None
    template = skill.get("template", "")
    if not template:
        return None
    variables = variables or {}
    out = template
    for k, v in variables.items():
        out = out.replace("{" + k + "}", str(v))
        out = out.replace("{{" + k + "}}", str(v))
    if use_ai_polish and os.environ.get("SKILL_NO_POLISH") != "1":
        try:
            sys.path.insert(0, str(SKILLS_DIR.parent))
            from keyhub_client import ai_generate
            prompt = (
                "You are polishing a message for Alaa Fathi (AI Automation Engineer).\n"
                "Keep the structure, language, and intent. Only improve clarity and "
                "personalization based on the variables provided.\n"
                f"Variables: {json.dumps(variables, ensure_ascii=False)}\n\n"
                f"Draft:\n{out}\n\n"
                "Return ONLY the polished text, no commentary."
            )
            polished = ai_generate(
                prompt,
                max_tokens=600,
                temperature=0.3,
                caller="skill_manager",
            )
            if polished:
                record_use(skill.get("name", ""))
                return polished
        except Exception:
            pass
    record_use(skill.get("name", ""))
    return out


def learn_from_sent(item: dict) -> Optional[dict]:
    """Convert a sent item (from hunt_decisions or sent log) into a skill draft.

    Returns the skill payload that can be saved with save_skill().
    """
    if not item or not item.get("body"):
        return None
    item_type = item.get("type", "")
    if item_type == "arabic_bid":
        return {
            "name": f"arabic_bid/learned_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "type": "arabic_bid",
            "language": "ar",
            "tags": [item.get("platform", "freelance"), "n8n", "automation"],
            "template": item["body"],
            "rules": ["keep Arabic formal (فصحى)", "reference project details"],
        }
    if item_type in ("email_followup", "email_reply"):
        return {
            "name": f"email_{item_type.split('_')[-1]}/learned_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "type": item_type,
            "language": "en",
            "tags": ["followup" if "followup" in item_type else "reply"],
            "template": item["body"],
            "rules": ["3-5 sentences max", "sign off as Alaa Fathi"],
        }
    if item_type == "forum_reply":
        return {
            "name": f"forum_reply/learned_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "type": "forum_reply",
            "language": "en",
            "tags": ["n8n", "community"],
            "template": item["body"],
            "rules": ["technical", "concise"],
        }
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Skills library manager")
    parser.add_argument("--list", action="store_true", help="List all skills")
    parser.add_argument("--type", help="Filter by type (arabic_bid, email_*, forum_reply)")
    parser.add_argument("--find", nargs="+", help="Find best skill by type + keywords")
    parser.add_argument("--show", help="Show a specific skill by name (e.g. arabic_bid/mostaql)")
    parser.add_argument("--stats", action="store_true", help="Show usage stats")
    args = parser.parse_args()

    if args.list:
        for s in list_skills(args.type):
            print(f"  {s.get('name'):<40} type={s.get('type'):<16} uses={s.get('uses', 0)}")
    elif args.show:
        s = get_skill(args.show)
        if s:
            print(json.dumps(s, ensure_ascii=False, indent=2))
        else:
            print(f"  Not found: {args.show}")
    elif args.find and len(args.find) >= 2:
        s = find_best_skill(args.find[0], args.find[1:])
        if s:
            print(f"Best match: {s.get('name')}")
            print(f"  Type: {s.get('type')}")
            print(f"  Tags: {s.get('tags')}")
            print(f"  Uses: {s.get('uses', 0)}")
        else:
            print("  No matching skill found.")
    elif args.stats:
        idx = _load_index()
        total = sum(s.get("uses", 0) for s in idx.get("skills", {}).values())
        n = len(idx.get("skills", {}))
        print(f"Skills: {n}")
        print(f"Total uses: {total}")
        for name, meta in idx.get("skills", {}).items():
            print(f"  {name:<40} {meta.get('uses', 0)} uses, v{meta.get('version', 1)}")
    else:
        parser.print_help()
