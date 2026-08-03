"""
hunt.py — Daily freelance hunter for Alaa Fathi (AI-in-the-loop architecture).

Two fronts, three phases:
  GATHER:  script finds opportunities, reads inbox — writes raw data to hunt_context.md
  DECIDE:  YOU (with the AI agent in chat) read hunt_context.md, write decisions
           to hunt_decisions.md (your personalized replies, bids, follow-ups)
  EXECUTE: script reads hunt_decisions.md, sends emails / posts / submits

The AI agent (me) writes the content with full context. The script is the
"hands" — it gathers data and executes your decisions. You supervise.

Two fronts:
  Arabic:   Mostaql + Nafezly (bids in Arabic)
  Foreign:  n8n Community + Upwork + direct email (English replies + follow-ups)

Usage:
  python hunt.py --gather           # GATHER phase (raw data → hunt_context.md)
  python hunt.py --gather --no-ai   # GATHER without AI suggestions
  python hunt.py --replies          # GATHER, replies only
  python hunt.py --outreach         # GATHER, new opportunities only
  python hunt.py --execute          # EXECUTE phase (reads hunt_decisions.md, sends)
  python hunt.py --auto             # legacy: COLLECT + SEND in one run (uses Groq)
  python hunt.py --open-context     # open hunt_context.md
  python hunt.py --open-decisions   # open hunt_decisions.md
  python hunt.py --status           # show queue state, daily limits, last run

Files:
  hunt_state.json       — sent bids, replied IDs, daily counters
  hunt_context.md       — raw data from latest GATHER (you read this)
  hunt_decisions.md     — your decisions (you write this, script sends it)
  hunter_drafts.md      — legacy: AI-generated drafts from --auto mode
  hunter.log            — full log
  hunter_screenshots/   — Playwright screenshots

Setup (one-time):
  1. Engine running at 127.0.0.1:5000 (auto-starts on login)
  2. GMAIL_APP_PASSWORD env var (for Gmail IMAP)
  3. GROQ_API_KEY in C:\\Users\\A\\Desktop\\AI-OS-Agent\\.env (for AI in --auto mode)
  4. Logged in to Mostaql + Nafezly + n8n Community via Playwright (saves session)
"""

import json
import os
import re
import sys
import time
import imaplib
import email
import smtplib
import subprocess
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ==================== Configuration ====================
WORKSPACE = Path(r"C:\Users\A\Desktop\Money")
AI_AGENT_DIR = Path(r"C:\Users\A\Desktop\AI-OS-Agent")
STATE_FILE = WORKSPACE / "hunt_state.json"
DRAFTS_FILE = WORKSPACE / "hunter_drafts.md"
LOG_FILE = WORKSPACE / "hunter.log"
SCREENSHOTS = WORKSPACE / "hunter_screenshots"
SCREENSHOTS.mkdir(exist_ok=True)
SENT_LOG = WORKSPACE / "hunter_sent.log"

EMAIL = "salim.muhammad.work@gmail.com"
NAME_AR = "سليم محمد"
NAME_EN = "Salim Muhammad"
HOURLY_RATE = "$15/hr"
INDUSTRY = "Computer Software"
INDUSTRY_AR = "تكنولوجيا المعلومات"

GMAIL_RECIPIENTS = [
    "info@zyimmo.de",
    "careers@asiacruit.com",
    "info@s-e.lt",
    "n8nera@gmail.com",
    "wayne@nocodecreative.io",
    "folafoluwaolaneye@gmail.com",
]

DAILY_LIMITS = {
    "replies": 10,
    "followups": 5,
    "mostaql_bids": 3,
    "nafezly_bids": 3,
    "forum_replies": 3,
    "upwork_applies": 5,
}

THREADS = [
    {
        "key": "mkitplug",
        "url": "https://community.n8n.io/t/i-built-a-free-figma-plugin-that-sends-design-data-to-n8n-looking-for-agencies-to-build-real-workflows-with/297696",
        "draft": "Application_N8N_Community_mkitplug.md",
        "label": "mkitplug (Michael) — Figma plugin",
    },
    {
        "key": "easybits",
        "url": "https://community.n8n.io/t/recruiter-friend-was-losing-half-her-day-to-manually-typing-linkedin-profiles-into-a-sheet-built-her-a-workflow-that-ends-the-retyping/297970",
        "draft": "Application_N8N_Community_easybits.md",
        "label": "easybits — Recruiter LinkedIn workflow",
    },
    {
        "key": "Doru_Gradinaru",
        "url": "https://community.n8n.io/t/built-an-importable-guard-workflow-for-costly-ai-tool-calls-looking-for-n8n-feedback/296302",
        "draft": "Application_N8N_Community_Doru_Gradinaru.md",
        "label": "Doru_Gradinaru — Guard workflow",
    },
]

# ==================== AI Client (keyhub) ====================
# Uses keyhub_client.py which routes through the engine's /proxy/ai endpoint.
# Falls back to direct Groq if the engine is unreachable.
AI_AVAILABLE = False
client = None
AI_MODEL = None

