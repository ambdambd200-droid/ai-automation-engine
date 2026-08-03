"""
skills_query.py — Search the local skills library from CLI.

Usage:
  python skills_query.py "nafezly n8n bid"
  python skills_query.py --tags arabic,bid
  python skills_query.py --type arabic_bid --limit 5
  python skills_query.py --list-types
  python skills_query.py --list-tags
"""
import json, argparse, sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
INDEX_PATH = WORKSPACE / "skills" / "index.json"


def load_index():
    if not INDEX_PATH.exists():
        print(f"Index not found: {INDEX_PATH}")
        sys.exit(1)
    with open(INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


def search_by_text(idx, query, limit=10):
    skills = idx.get("skills", {})
    if isinstance(skills, dict):
        skills = list(skills.values())
    if not skills:
        return []

    q = query.lower().strip()
    if not q:
        return []

    scored = []
    for s in skills:
        if not isinstance(s, dict):
            continue
        score = 0
        name = s.get("name", "").lower()
        tags = [t.lower() for t in s.get("tags", [])]
        stype = s.get("type", "").lower()

        if q in name:
            score += 3
        if q in stype:
            score += 2
        for tag in tags:
            if q in tag:
                score += 2
        if score:
            scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:limit]]


def search_by_tags(idx, tag_list, limit=10):
    skills = idx.get("skills", {})
    if isinstance(skills, dict):
        skills = list(skills.values())
    wanted = {t.strip().lower() for t in tag_list}
    matched = []
    for s in skills:
        if not isinstance(s, dict):
            continue
        tags = {t.lower() for t in s.get("tags", [])}
        if wanted & tags:
            matched.append(s)
    return matched[:limit]


def filter_by_type(idx, skill_type, limit=10):
    skills = idx.get("skills", {})
    if isinstance(skills, dict):
        skills = list(skills.values())
    matched = [s for s in skills if isinstance(s, dict) and s.get("type") == skill_type]
    return matched[:limit]


def print_skill(s, idx=0):
    prefix = f"[{idx}] " if idx else ""
    print(f"{prefix}{s.get('name','(unnamed)')}")
    print(f"    Type: {s.get('type','?')} | Lang: {s.get('language','?')}")
    print(f"    Tags: {', '.join(s.get('tags',[])) or '(none)'}")
    print(f"    Uses: {s.get('uses',0)} | From real: {s.get('from_real',False)}")
    path = s.get("path")
    if path:
        print(f"    File: {path}")
    print()


def list_types(idx):
    skills = idx.get("skills", {})
    if isinstance(skills, dict):
        skills = list(skills.values())
    types = set(s.get("type") for s in skills if isinstance(s, dict) and s.get("type"))
    print("Available types:")
    for t in sorted(types):
        print(f"  {t}")


def list_tags(idx):
    skills = idx.get("skills", {})
    if isinstance(skills, dict):
        skills = list(skills.values())
    all_tags = set()
    for s in skills:
        if isinstance(s, dict):
            all_tags.update(s.get("tags", []))
    print("Available tags:")
    for t in sorted(all_tags):
        print(f"  {t}")


def main():
    p = argparse.ArgumentParser(description="Query local skills library")
    p.add_argument("query", nargs="?", help="Free-text search")
    p.add_argument("--tags", help="Comma-separated tag filter")
    p.add_argument("--type", help="Filter by skill type")
    p.add_argument("--limit", type=int, default=10, help="Max results")
    p.add_argument("--list-types", action="store_true")
    p.add_argument("--list-tags", action="store_true")
    p.add_argument("--show-template", action="store_true", help="Print template content")
    args = p.parse_args()

    idx = load_index()

    if args.list_types:
        list_types(idx)
        return
    if args.list_tags:
        list_tags(idx)
        return

    results = []
    if args.query:
        results = search_by_text(idx, args.query, args.limit)
    elif args.tags:
        results = search_by_tags(idx, args.tags.split(","), args.limit)
    elif args.type:
        results = filter_by_type(idx, args.type, args.limit)
    else:
        p.print_help()
        return

    if not results:
        print("No skills matched.")
        return

    print(f"Found {len(results)} skill(s):\n")
    for i, s in enumerate(results, 1):
        print_skill(s, i)

        if args.show_template:
            path = Path(__file__).resolve().parent / s.get("path", "")
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    tmpl = data.get("template", "")
                    if tmpl:
                        print("    --- TEMPLATE ---")
                        for line in tmpl.splitlines()[:30]:
                            print(f"    {line}")
                        if len(tmpl.splitlines()) > 30:
                            print(f"    ... ({len(tmpl.splitlines())} lines total)")
                        print("    --- END ---\n")
                except Exception:
                    pass


if __name__ == "__main__":
    main()