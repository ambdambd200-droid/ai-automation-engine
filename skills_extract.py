"""
skills_extract.py — Extract real sent items from hunt_decisions.md
and convert them into reusable JSON skills.

Rule: every sent bid, follow-up email, or forum reply becomes a
reusable template in skills/ with:
  - original body cleaned of recipient-specific fields
  - variables: TO, SUBJECT, first_name, context, topic, company
  - signature as Salim Muhammad (not Alaa Fathi)

After extraction, `skills/index.json` is rebuilt.

MUST call from anywhere in Money/ workspace:
  python skills_extract.py
  python skills_extract.py --without-forum  # emails only
"""
import json, re, hashlib
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path(__file__).resolve().parent
DECISIONS_MD = WORKSPACE / "hunt_decisions.md"
STATE_JSON = WORKSPACE / "hunt_state.json"
SKILLS_DIR = WORKSPACE / "skills"
INDEX_PATH = SKILLS_DIR / "index.json"

# types and their skill folders + defaults
TYPE_MAP = {
    "email_followup": {
        "folder": "email_followup",
        "tags": ["email", "followup", "english", "cold"],
        "template_file": "english_cold.json",
        "default_subject": "Following up — quick test task for {company}",
        "sign": "Salim Muhammad\nAI Automation Engineer\nsalim.muhammad.work@gmail.com",
    },
    "email_reply": {
        "folder": "email_reply",
        "tags": ["email", "reply", "english"],
        "template_file": "professional_en.json",
        "default_subject": "",
        "sign": "Salim Muhammad\nAI Automation Engineer\nsalim.muhammad.work@gmail.com",
    },
    "forum_reply": {
        "folder": "forum_reply",
        "tags": ["forum", "technical", "n8n"],
        "template_file": "technical_n8n.json",
        "default_subject": "",
        "sign": "Salim\nsalim.muhammad.work@gmail.com",
    },
    "arabic_bid": {
        "folder": "arabic_bid",
        "tags": ["arabic", "bid", "mostaql", "nafezly"],
        "template_file": "mostaql.json",
        "default_subject": "",
        "sign": "سليم محمد\nمهندس أتمتة ذكاء اصطناعي\nsalim.muhammad.work@gmail.com",
    },
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _body_hash(body: str) -> str:
    return hashlib.md5(body.encode()).hexdigest()[:12]


def _load_decisions():
    if not DECISIONS_MD.exists():
        return []
    text = DECISIONS_MD.read_text(encoding="utf-8")
    blocks = re.split(r"\n## DECISION:", text)
    items = []
    for blk in blocks:
        if "item_" not in blk[:50]:
            continue
        action_match = re.search(r"ACTION:\s*(\w+)", blk)
        type_match = re.search(r"TYPE:\s*(\w+)", blk)
        body_match = re.search(r"BODY:\n(.+)", blk, re.DOTALL)
        if action_match and body_match and type_match:
            items.append({
                "action": action_match.group(1),
                "type": type_match.group(1),
                "body": body_match.group(1).strip(),
            })
    return items


def _load_sent_state():
    if not STATE_JSON.exists():
        return []
    try:
        state = json.loads(STATE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    sent = state.get("sent", [])
    items = []
    for s in sent:
        if isinstance(s, dict) and s.get("body"):
            items.append({
                "action": "sent",
                "type": s.get("type", "email_followup"),
                "body": s.get("body", "").strip(),
                "to": s.get("to", ""),
                "subject": s.get("subject", ""),
            })
    return items


def _clean_body(body, item_type):
    """Strip recipient-specific refs but keep structure."""
    body = body.replace("Alaa Fathi", "Salim Muhammad")
    body = body.replace("ambdambd200@gmail.com", "salim.muhammad.work@gmail.com")
    body = body.replace("Alaa", "Salim")
    b = body.replace("ZY IMMO", "{company}")
    b = b.replace("Asiacruit", "{company}")
    b = b.replace("Synergy Effect", "{company}")
    b = b.replace("Wayne", "{first_name}")
    b = b.replace("Nikolaos", "{first_name}")
    b = b.replace("Michael", "{first_name}")
    b = b.replace("Best,\nSalim Muhammad", "Best,\n{signature}")
    b = b.strip()
    return b


def _write_skill(item_type, body, template_file, tags, sign):
    folder = TYPE_MAP.get(item_type, TYPE_MAP["email_followup"])["folder"]
    out_dir = SKILLS_DIR / folder
    out_dir.mkdir(parents=True, exist_ok=True)

    bhash = _body_hash(body)
    slug = f"{template_file.replace('.json','')}_real_{bhash[:6]}"
    path = out_dir / f"{slug}.json"

    skill = {
        "name": f"{folder}/{slug}",
        "type": item_type,
        "language": "en",
        "tags": tags,
        "template": body.replace("Best,\n{signature}", sign),
        "rules": [
            "Fill {first_name} from recipient's known name",
            "Fill {company} from recipient's company name",
            "Fill {topic} from the email subject pattern",
            "sign as Salim Muhammad",
        ],
        "examples": [],
        "uses": 0,
        "last_used": None,
        "created": _now(),
        "version": 2,
        "from_real": True,
        "source": "extracted from hunt_decisions.md",
        "body_hash": bhash,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(skill, f, ensure_ascii=False, indent=2)
    return path


def _rebuild_index():
    idx = {"updated": _now(), "skills": []}
    for folder in SKILLS_DIR.iterdir():
        if not folder.is_dir():
            continue
        for skill_file in folder.glob("*.json"):
            if skill_file.name == "index.json":
                continue
            try:
                data = json.loads(skill_file.read_text(encoding="utf-8"))
                idx["skills"].append({
                    "name": data.get("name", f"{folder.name}/{skill_file.stem}"),
                    "type": data.get("type", folder.name),
                    "tags": data.get("tags", []),
                    "language": data.get("language", "ar"),
                    "uses": data.get("uses", 0),
                    "last_used": data.get("last_used"),
                    "from_real": data.get("from_real", False),
                    "path": str(skill_file.relative_to(WORKSPACE)),
                })
            except (json.JSONDecodeError, KeyError):
                pass
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    return idx


def main():
    dec_items = _load_decisions()
    sent_items = _load_sent_state()
    all_items = dec_items + sent_items

    print(f"Found {len(dec_items)} decisions + {len(sent_items)} sent-state items")
    written = 0
    skipped = 0

    for item in all_items:
        action = item.get("action", "send")
        i_type = item.get("type", "email_followup")
        body = item.get("body", "")
        if not body or action != "send":
            skipped += 1
            continue
        if i_type not in TYPE_MAP:
            skipped += 1
            continue

        cfg = TYPE_MAP.get(i_type)
        cleaned = _clean_body(body, i_type)
        path = _write_skill(
            i_type, cleaned,
            cfg["template_file"], cfg["tags"], cfg["sign"]
        )
        print(f"  Wrote {path.name}")
        written += 1

    idx = _rebuild_index()
    total = len(idx["skills"])
    real_count = sum(1 for s in idx["skills"] if s.get("from_real"))
    print(f"\nIndex rebuilt: {total} skills total, {real_count} from real sends, {skipped} skipped")
    print(f"Index: {INDEX_PATH}")


if __name__ == "__main__":
    main()