try:
    sys.path.insert(0, str(WORKSPACE))
    import keyhub_client
    # Probe to see if engine is up
    if keyhub_client._engine_alive():
        AI_AVAILABLE = True
        AI_MODEL = os.environ.get("AI_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    else:
        # Fall back to direct Groq
        from dotenv import load_dotenv
        load_dotenv(AI_AGENT_DIR / ".env")
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        if GROQ_API_KEY:
            from openai import OpenAI
            client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
            AI_MODEL = os.getenv("AI_OS_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
            AI_AVAILABLE = True
except Exception as e:
    print(f"  [WARN] AI init failed: {e}")


# ==================== Skills Library (local) ====================
# Skills are reusable templates stored in Money/skills/. hunt.py tries
# a matching skill first; if no good match, it falls back to AI generation.
# Skills cut AI calls in half for repeat task types (bids, follow-ups, replies).
SKILLS_AVAILABLE = False
skill_manager = None
SKILL_TRY_FIRST = os.environ.get("HUNT_SKILL_FIRST", "1") == "1"

try:
    sys.path.insert(0, str(WORKSPACE / "skills"))
    from manager import find_best_skill, apply_skill, list_skills, get_skill, save_skill, learn_from_sent
    SKILLS_AVAILABLE = True
except Exception as e:
    print(f"  [WARN] Skills init failed: {e}")


def try_skill(skill_type, context_keywords, variables, use_ai_polish=True):
    """Try to fill a skill template. Returns text or None.

    Set HUNT_SKILL_FIRST=0 to disable (force AI generation).
    """
    if not SKILLS_AVAILABLE or not SKILL_TRY_FIRST:
        return None
    try:
        skill = find_best_skill(skill_type, context_keywords)
        if not skill:
            return None
        if not skill.get("template"):
            return None
        out = apply_skill(skill, variables or {}, use_ai_polish=use_ai_polish)
        if out:
            log(f"  [SKILL] Used '{skill['name']}' (v{skill.get('version', 1)})")
        return out
    except Exception as e:
        log(f"  [SKILL ERROR] {e}")
        return None


# ==================== State Management ====================
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {
        "last_run": None,
        "sent_emails": [],
        "sent_bids": [],
        "sent_replies": [],
        "sent_followups": [],
        "replied_ids": [],
        "daily_counters": {},
        "completed_phases": [],
    }


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


_LEARN_COUNTER = {"n": 0}


def record_learned_skill(item, log_label="LEARN"):
    """Save a sent item as a learned skill in skills/learning/.

    Hooked into send_decisions() so every successful send becomes a
    reusable template. To disable: set HUNT_AUTO_LEARN=0 in env.
    """
    if os.environ.get("HUNT_AUTO_LEARN", "1") != "1":
        return None
    if not SKILLS_AVAILABLE:
        return None
    try:
        draft = learn_from_sent(item)
        if not draft:
            return None
        original_name = draft.get("name", "")
        if not original_name.startswith("learning/"):
            draft["name"] = "learning/" + original_name
        # Ensure unique filename even when many items land in the same second
        _LEARN_COUNTER["n"] += 1
        body_hash = abs(hash(item.get("body", ""))) % 100000
        draft["name"] = f"{draft['name']}_{_LEARN_COUNTER['n']}_{body_hash}"
        draft["source"] = {
            "to": item.get("to", ""),
            "subject": item.get("subject", ""),
            "type": item.get("type", ""),
            "company": item.get("company", ""),
            "platform": item.get("platform", ""),
            "learned_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
        if save_skill(draft["name"], draft):
            log(f"  [{log_label}] Saved as skill: {draft['name']}")
            return draft["name"]
    except Exception as e:
        log(f"  [{log_label} ERROR] {e}")
    return None


# ==================== Logging ====================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def banner(text):
    bar = "=" * 60
    log(bar)
    log(f"  {text}")
    log(bar)


def can_send_today(state, key):
    """Check if we can send more of this type today (uses daily_counters)."""
    limit = DAILY_LIMITS.get(key, 99)
    today = datetime.now().strftime("%Y-%m-%d")
    counters = state.setdefault("daily_counters", {})
    if counters.get("date") != today:
        counters["date"] = today
        counters["counts"] = {}
    return counters["counts"].get(key, 0) < limit


def increment_counter(state, key):
    today = datetime.now().strftime("%Y-%m-%d")
    counters = state.setdefault("daily_counters", {})
    if counters.get("date") != today:
        counters["date"] = today
        counters["counts"] = {}
    counters["counts"][key] = counters["counts"].get(key, 0) + 1


# ==================== AI Generation ====================
AI_CALLS = 0
AI_MAX_CALLS = 25


def ai_generate(prompt, system=None, max_tokens=1024):
    global AI_CALLS
    if not AI_AVAILABLE:
        return None
    if AI_CALLS >= AI_MAX_CALLS:
        log(f"  [AI LIMIT] {AI_MAX_CALLS} calls reached, skipping")
        return None
    if system is None:
        system = (
            f"You are {NAME_EN}, an AI Automation Engineer and freelance consultant "
            "You write in clear, professional English or Arabic as needed. "
            "Be concise, results-oriented, and friendly. Never mention being an AI. "
            "Always sign off as Alaa."
        )

    # Try keyhub (engine) first
    try:
        import keyhub_client
        result = keyhub_client.ai_generate(
            prompt, system=system, max_tokens=max_tokens,
            model=AI_MODEL, caller="hunt.py"
        )
        if result:
            AI_CALLS += 1
            return result
    except Exception as e:
        log(f"  [KEYHUB ERROR] {e}")

    # Fallback to direct Groq
    if client is not None:
        try:
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.4,
            )
            AI_CALLS += 1
            return response.choices[0].message.content.strip()
        except Exception as e:
            log(f"  [GROQ ERROR] {e}")
    return None


# ==================== Email Helpers ====================
def decode_header_str(s):
    if not s:
        return ""
    parts = decode_header(s)
    out = []
    for p in parts:
        if isinstance(p[0], bytes):
            out.append(p[0].decode(p[1] or "utf-8", errors="replace"))
        else:
            out.append(str(p[0]))
    return "".join(out)


def notify_engine(item_type, recipient, subject, body, source=""):
    """Fire-and-forget: notify the AI engine that an item was sent.

    The engine logs the send for stats + learns from successful patterns.
    Fails silently — never blocks the local send.
    """
    try:
        engine_url = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")
        requests.post(
            f"{engine_url}/api/hunt_event",
            json={
                "type": item_type,
                "recipient": recipient,
                "subject": subject,
                "body": body[:500] if body else "",
                "source": source,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            timeout=5,
        )
    except Exception as e:
        log(f"  [engine notify failed] {e}")


def send_email_smtp(to, subject, body):
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if not pw:
        log("  [SMTP SKIP] GMAIL_APP_PASSWORD not set")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, pw)
            server.sendmail(EMAIL, to, msg.as_string())
        log(f"  [SENT] {to}: {subject[:60]}")
        with SENT_LOG.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] TO={to} SUBJECT={subject}\n")
        return True
    except Exception as e:
        log(f"  [SMTP ERROR] {e}")
        return False


# ==================== PHASE: Gmail Replies ====================
def get_replies_from_recipients(days_back=14):
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if not pw:
        log("  [SKIP] GMAIL_APP_PASSWORD not set — cannot check Gmail")
        return []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, pw)
        mail.select("inbox")
        since = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        all_ids = set()
        for r in GMAIL_RECIPIENTS:
            status, data = mail.search(None, f'FROM "{r}" SINCE {since}')
            if status == "OK" and data and data[0]:
                all_ids.update(data[0].split())
        replies = []
        for num in sorted(all_ids):
            status, msg_data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode(errors="replace")
                        except Exception:
                            body = str(part.get_payload())
                        break
            else:
                try:
                    body = msg.get_payload(decode=True).decode(errors="replace")
                except Exception:
                    body = str(msg.get_payload())
            replies.append({
                "from": decode_header_str(msg.get("From", "")),
                "subject": decode_header_str(msg.get("Subject", "")),
                "date": msg.get("Date", ""),
                "body": body[:2500],
                "message_id": num.decode(),
            })
        mail.logout()
        return replies
    except Exception as e:
        log(f"  [GMAIL ERROR] {e}")
        return []


def generate_email_reply(email_data):
    skill_text = try_skill(
        "email_reply",
        context_keywords=["english", "professional", "client", "reply"],
        variables={
            "client_name": email_data.get("from", "").split("<")[0].strip() or "there",
            "systems": "n8n / OpenAI / Sheets / Slack (stack of the project you sent me)",
        },
        use_ai_polish=AI_AVAILABLE,
    )
    if skill_text:
        return skill_text
    prompt = f"""Generate a professional, concise reply to this email from a potential client.

From: {email_data['from']}
Subject: {email_data['subject']}

Body:
{email_data['body']}

Reply rules:
- From {NAME_EN}, AI Automation Engineer (n8n, Python, OpenAI, workflow automation)
- 3-5 sentences max
- Address their question or interest directly
- Offer a concrete next step (15-min call, demo, or proposal)
- Match the language of the original email
- Sign off as "{NAME_EN}"
- No subject line, just the body

Write only the reply body."""
    return ai_generate(prompt, max_tokens=600)


def phase_replies(state, drafts, auto=False, no_ai=False):
    banner("PHASE: Gmail replies (incoming)")
    replies = get_replies_from_recipients()
    if not replies:
        log("  No replies found.")
        return 0
    log(f"  Found {len(replies)} reply/replies")
    count = 0
    for r in replies:
        if r["message_id"] in state.get("replied_ids", []):
            log(f"  [SKIP] Already replied: {r['subject'][:50]}")
            continue
        if not can_send_today(state, "replies"):
            log("  [LIMIT] Daily reply limit reached")
            break
        log(f"  Drafting reply: {r['subject'][:50]}")
        body = None
        if not no_ai:
            body = generate_email_reply(r)
        if not body:
            log(f"  [INFO] No AI body — raw email will be in context for you to draft")
        item = {
            "type": "email_reply",
            "to": r["from"],
            "from": r["from"],
            "subject": f"Re: {r['subject']}" if not r["subject"].lower().startswith("re:") else r["subject"],
            "date": r.get("date", ""),
            "body": body or r["body"],  # if no AI body, include original for context
            "context": f"In reply to: {r['subject'][:60]}",
        }
        if auto:
            if body and send_email_smtp(item["to"], item["subject"], item["body"]):
                state.setdefault("replied_ids", []).append(r["message_id"])
                increment_counter(state, "replies")
                count += 1
        else:
            drafts.append(item)
            count += 1
    log(f"  Processed {count} replies (auto={auto}, no_ai={no_ai})")
    return count


# ==================== PHASE: Follow-ups ====================
def find_old_applications():
    """Parse Application_Pipeline.md for sent apps > 5 days old, no reply."""
    pipeline_file = WORKSPACE / "Application_Pipeline.md"
    if not pipeline_file.exists():
        return []
    text = pipeline_file.read_text(encoding="utf-8")
    old_apps = []
    today = datetime.now()
    # Match rows like: | 1 | 2026-06-01 | ZY IMMO Capital | info@zyimmo.de | Sent, no reply | 2026-06-08 |
    row_re = re.compile(
        r"\|\s*(\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(\d{4}-\d{2}-\d{2})"
    )
    for m in row_re.finditer(text):
        idx, sent_date, company, contact, status, follow_date = m.groups()
        if "Sent, no reply" not in status and "no reply" not in status.lower():
            continue
        try:
            sent = datetime.strptime(sent_date, "%Y-%m-%d")
        except ValueError:
            continue
        days_old = (today - sent).days
        if days_old >= 5:
            old_apps.append({
                "index": idx.strip(),
                "company": company.strip(),
                "contact": contact.strip(),
                "sent_date": sent_date,
                "days_old": days_old,
            })
    return old_apps


def generate_followup_email(app):
    skill_text = try_skill(
        "email_followup",
        context_keywords=["followup", "english", "cold", "no_reply", "polite"],
        variables={
            "company": app["company"],
            "days_ago": str(app["days_old"]),
        },
        use_ai_polish=AI_AVAILABLE,
    )
    if skill_text:
        return skill_text
    prompt = f"""Generate a short, polite follow-up email for a job application sent {app['days_old']} days ago with no reply.

To: {app['company']} ({app['contact']})
Sent: {app['sent_date']} ({app['days_old']} days ago)

Follow-up rules:
- Subject: "Following up — AI Automation Engineer application"
- 3-4 sentences max
- Brief reminder of what was offered
- Show flexibility on scope/budget
- Offer a small test task to demonstrate value
- Sign off as "{NAME_EN}, AI Automation Engineer"
- No need to re-attach CV

Just the email body."""
    return ai_generate(prompt, max_tokens=400)


def phase_followups(state, drafts, auto=False, no_ai=False):
    banner("PHASE: Follow-ups (5+ day old applications)")
    old = find_old_applications()
    if not old:
        log("  No old applications needing follow-up.")
        return 0
    log(f"  Found {len(old)} old application(s)")
    count = 0
    for app in old:
        if not can_send_today(state, "followups"):
            log("  [LIMIT] Daily follow-up limit reached")
            break
        already = f"{app['contact']}@{app['sent_date']}" in state.get("sent_followups", [])
        if already:
            log(f"  [SKIP] Already followed up: {app['company']}")
            continue
        log(f"  Drafting follow-up: {app['company']} ({app['days_old']}d old)")
        body = None
        if not no_ai:
            body = generate_followup_email(app)
        if not body:
            log(f"  [INFO] No AI body — meta is in context for you to draft")
        item = {
            "type": "email_followup",
            "to": app["contact"],
            "company": app["company"],
            "contact": app["contact"],
            "sent_date": app["sent_date"],
            "days_old": app["days_old"],
            "subject": f"Following up — AI Automation Engineer application",
            "body": body or f"[Write a follow-up for {app['company']} here]",
            "context": f"Follow-up #{app['index']}: {app['company']} (sent {app['sent_date']})",
        }
        if auto:
            if body and send_email_smtp(item["to"], item["subject"], item["body"]):
                state.setdefault("sent_followups", []).append(
                    f"{app['contact']}@{app['sent_date']}"
                )
                increment_counter(state, "followups")
                count += 1
        else:
            drafts.append(item)
            count += 1
    log(f"  Processed {count} follow-ups (auto={auto}, no_ai={no_ai})")
    return count


# ==================== PHASE: Arabic Bids (Mostaql + Nafezly) ====================
def generate_arabic_bid(project_title, project_desc, platform="mostaql"):
    """Generate Arabic bid using skill template + AI personalization."""
    skill_text = try_skill(
        "arabic_bid",
        context_keywords=[platform, "n8n", "automation", "freelance", "arabic"],
        variables={
            "n_workflows": "10",
            "duration": "5",
            "budget": "100",
        },
        use_ai_polish=AI_AVAILABLE,
    )
    if skill_text:
        return skill_text
    template = """السلام عليكم،

شكرًا على نشر المشروع. قرأت التفاصيل وأعتقد أستطيع تقديم حل عملي ومُجرَّب.

خبرتي:
بنيت أكثر من [X] workflow في n8n تربط بين OpenAI و Google Sheets و Slack و Airtable. عندي مثال حي: pipeline لتأهيل العملاء المحتملين يقرأ من Google Sheet ويستدعي OpenAI ويكتب النتائج في Sheet جديدة ويرسل Slack notification.

كيف سأنفّذ مشروعك:
1. نتفق على المتطلبات بالتفصيل في المحادثة
2. أحدد العقد (nodes) المطلوبة في n8n
3. أسلّم workflow جاهز للاختبار خلال 2-3 أيام
4. نكرّر التعديلات حتى رضاك
5. تسليم نهائي مع توثيق مختصر

المدة: [X] أيام
الميزانية: [X]$

أمثلة من أعمالي متاحة في معرض أعمالي.

لو عندك أي سؤال، أنا في الخدمة.

تحياتي،
علاء فتحي"""

    if AI_AVAILABLE:
        prompt = f"""Personalize this Arabic bid template for a specific project on {platform}.

Project title: {project_title}

Project description:
{project_desc[:1500]}

Template to personalize (in Arabic):
{template}

Rules:
- Keep the السلام عليكم opening
- Reference the specific project (mention 1-2 details from the description)
- Replace [X] placeholders with realistic numbers
- Add 1 specific line about how you'd solve THEIR problem
- Keep total length 250-400 words
- Sign as علاء فتحي
- Use formal Arabic (فصحى)
- Output ONLY the bid body, no extra commentary
"""
        result = ai_generate(prompt, max_tokens=900)
        if result:
            return result
    return template


def get_arabic_browser_page(context, platform_url):
    """Open the projects page, return page object (assumes user is logged in)."""
    from playwright.sync_api import sync_playwright
    browser = context.browser
    page = context.new_page()
    page.goto(platform_url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    return page


def phase_arabic_bids(state, drafts, auto=False, context=None, no_ai=False):
    """Browse Mostaql + Nafezly, find projects, generate Arabic bids."""
    banner("PHASE: Arabic platform bids (Mostaql + Nafezly)")

    if not context:
        log("  [SKIP] No browser context provided (run in non-auto mode to skip)")
        return 0

    if not AI_AVAILABLE:
        log("  [WARN] AI not available — bids will use template only")

    platforms = [
        {
            "name": "mostaql",
            "url": "https://mostaql.com/projects/ai-machine-learning",
            "key": "mostaql_bids",
            "label": "Mostaql (مستقل)",
        },
        {
            "name": "nafezly",
            "url": "https://nafezly.com/projects",
            "key": "nafezly_bids",
            "label": "Nafezly (نفذلي)",
        },
    ]

    total_count = 0
    for plat in platforms:
        log(f"\n  --- {plat['label']} ---")
        if not can_send_today(state, plat["key"]):
            log(f"  [LIMIT] Daily {plat['key']} limit reached")
            continue

        try:
            page = context.new_page()
            page.goto(plat["url"], wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            shot = SCREENSHOTS / f"{plat['name']}_projects.png"
            page.screenshot(path=str(shot))
            log(f"  Screenshot: {shot.name}")

            # Login check
            try:
                sign_in = page.get_by_role("link", name=re.compile("تسجيل الدخول|Sign In|دخول", re.I))
                if sign_in.count() > 0:
                    log(f"  ⚠ Not logged in to {plat['name']}. Login in browser, then re-run.")
                    page.close()
                    continue
            except Exception:
                pass

            # Extract project links
            project_links = []
            for sel in ["a[href*='/project/']", "a[href*='/jobs/']"]:
                try:
                    anchors = page.locator(sel).all()
                    for a in anchors[:10]:
                        href = a.get_attribute("href")
                        if href and "/project/" in href and href not in project_links:
                            if not href.startswith("http"):
                                href = f"https://{plat['name']}.com" + href
                            project_links.append(href)
                except Exception:
                    pass
            log(f"  Found {len(project_links)} project links")

            # Visit top 3-5 to extract details
            count = 0
            for link in project_links[:5]:
                if not can_send_today(state, plat["key"]):
                    break
                if f"{plat['name']}:{link}" in state.get("sent_bids", []):
                    log(f"  [SKIP] Already bid on: {link[:60]}")
                    continue
                try:
                    page2 = context.new_page()
                    page2.goto(link, wait_until="domcontentloaded")
                    page2.wait_for_timeout(2000)
                    title = "(no title)"
                    desc = ""
                    try:
                        title = page2.locator("h1").first.text_content(timeout=5000) or title
                    except Exception:
                        pass
                    try:
                        desc = page2.locator("article, .project-description, .description, p").first.text_content(timeout=5000) or ""
                        if not desc:
                            desc = page2.locator("body").first.text_content(timeout=3000) or ""
                    except Exception:
                        pass
                    page2.close()
                    log(f"  Project: {title[:60]}")
                    bid = None
                    if not no_ai:
                        log(f"  Generating Arabic bid...")
                        bid = generate_arabic_bid(title.strip(), desc[:1500].strip(), plat["name"])
                    item = {
                        "type": f"{plat['name']}_bid",
                        "platform": plat["name"],
                        "project_url": link,
                        "project_title": title.strip(),
                        "body": bid or "[Write Arabic bid here based on project description]",
                        "context": f"Bid on {plat['label']}: {title[:60]}",
                    }
                    if auto:
                        log(f"  [AUTO] Would submit bid for: {link[:60]}")
                        log(f"  [INFO] Auto-submit not implemented in v1 — saved as draft instead")
                        drafts.append(item)
                        state.setdefault("sent_bids", []).append(f"{plat['name']}:{link}")
                        increment_counter(state, plat["key"])
                    else:
                        drafts.append(item)
                        log(f"  Drafted bid for: {link[:60]}")
                    count += 1
                except Exception as e:
                    log(f"  [ERROR] Project {link}: {e}")
                    continue

            page.close()
            total_count += count
            log(f"  {plat['label']}: {count} bid(s) drafted")
        except Exception as e:
            log(f"  [ERROR] {plat['label']}: {e}")
            import traceback
            traceback.print_exc()

    log(f"\n  Total Arabic bids: {total_count}")
    return total_count


# ==================== PHASE: n8n Community Forum ====================
def extract_reply_from_md(md_path):
    text = Path(md_path).read_text(encoding="utf-8")
    match = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def phase_n8n_forum(state, drafts, auto=False, context=None, no_ai=False):
    banner("PHASE: n8n Community forum replies")
    count = 0
    for thread in THREADS:
        if not can_send_today(state, "forum_replies"):
            log("  [LIMIT] Daily forum reply limit reached")
            break
        if f"forum:{thread['key']}" in state.get("sent_bids", []):
            log(f"  [SKIP] Already posted: {thread['key']}")
            continue

        md = WORKSPACE / thread["draft"]
        if not md.exists():
            log(f"  [SKIP] Draft not found: {md.name}")
            continue
        reply_text = extract_reply_from_md(md)
        if not reply_text:
            log(f"  [SKIP] No code block in {md.name}")
            continue

        item = {
            "type": "forum_reply",
            "thread_key": thread["key"],
            "thread_url": thread["url"],
            "body": reply_text,
            "context": f"Reply to: {thread['label']}",
        }
        if auto and context:
            try:
                page = context.new_page()
                page.goto(thread["url"], wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
                if not ensure_logged_in(
                    page,
                    "n8n Community",
                    "https://community.n8n.io/login",
                    "button:has-text('Reply')",
                ):
                    log(f"  [ERROR] Not logged in to n8n Community — skipping")
                    drafts.append(item)
                    continue
                try:
                    reply_btn = page.locator("button:has-text('Reply')").first
                    reply_btn.scroll_into_view_if_needed()
                    reply_btn.click()
                    page.wait_for_timeout(1500)
                    editor = page.locator("textarea.d-editor-input").first
                    editor.wait_for(state="visible", timeout=10000)
                    editor.fill(reply_text)
                    page.wait_for_timeout(500)
                    post_btn = page.locator(
                        "button:has-text('Reply to Topic'), button:has-text('Post Reply')"
                    ).first
                    post_btn.click()
                    page.wait_for_timeout(3000)
                    shot = SCREENSHOTS / f"forum_{thread['key']}_posted.png"
                    page.screenshot(path=str(shot))
                    log(f"  [POSTED] {thread['key']}")
                    state.setdefault("sent_bids", []).append(f"forum:{thread['key']}")
                    increment_counter(state, "forum_replies")
                    count += 1
                except Exception as e:
                    log(f"  [ERROR] Could not auto-post {thread['key']}: {e}")
                    drafts.append(item)
                finally:
                    page.close()
            except Exception as e:
                log(f"  [ERROR] {thread['key']}: {e}")
                drafts.append(item)
        else:
            drafts.append(item)
            log(f"  Drafted forum reply: {thread['key']}")
            count += 1

    log(f"  Processed {count} forum replies (auto={auto}, no_ai={no_ai})")
    return count


# ==================== PHASE: Upwork (if session available) ====================
def phase_upwork(state, drafts, auto=False, context=None):
    banner("PHASE: Upwork job search (if logged in)")
    if not context:
        log("  [SKIP] No browser context")
        return 0
    try:
        page = context.new_page()
        page.goto("https://www.upwork.com/nx/search/jobs/?q=automation%20n8n", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        if "login" in page.url.lower() or "signin" in page.url.lower():
            log("  [SKIP] Not logged in to Upwork. Complete signup first (Upwork_Signup_Steps.md)")
            page.close()
            return 0
        shot = SCREENSHOTS / "upwork_jobs.png"
        page.screenshot(path=str(shot))
        log(f"  Screenshot: {shot.name}")
        log(f"  [INFO] Review jobs in browser, then run --send to apply")
        page.close()
    except Exception as e:
        log(f"  [ERROR] {e}")
    return 0


# ==================== Drafts Aggregator ====================
def save_drafts(drafts):
    """Write all drafts to hunter_drafts.md for user review."""
    if not drafts:
        log("  No drafts to save.")
        return

    header = (
        f"# Hunter Drafts — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"**Total items:** {len(drafts)}\n\n"
        "Review each item below. To approve all, run: `python hunt.py --send`\n"
        "To approve selectively, edit this file and remove items you don't want sent.\n"
        "Items must start with `## Item N: ...` to be sent.\n\n---\n\n"
    )
    body_parts = [header]
    for i, d in enumerate(drafts, 1):
        section = [f"## Item {i}: {d.get('context', d.get('type', 'Unknown'))}\n"]
        section.append(f"**Type:** `{d.get('type', '')}`\n")
        for k in ("to", "subject", "thread_key", "thread_url", "project_url", "project_title", "platform"):
            if d.get(k):
                section.append(f"**{k.replace('_', ' ').title()}:** {d[k]}\n")
        section.append("\n**Body:**\n\n```\n" + d.get("body", "") + "\n```\n\n---\n\n")
        body_parts.extend(section)

    DRAFTS_FILE.write_text("".join(body_parts), encoding="utf-8")
    log(f"  Drafts saved to: {DRAFTS_FILE}")
    log(f"  Review and run: python hunt.py --send")


def parse_drafts():
    """Parse hunter_drafts.md and return list of approved items."""
    if not DRAFTS_FILE.exists():
        log("  [ERROR] No drafts file found. Run hunt.py first.")
        return []
    text = DRAFTS_FILE.read_text(encoding="utf-8")
    items = []
    # Split on item headers
    parts = re.split(r"^## Item (\d+): (.+)$", text, flags=re.MULTILINE)
    # parts[0] = preamble, then triplets: (num, header, body)
    i = 1
    while i < len(parts):
        num = parts[i]
        header = parts[i + 1]
        body = parts[i + 2] if i + 2 < len(parts) else ""
        item = {"header": header, "body": body}
        # Extract type
        type_m = re.search(r"\*\*Type:\*\*\s*`?(\w+)`?", body)
        if type_m:
            item["type"] = type_m.group(1).strip()
        # Extract to/subject/url from metadata
        for k, key in [("To", "to"), ("Subject", "subject"),
                        ("Thread Url", "thread_url"), ("Project Url", "project_url"),
                        ("Project Title", "project_title"), ("Platform", "platform")]:
            m = re.search(rf"\*\*{k}:\*\*\s*(.+)", body)
            if m:
                item[key] = m.group(1).strip()
        # Extract body content
        body_m = re.search(r"\*\*Body:\*\*\s*\n+```\n(.+?)\n```", body, re.DOTALL)
        if body_m:
            item["body"] = body_m.group(1).strip()
        items.append(item)
        i += 3
    return items


# ==================== SEND Phase ====================
def send_drafts(items, context=None):
    """Execute approved drafts."""
    banner("SEND PHASE: executing approved drafts")
    sent = 0
    failed = 0
    for it in items:
        t = it.get("type", "")
        log(f"\n  → Item: {it.get('header', '?')[:60]} (type={t})")
        try:
            if t in ("email_reply", "email_followup"):
                if send_email_smtp(it.get("to", ""), it.get("subject", ""), it.get("body", "")):
                    sent += 1
                else:
                    failed += 1
            elif t == "forum_reply":
                if context:
                    page = context.new_page()
                    try:
                        page.goto(it.get("thread_url", ""), wait_until="domcontentloaded")
                        page.wait_for_timeout(2000)
                        try:
                            page.get_by_role("button", name=re.compile("Sign In|Log In", re.I))
                        except Exception:
                            pass
                        try:
                            reply_btn = page.locator("button:has-text('Reply')").first
                            reply_btn.click()
                            page.wait_for_timeout(1500)
                            editor = page.locator("textarea.d-editor-input").first
                            editor.fill(it.get("body", ""))
                            page.wait_for_timeout(500)
                            post_btn = page.locator(
                                "button:has-text('Reply to Topic'), button:has-text('Post Reply')"
                            ).first
                            post_btn.click()
                            page.wait_for_timeout(3000)
                            log(f"  [POSTED] Forum reply: {it.get('thread_url', '')[:60]}")
                            sent += 1
                        except Exception as e:
                            log(f"  [ERROR] Forum post failed: {e}")
                            failed += 1
                    finally:
                        page.close()
                else:
                    log(f"  [SKIP] No browser context for forum post")
                    failed += 1
            elif t in ("mostaql_bid", "nafezly_bid"):
                if context:
                    log(f"  [INFO] Auto-submit for Arabic bids is interactive — please submit manually")
                    log(f"  URL: {it.get('project_url', '')}")
                    log(f"  Bid body saved in drafts file")
                failed += 1
            else:
                log(f"  [SKIP] Unknown type: {t}")
                failed += 1
        except Exception as e:
            log(f"  [ERROR] {e}")
            failed += 1

    log(f"\n  SEND complete: {sent} sent, {failed} failed")
    return sent, failed


# ==================== Main Orchestrator ====================
def run_collect(args, state, drafts):
    """Run all COLLECT phases."""
    banner(f"HUNT.PY — COLLECT PHASE ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    log(f"  Already completed today: {list(state.get('daily_counters', {}).get('counts', {}).keys())}")
    log(f"  AI available: {AI_AVAILABLE} (calls used: {AI_CALLS}/{AI_MAX_CALLS})")

    # Initialize browser if needed for any phase
    context = None
    pw = None
    if not args.replies_only:
        try:
            pw, context = launch_browser(args.brave_profile)

            # Phase: Gmail replies
            if not args.outreach:
                phase_replies(state, drafts, auto=False, no_ai=args.no_ai)

            # Phase: Follow-ups
            if not args.outreach:
                phase_followups(state, drafts, auto=False, no_ai=args.no_ai)

            # Phase: Arabic bids
            if not args.replies:
                phase_arabic_bids(state, drafts, auto=False, context=context, no_ai=args.no_ai)

            # Phase: n8n Community forum
            if not args.replies:
                phase_n8n_forum(state, drafts, auto=False, context=context, no_ai=args.no_ai)

            # Phase: Upwork (informational)
            if not args.replies:
                phase_upwork(state, drafts, auto=False, context=context)

            context.close()
            if pw:
                pw.stop()
        except ImportError:
            log("  [ERROR] Playwright not installed")
        except Exception as e:
            log(f"  [BROWSER ERROR] {e}")
            import traceback
            traceback.print_exc()

    # Save drafts
    if drafts:
        save_drafts(drafts)
        log(f"\n  >>> Next step: review {DRAFTS_FILE.name}, then run: python hunt.py --send")
    else:
        log("\n  No new drafts to send. Check logs for details.")


def run_send(args, state):
    """Run SEND phase — read approved drafts and execute."""
    banner(f"HUNT.PY — SEND PHASE ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    items = parse_drafts()
    if not items:
        log("  No drafts to send.")
        return
    log(f"  Found {len(items)} item(s) in {DRAFTS_FILE.name}")

    context = None
    needs_browser = any(it.get("type") == "forum_reply" for it in items)
    if needs_browser:
        try:
            pw, context = launch_browser(args.brave_profile)
            send_drafts(items, context=context)
            context.close()
            pw.stop()
        except Exception as e:
            log(f"  [BROWSER ERROR] {e}")
            send_drafts(items, context=None)
    else:
        send_drafts(items, context=None)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hunt.py — Daily freelance hunter")
    parser.add_argument("--send", action="store_true", help="Send approved drafts")
    parser.add_argument("--replies", action="store_true", help="Replies only")
    parser.add_argument("--outreach", action="store_true", help="New outreach only")
    parser.add_argument("--auto", action="store_true", help="Auto-send without review (risky)")
    parser.add_argument("--open-drafts", action="store_true", help="Open drafts file")
    args = parser.parse_args()

    if args.open_drafts:
        if DRAFTS_FILE.exists():
            os.startfile(str(DRAFTS_FILE))
            log(f"Opened: {DRAFTS_FILE}")
        else:
            log("No drafts file yet.")
        return

    state = load_state()
    state["last_run"] = datetime.now().isoformat()
    drafts = []

    if args.send:
        run_send(args, state)
    else:
        # Collect phase
        run_collect(args, state, drafts)

    state["last_run"] = datetime.now().isoformat()
    save_state(state)
    log(f"\n  State saved to: {STATE_FILE}")
    log(f"  Log file: {LOG_FILE}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="hunt.py — AI-in-the-loop freelance hunter")
    parser.add_argument("--gather", action="store_true",
                        help="GATHER phase: collect raw data, write hunt_context.md")
    parser.add_argument("--execute", action="store_true",
                        help="EXECUTE phase: read hunt_decisions.md and send")
    parser.add_argument("--send", action="store_true",
                        help="[legacy] Same as --execute, reads hunter_drafts.md")
    parser.add_argument("--replies", action="store_true", help="Gather, replies only")
    parser.add_argument("--outreach", action="store_true", help="Gather, new opportunities only")
    parser.add_argument("--no-ai", action="store_true",
                        help="GATHER without Groq AI (raw data only, faster)")
    parser.add_argument("--auto", action="store_true",
                        help="[legacy] AI-generated + auto-send (skip review, risky)")
    parser.add_argument("--open-context", action="store_true", help="Open hunt_context.md")
    parser.add_argument("--open-decisions", action="store_true", help="Open hunt_decisions.md")
    parser.add_argument("--open-drafts", action="store_true",
                        help="[legacy] Open hunter_drafts.md")
    parser.add_argument("--status", action="store_true", help="Show queue state + daily limits")
    parser.add_argument("--learn", action="store_true",
                        help="LEARN phase: convert sent items (from hunt_decisions.md) "
                             "into reusable skills in skills/learning/")
    parser.add_argument("--brave-profile", action="store_true",
                        help="Use your Brave browser profile (must close Brave first). "
                             "Useful when you're already logged in to the target site in Brave.")
    args = parser.parse_args()

    # File open commands
    if args.open_context:
        _open_file(CONTEXT_FILE, "hunt_context.md")
        return
    if args.open_decisions:
        _open_file(DECISIONS_FILE, "hunt_decisions.md")
        return
    if args.open_drafts:
        _open_file(DRAFTS_FILE, "hunter_drafts.md (legacy)")
        return
    if args.status:
        show_status()
        return

    state = load_state()
    state["last_run"] = datetime.now().isoformat()

    if args.execute or args.send:
        run_execute(args, state)
    elif args.learn:
        run_learn(state)
    elif args.gather or args.replies or args.outreach:
        run_gather(args, state)
    elif args.auto:
        log("  [LEGACY] --auto mode: AI-generates content + sends in one run")
        drafts = []
        run_collect(args, state, drafts)
        if drafts:
            send_drafts_items(drafts, context=None)
    else:
        # No mode specified — show help
        log("  hunt.py — AI-in-the-loop freelance hunter")
        log("")
        log("  Quick start:")
        log("    1. python hunt.py --gather          # find opportunities")
        log("    2. [read hunt_context.md, write hunt_decisions.md in chat]")
        log("    3. python hunt.py --execute         # send your decisions")
        log("")
        log("  Other commands:")
        log("    --status         show state + daily limits")
        log("    --replies        gather replies only")
        log("    --outreach       gather new opportunities only")
        log("    --no-ai          gather without AI (raw data, faster)")
        log("    --auto           AI-generate + send (skip review)")
        log("    --learn          turn sent items into reusable skills")
        log("    --open-context   open hunt_context.md")
        log("    --open-decisions open hunt_decisions.md")
        log("    --send           [legacy] same as --execute")
        return

    state["last_run"] = datetime.now().isoformat()
    save_state(state)
    log(f"\n  State saved to: {STATE_FILE}")
    log(f"  Log file: {LOG_FILE}")


# ==================== New: GATHER/EXECUTE Workflow ====================
CONTEXT_FILE = WORKSPACE / "hunt_context.md"
DECISIONS_FILE = WORKSPACE / "hunt_decisions.md"
USER_DATA_DIR = WORKSPACE / ".playwright_userdata"
USER_DATA_DIR.mkdir(exist_ok=True)


def launch_browser(use_brave_profile=False):
    """Launch Playwright with PERSISTENT context.

    Cookies, localStorage, and session data are saved to USER_DATA_DIR
    so login state persists across hunt.py runs.

    If use_brave_profile=True, uses the user's Brave browser profile
    directly (must close Brave first). Useful when the user is already
    logged in to the target platform in Brave.

    Returns (playwright_instance, browser_context).
    Call `context.close()` to close the browser when done.
    """
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    if use_brave_profile:
        user_data = Path(r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data")
        exe = Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
        if exe.exists():
            log(f"  Using Brave profile: {user_data}")
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(user_data),
                executable_path=str(exe),
                headless=False,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
                viewport={"width": 1366, "height": 768},
            )
            return pw, context
        log(f"  [WARN] Brave not found at {exe}, falling back to Playwright Chromium")
    context = pw.chromium.launch_persistent_context(
        user_data_dir=str(USER_DATA_DIR),
        headless=False,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
        viewport={"width": 1366, "height": 768},
    )
    return pw, context


def ensure_logged_in(page, platform_name, login_url, logged_in_indicator, max_wait=300):
    """Check if user is logged in to a platform; wait if not.

    Args:
        page: Playwright page (already navigated)
        platform_name: Display name (e.g. "n8n Community")
        login_url: URL to navigate to for login
        logged_in_indicator: Selector that exists ONLY when logged in
                            (e.g. button:has-text('Reply'))
        max_wait: seconds to wait for user to log in (default 90)

    Returns True if logged in, False if timeout.
    """
    # First quick check
    try:
        if page.locator(logged_in_indicator).count() > 0:
            return True
    except Exception:
        pass

    log(f"  ⚠ Not logged in to {platform_name}")
    log(f"  Opening login page in browser window...")
    log(f"")
    log(f"  {'='*56}")
    log(f"  >>> PLEASE LOG IN to {platform_name} now")
    log(f"  >>> A browser window has opened with the login page")
    log(f"  >>> After login, this script will continue automatically")
    log(f"  >>> You have {max_wait} seconds")
    log(f"  {'='*56}")
    log(f"")
    page.goto(login_url, wait_until="domcontentloaded")

    # Wait for login, checking every 5 seconds
    import time as _time
    start = _time.time()
    check_interval = 5
    next_check = start
    while _time.time() - start < max_wait:
        _time.sleep(1)
        if _time.time() >= next_check:
            elapsed = int(_time.time() - start)
            remaining = max_wait - elapsed
            try:
                if page.locator(logged_in_indicator).count() > 0:
                    log(f"  ✓ Login detected after {elapsed}s — continuing")
                    return True
            except Exception:
                pass
            if remaining > 0:
                log(f"  ... waiting for login ({remaining}s remaining)")
            next_check = _time.time() + check_interval

    log(f"  ✗ Timeout ({max_wait}s) — not logged in")
    return False


def _open_file(path, label):
    if path.exists():
        os.startfile(str(path))
        log(f"Opened: {label} -> {path}")
    else:
        log(f"  File does not exist yet: {path}")
        log(f"  Run 'python hunt.py --gather' first to create it.")


def show_status():
    banner("HUNT.PY STATUS")
    state = load_state()
    print(f"  Last run:           {state.get('last_run', 'never')}")
    print(f"  Sent emails:        {len(state.get('sent_emails', []))}")
    print(f"  Sent bids:          {len(state.get('sent_bids', []))}")
    print(f"  Sent replies:       {len(state.get('sent_replies', []))}")
    print(f"  Sent followups:     {len(state.get('sent_followups', []))}")
    print(f"  Replied IDs:        {len(state.get('replied_ids', []))}")
    print()
    print(f"  Daily counters ({state.get('daily_counters', {}).get('date', 'none')}):")
    for k, v in state.get("daily_counters", {}).get("counts", {}).items():
        limit = DAILY_LIMITS.get(k, "?")
        print(f"    {k:20s} {v}/{limit}")
    print()
    print(f"  Files:")
    for f, label in [
        (CONTEXT_FILE, "context (GATHER output)"),
        (DECISIONS_FILE, "decisions (you write this)"),
        (DRAFTS_FILE, "drafts (legacy AI-generated)"),
        (STATE_FILE, "state"),
        (LOG_FILE, "log"),
    ]:
        exists = "[X]" if f.exists() else "[ ]"
        size = f.stat().st_size if f.exists() else 0
        print(f"    {exists} {label:30s} {f.name} ({size} bytes)")


def write_context_file(items, today):
    """Write raw data to hunt_context.md for the AI to read and decide on."""
    if not items:
        log("  No items to write to context file.")
        return

    sections = [
        f"# Hunt Context — {today}",
        "",
        f"**Total items found:** {len(items)}",
        "",
        "Read each item below. In chat, write your decisions to `hunt_decisions.md`",
        "and run `python hunt.py --execute` to send them.",
        "",
        "**Decision file format:**",
        "",
        "```",
        "## DECISION: <item_id>",
        "ACTION: send | skip | edit",
        "TO: <recipient>",
        "SUBJECT: <subject>",
        "BODY:",
        "<your personalized content here>",
        "```",
        "",
        "---",
        "",
    ]

    for i, item in enumerate(items, 1):
        item_id = f"item_{i:02d}"
        item["_id"] = item_id
        sections.append(f"## {item_id}: {item.get('context', item.get('type', 'Unknown'))}")
        sections.append("")
        sections.append(f"**Type:** `{item.get('type', '')}`")
        sections.append(f"**ID:** `{item_id}`")
        for k in ("to", "subject", "from", "thread_key", "thread_url",
                  "project_url", "project_title", "platform", "date",
                  "days_old", "company", "contact", "sent_date"):
            if item.get(k) is not None:
                v = item[k]
                if isinstance(v, str) and len(v) > 200:
                    v = v[:200] + "..."
                sections.append(f"**{k.replace('_', ' ').title()}:** {v}")
        sections.append("")
        if item.get("body"):
            sections.append("**Content (raw / AI-suggested):**")
            sections.append("")
            sections.append("```")
            sections.append(str(item.get("body", "")))
            sections.append("```")
            sections.append("")
        sections.append("---")
        sections.append("")

    CONTEXT_FILE.write_text("\n".join(sections), encoding="utf-8")
    log(f"  Context written: {CONTEXT_FILE} ({len(items)} items)")


def run_gather(args, state):
    """GATHER phase: collect raw data + AI suggestions, write to hunt_context.md."""
    banner(f"HUNT.PY — GATHER PHASE ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    log(f"  AI suggestions: {'ON' if AI_AVAILABLE and not args.no_ai else 'OFF'}")
    log(f"  Mode: {'replies only' if args.replies else 'outreach only' if args.outreach else 'full'}")

    items = []

    # Initialize browser if needed
    context = None
    needs_browser = not args.replies
    if needs_browser:
        try:
            pw, context = launch_browser(args.brave_profile)

            # Collect each phase, passing items list
            if not args.outreach:
                phase_replies(state, items, auto=False, no_ai=args.no_ai)
            if not args.replies:
                phase_followups(state, items, auto=False, no_ai=args.no_ai)
            if not args.replies:
                phase_arabic_bids(state, items, auto=False, context=context, no_ai=args.no_ai)
            if not args.replies:
                phase_n8n_forum(state, items, auto=False, context=context, no_ai=args.no_ai)
            if not args.replies:
                phase_upwork(state, items, auto=False, context=context)

            context.close()
            pw.stop()
        except ImportError:
            log("  [ERROR] Playwright not installed")
        except Exception as e:
            log(f"  [BROWSER ERROR] {e}")
            import traceback
            traceback.print_exc()
    else:
        # Replies-only mode: no browser needed
        phase_replies(state, items, auto=False, no_ai=args.no_ai)

    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_context_file(items, today)

    # Also save raw items as JSON for the script to read
    raw_file = WORKSPACE / "hunt_raw.json"
    raw_file.write_text(
        json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log(f"  Raw data: {raw_file}")

    if items:
        log(f"\n  >>> Next step:")
        log(f"      1. Read {CONTEXT_FILE.name} in chat")
        log(f"      2. Write your decisions to {DECISIONS_FILE.name}")
        log(f"      3. Run: python hunt.py --execute")
    else:
        log("\n  No items found. Check log for details.")


def run_execute(args, state):
    """EXECUTE phase: read hunt_decisions.md, send everything marked as 'send'."""
    banner(f"HUNT.PY — EXECUTE PHASE ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    if not DECISIONS_FILE.exists():
        log(f"  [ERROR] {DECISIONS_FILE.name} not found.")
        log(f"  Write your decisions first, then re-run.")
        log(f"  See {CONTEXT_FILE.name} for the data to decide on.")
        return

    # Parse decisions file
    decisions = parse_decisions_file()
    if not decisions:
        log("  No actionable decisions found in hunt_decisions.md")
        return
    log(f"  Found {len(decisions)} decision(s)")

    # Load raw items to map decisions to original data
    raw_file = WORKSPACE / "hunt_raw.json"
    raw_items = []
    if raw_file.exists():
        try:
            raw_items = json.loads(raw_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Filter out items that were already sent in previous runs
    sent_followup_keys = set(state.get("sent_followups", []))
    sent_replies_keys = set(state.get("replied_ids", []))
    sent_bids_keys = set(state.get("sent_bids", []))
    filtered = []
    for d in decisions:
        t = d.get("type", "")
        to = d.get("to", "")
        thread_url = d.get("thread_url", "")
        if t == "email_followup" and to in sent_followup_keys:
            log(f"  [SKIP] Already sent followup to: {to}")
            continue
        if t == "email_reply":
            # Match by message_id if we can find it in raw
            log(f"  [INFO] Reply to {to} — will check before sending")
        if t == "forum_reply" and any(thread_url[:60] in k for k in sent_bids_keys):
            log(f"  [SKIP] Already posted to forum thread: {thread_url[:60]}")
            continue
        filtered.append(d)
    decisions = filtered
    if not decisions:
        log("  All decisions were already sent. Nothing to do.")
        return

    # Initialize browser if any decision needs it
    context = None
    needs_browser = any(d.get("type") in ("forum_reply", "mostaql_bid", "nafezly_bid")
                        for d in decisions)
    if needs_browser:
        try:
            pw, context = launch_browser(args.brave_profile)
            send_decisions(decisions, state, context=context)
            context.close()
            pw.stop()
        except Exception as e:
            log(f"  [BROWSER ERROR] {e}")
            send_decisions(decisions, state, context=None)
    else:
        send_decisions(decisions, state, context=None)


def run_learn(state):
    """LEARN phase: convert every sent item from hunt_decisions.md
    into a reusable skill under skills/learning/.

    Idempotent: skills already saved are skipped (matched by source.to or
    source.thread_url). Safe to run after every --execute.
    """
    log("\n=== LEARN PHASE ===\n")
    if not SKILLS_AVAILABLE:
        log("  [ERROR] skills.manager not importable. Aborting.")
        return
    if not DECISIONS_FILE.exists():
        log(f"  [ERROR] {DECISIONS_FILE.name} not found. Run --execute first or create one.")
        return

    decisions = parse_decisions_file()
    if not decisions:
        log("  No decisions to learn from.")
        return

    # Load existing learned skill sources so we don't double-save
    from pathlib import Path
    learned_dir = WORKSPACE / "skills" / "learning"
    already = set()
    if learned_dir.exists():
        for f in learned_dir.rglob("*.json"):
            try:
                import json as _json
                data = _json.loads(f.read_text(encoding="utf-8"))
                src = data.get("source") or {}
                marker = src.get("to") or src.get("thread_url") or ""
                if marker:
                    already.add(marker[:60])
            except Exception:
                pass

    saved = 0
    skipped = 0
    by_type = {}
    for d in decisions:
        t = d.get("type", "")
        if t not in ("email_reply", "email_followup", "forum_reply", "arabic_bid"):
            continue
        marker = d.get("to", "") or d.get("thread_url", "") or d.get("project_url", "")
        marker = marker[:60]
        if marker and marker in already:
            skipped += 1
            continue
        name = record_learned_skill(d, log_label="LEARN")
        if name:
            saved += 1
            by_type[t] = by_type.get(t, 0) + 1

    log(f"\n  LEARN summary: {saved} new skills saved, {skipped} already known")
    for t, n in sorted(by_type.items()):
        log(f"    {t}: {n}")

    # Show current skills index
    try:
        idx_path = WORKSPACE / "skills" / "index.json"
        if idx_path.exists():
            import json as _json
            idx = _json.loads(idx_path.read_text(encoding="utf-8"))
            total = len(idx.get("skills", {}))
            learned = sum(1 for k in idx.get("skills", {}) if k.startswith("learning/"))
            log(f"\n  Skills index: {total} total ({learned} in learning/)")
    except Exception:
        pass

    log(f"\n  Tip: run --learn periodically. Edit skills/learning/*.json by hand "
        f"to promote good ones to skills/{{arabic_bid,email_*,forum_reply}}/")


def parse_decisions_file():
    """Parse hunt_decisions.md for actionable decisions.

    Format:
        ## DECISION: item_03
        ACTION: send
        TO: info@example.com
        SUBJECT: ...
        BODY:
        <content>
        ---
    """
    if not DECISIONS_FILE.exists():
        return []
    text = DECISIONS_FILE.read_text(encoding="utf-8")
    decisions = []
    # Match each decision block
    pattern = re.compile(
        r"## DECISION:\s*(\S+)\s*\n"
        r"ACTION:\s*(send|skip|edit)\s*\n"
        r"(.*?)(?=^## DECISION:|^---|\Z)",
        re.MULTILINE | re.DOTALL
    )
    for m in pattern.finditer(text):
        item_id = m.group(1).strip()
        action = m.group(2).strip().lower()
        rest = m.group(3)
        if action == "skip":
            log(f"  [SKIP] {item_id}: marked as skip")
            continue
        decision = {"item_id": item_id, "action": action}
        # Extract metadata
        to_m = re.search(r"^TO:\s*(.+)$", rest, re.MULTILINE)
        subj_m = re.search(r"^SUBJECT:\s*(.+)$", rest, re.MULTILINE)
        type_m = re.search(r"^TYPE:\s*(\S+)", rest, re.MULTILINE)
        thread_m = re.search(r"^THREAD_URL:\s*(.+)$", rest, re.MULTILINE)
        project_m = re.search(r"^PROJECT_URL:\s*(.+)$", rest, re.MULTILINE)
        body_m = re.search(r"^BODY:\s*\n(.+?)(?=^---|\Z)", rest, re.MULTILINE | re.DOTALL)
        if to_m:
            decision["to"] = to_m.group(1).strip()
        if subj_m:
            decision["subject"] = subj_m.group(1).strip()
        if type_m:
            decision["type"] = type_m.group(1).strip()
        if thread_m:
            decision["thread_url"] = thread_m.group(1).strip()
        if project_m:
            decision["project_url"] = project_m.group(1).strip()
        if body_m:
            decision["body"] = body_m.group(1).strip()
        if not decision.get("body"):
            log(f"  [WARN] {item_id}: no body, skipping")
            continue
        decisions.append(decision)
    return decisions


def send_decisions(decisions, state, context=None):
    """Send each decision via the appropriate channel."""
    sent = 0
    failed = 0
    for d in decisions:
        t = d.get("type", "")
        log(f"\n  → {d['item_id']} ({t}): {d.get('to') or d.get('thread_url') or d.get('project_url', '?')[:60]}")
        try:
            if t in ("email_reply", "email_followup"):
                if send_email_smtp(d.get("to", ""), d.get("subject", ""), d.get("body", "")):
                    state.setdefault("sent_replies" if t == "email_reply" else "sent_followups", []).append(
                        d.get("to", "")
                    )
                    if t == "email_reply":
                        increment_counter(state, "replies")
                    else:
                        increment_counter(state, "followups")
                    record_learned_skill(d)
                    sent += 1
                else:
                    failed += 1
            elif t == "forum_reply" and context:
                page = context.new_page()
                try:
                    page.goto(d.get("thread_url", ""), wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                    # Check login status — first time, prompt user to log in
                    if not ensure_logged_in(
                        page,
                        "n8n Community",
                        "https://community.n8n.io/login",
                        "button:has-text('Reply')",
                    ):
                        log(f"  [ERROR] Still not logged in to n8n Community — skipping")
                        failed += 1
                        continue
                    try:
                        reply_btn = page.locator("button:has-text('Reply')").first
                        reply_btn.scroll_into_view_if_needed()
                        reply_btn.click()
                        page.wait_for_timeout(1500)
                        editor = page.locator("textarea.d-editor-input").first
                        editor.wait_for(state="visible", timeout=10000)
                        editor.fill(d.get("body", ""))
                        page.wait_for_timeout(500)
                        shot = SCREENSHOTS / f"forum_post_{datetime.now().strftime('%H%M%S')}.png"
                        page.screenshot(path=str(shot))
                        post_btn = page.locator(
                            "button:has-text('Reply to Topic'), button:has-text('Post Reply')"
                        ).first
                        post_btn.click()
                        page.wait_for_timeout(3000)
                        log(f"  [POSTED] Forum reply (screenshot: {shot.name})")
                        state.setdefault("sent_bids", []).append(
                            f"forum:{d.get('thread_url', '')[:60]}"
                        )
                        increment_counter(state, "forum_replies")
                        record_learned_skill(d)
                        sent += 1
                    except Exception as e:
                        log(f"  [ERROR] Forum post: {e}")
                        failed += 1
                finally:
                    page.close()
            elif t in ("mostaql_bid", "nafezly_bid"):
                log(f"  [INFO] Arabic bid — please submit manually in browser")
                log(f"        URL: {d.get('project_url', '')}")
                log(f"        Body saved in decisions file")
                failed += 1
            else:
                log(f"  [WARN] Unknown type: {t}")
                failed += 1
        except Exception as e:
            log(f"  [ERROR] {e}")
            failed += 1

    log(f"\n  EXECUTE complete: {sent} sent, {failed} failed")


def send_drafts_items(drafts, context=None):
    """[Legacy] Send items from the old draft format."""
    log("  [LEGACY] Use --execute with hunt_decisions.md instead")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nAborted by user (Ctrl+C).")
        sys.exit(1)
