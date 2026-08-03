"""
email_agent.py — Autonomous Email Agent (Phase 1).

Checks Gmail, classifies each message using AI, generates responses,
writes decisions to hunt_decisions.md for user review, and learns
from each interaction.

Usage:
    python email_agent.py                 # Full run: check + classify + decide
    python email_agent.py --check-only    # Only check, no AI
    python email_agent.py --status        # Show thread state
    python email_agent.py --reset-state   # Clear state (testing)

Dependencies: keyhub_client.py, quota.py
"""

import imaplib
import socket
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import os
import sys
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from html import unescape

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(__file__).parent
STATE_FILE = WORKSPACE / "email_agent_state.json"
LOG_FILE = WORKSPACE / "email_agent.log"
DECISIONS_FILE = WORKSPACE / "hunt_decisions.md"

GMAIL_USER = "salim.muhammad.work@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"
DAYS_BACK = 14
FOLLOWUP_DAYS = 7  # Send follow-up if no reply after N days

sys.path.insert(0, str(WORKSPACE))
try:
    from keyhub_client import ai_generate, ai_generate_json
    from quota import can_send, record_sent, get_remaining
except ImportError as e:
    print(f"[ERROR] Cannot import workspace modules: {e}")
    print("Make sure you're running from Money/ directory.")
    sys.exit(1)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"threads": {}, "last_check": None}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


IMAP_TIMEOUT = 45

SPAM_SENDERS = [
    "noreply@", "notifications@", "newsletter@", "hello@", "team@",
    "marketing@", "updates@", "info@", "news@", "digest@",
    "no-reply@", "account-security-noreply@",
]
SPAM_DOMAINS = [
    "substack.com", "skool.com",
    "facebookmail.com", "engage.canva.com", "send.vidiq.com",
    "reverso.net", "ollama.com", "groq.co",
    "google.com", "m.weworkremotely.com",
    "email.openai.com", "mail.uptimerobot.com", "uptimerobot.com",
    "mail.mangolanguages.com", "workingnomads.com", "youtube.com",
    "accountprotection.microsoft.com",
    "emailnotifications.microsoft.com", "infomails.microsoft.com",
]

PLATFORM_DOMAINS = {
    "linkedin": ["em.linkedin.com", "linkedin.com"],
    "github": ["github.com", "notifications@github.com"],
    "microsoft": ["microsoft.com"],
    "netlify": ["netlify.com"],
}

# Fallback keyword classifier (works without AI)
CLIENT_KEYWORDS_EN = [
    "project", "hire", "freelance", "automation", "n8n",
    "offer", "budget", "contract", "proposal", "interested",
    "quote", "pricing", "scope", "timeline", "availability",
    "workflow", "integrat", "api", "webhook", "developer",
    "engineer", "candidate", "interview", "position", "role",
    "opportunity", "collaborate", "partnership",
    "test task", "sample", "portfolio", "freelancer",
    "urgent", "available", "need", "looking for", "seeking",
]
CLIENT_KEYWORDS_AR = [
    "مشروع", "توظيف", "عمل", "حر", "أتمتة",
    "عرض", "ميزانية", "عقد", "اقتراح", "مهتم",
    "سعر", "نطاق", "جدول", "متاح",
    "مطور", "مهندس", "فرصة", "تعاون", "شراكة",
    "احتاج", "مطلوب", "مساعدة", "استفسار",
]

PLATFORM_KEYWORDS = {
    "linkedin_message": ["linkedin", "inmail", "connection request", "invitation", "shared"],
    "n8n_forum": ["n8n community", "forum", "discourse", "topic"],
    "upwork": ["upwork", "project invite", "interview", "job invitation"],
    "nafezly": ["nafezly", "نفذلي", "مشروع"],
    "mostaql": ["mostaql", "مستقل", "عرض"],
}

def connect():
    if not GMAIL_APP_PASSWORD:
        log("ERROR: GMAIL_APP_PASSWORD env var not set")
        return None
    try:
        socket.setdefaulttimeout(IMAP_TIMEOUT)
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=IMAP_TIMEOUT)
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        return mail
    except socket.timeout:
        log("ERROR: IMAP connection timed out (network too slow)")
        return None
    except Exception as e:
        log(f"ERROR: IMAP connect failed: {type(e).__name__}: {e}")
        return None


def decode_header_str(header_value):
    if not header_value:
        return ""
    parts = decode_header(header_value)
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except (LookupError, UnicodeDecodeError):
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(str(part))
    return " ".join(result)


def extract_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition", ""))
            if "attachment" in cdisp:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            try:
                charset = part.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                decoded = payload.decode("utf-8", errors="replace")
            if ctype == "text/plain":
                body = decoded
                break
            elif ctype == "text/html" and not body:
                body = decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                charset = msg.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                body = payload.decode("utf-8", errors="replace")

    body = re.sub(r"<[^>]+>", " ", body)
    body = unescape(body)
    body = re.sub(r"\s+", " ", body).strip()
    body = re.sub(r"(https?://\S+)", " [URL] ", body)
    return body[:2000]


def get_thread_id(msg):
    msg_id = msg.get("Message-ID", "") or msg.get("Message-Id", "")
    if msg_id:
        return msg_id.strip().strip("<>")
    return None


def get_references(msg):
    refs = msg.get("References", "") or msg.get("In-Reply-To", "")
    if refs:
        for ref in re.split(r"\s+", refs):
            ref = ref.strip().strip("<>")
            if ref:
                return ref
    return None


def fetch_emails(mail, folder="inbox", since_days=DAYS_BACK):
    try:
        mail.select(folder)
    except Exception as e:
        log(f"ERROR selecting {folder}: {e}")
        return []
    since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
    try:
        status, data = mail.search(None, f"SINCE {since_date}")
    except Exception as e:
        log(f"ERROR searching {folder}: {e}")
        return []
    if status != "OK" or not data or not data[0]:
        return []
    
    emails_list = []
    for num in data[0].split():
        status, msg_data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        
        thread_id = get_thread_id(msg)
        parent_id = get_references(msg)
        subject = decode_header_str(msg.get("Subject", ""))
        from_addr = decode_header_str(msg.get("From", ""))
        date_str = msg.get("Date", "")
        
        try:
            dt = parsedate_to_datetime(date_str)
        except Exception:
            dt = datetime.now(timezone.utc)
        
        body = extract_body(msg)
        
        is_reply = bool(parent_id) or subject.lower().startswith("re:")
        
        emails_list.append({
            "thread_id": thread_id,
            "parent_id": parent_id,
            "folder": folder,
            "uid": num.decode(),
            "from": from_addr,
            "subject": subject,
            "date": date_str,
            "datetime": dt.isoformat(),
            "body": body,
            "is_reply": is_reply,
            "raw_subject": msg.get("Subject", ""),
        })
    
    return emails_list


def detect_platform(email_data):
    from_addr = email_data.get("from", "").lower()
    subject = email_data.get("subject", "").lower()
    for platform, domains in PLATFORM_DOMAINS.items():
        for d in domains:
            if d in from_addr:
                if platform == "linkedin" and ("inmail" in subject or "message" in subject or "connection" in subject):
                    return "linkedin_message"
                if platform == "github":
                    return "github_notification"
                return f"platform_{platform}"
    for platform, kws in PLATFORM_KEYWORDS.items():
        for kw in kws:
            if kw.lower() in subject:
                return platform
    return None


def is_obviously_spam(email_data):
    from_addr = email_data.get("from", "").lower()
    subject = email_data.get("subject", "").lower()
    
    platform = detect_platform(email_data)
    if platform:
        return False
    
    for sender in SPAM_SENDERS:
        if sender in from_addr:
            return True
    for domain in SPAM_DOMAINS:
        if domain in from_addr:
            return True
    
    spam_subjects = ["unsubscribe", "weekly digest",
                     "new skill", "appeared in", "complete your profile",
                     "is hiring", "hiring a", "40% off"]
    for phrase in spam_subjects:
        if phrase in subject:
            return True
    
    return False


def classify_by_keywords(email_data):
    subject = email_data.get("subject", "").lower()
    body = email_data.get("body", "").lower()
    combined = subject + " " + body
    
    platform = detect_platform(email_data)
    if platform:
        if "message" in platform or "inmail" in platform or platform == "linkedin_message":
            return "interested", f"platform: {platform}"
        return platform, f"platform notification: {platform}"
    
    for kw in CLIENT_KEYWORDS_EN + CLIENT_KEYWORDS_AR:
        if kw.lower() in combined:
            return "interested", f"keyword match: {kw}"
    
    return None, None


def classify_email(email_data, state):
    thread_id = email_data["thread_id"]
    
    existing = state["threads"].get(thread_id)
    if existing and existing.get("classification") in ("interested", "question", "reject"):
        if existing.get("responded"):
            return existing["classification"], "already processed"

    kw_class, kw_reason = classify_by_keywords(email_data)
    if kw_class:
        if kw_class in ("linkedin_message", "n8n_forum", "upwork", "nafezly", "mostaql"):
            return kw_class, kw_reason
        return kw_class, kw_reason

    prompt = f"""Classify this email for a freelance AI Automation Engineer named Salim Muhammad.

From: {email_data["from"]}
Subject: {email_data["subject"]}
Body: {email_data["body"][:1000]}

Return a JSON object with:
- "classification": one of ["interested", "question", "negotiation", "reject", "spam", "auto_reply", "platform_notification", "other"]
- "confidence": 0.0 to 1.0
- "reason": short explanation
- "needs_reply": true/false
- "suggested_tone": "formal_en" | "casual_en" | "formal_ar" | "casual_ar"

Rules:
- "interested" = wants to hire, discuss project, or collaborate
- "question" = asking for info, clarification, or pricing
- "negotiation" = discussing terms, price, scope
- "reject" = not interested, no budget, found someone else
- "spam" = irrelevant, promotional, newsletter
- "auto_reply" = out-of-office, automatic confirmation
- "platform_notification" = LinkedIn/n8n forum/Upwork notification, might be a client message
- "other" = anything else"""
    
    result = ai_generate_json(prompt, temperature=0.2, caller="email_agent_classify")
    if not result:
        return "other", "AI unavailable"
    
    classification = result.get("classification", "other")
    confidence = result.get("confidence", 0.0)
    needs_reply = result.get("needs_reply", False)
    
    if not needs_reply or classification in ("spam", "auto_reply", "reject"):
        return classification, result.get("reason", "")
    
    if classification == "interested" and confidence < 0.5:
        return "other", f"low confidence ({confidence})"
    
    return classification, result.get("reason", "")


def generate_response(email_data, classification, context):
    skip = ("spam", "auto_reply", "reject", "other",
            "platform_github", "platform_microsoft", "platform_netlify")
    needs_reply = classification not in skip
    if not needs_reply:
        return None

    platform_lead = classification in ("linkedin_message", "n8n_forum", "upwork", "nafezly", "mostaql")
    if platform_lead:
        return None

    prompt = f"""Generate an email response for Salim Muhammad, an AI Automation Engineer (freelance).

Context: This is a reply to an email from a client/prospect.
Classification: {classification}
From: {email_data["from"]}
Subject: {email_data["subject"]}
Original body: {email_data["body"][:800]}

Rules:
- Be professional, concise, results-oriented
- If interested: thank them, offer next steps (free test task or 15-min call)
- If question: answer directly, ask 1-2 clarifying questions
- If negotiation: be flexible but don't undershoot ($25-50/hr range, $200-500/project)
- NEVER reveal being an AI
- Sign as "Salim Muhammad"
- Include email: salim.muhammad.work@gmail.com
- 3-5 paragraphs maximum
- In English (or Arabic if client wrote in Arabic)

Return ONLY the response body, no JSON, no markdown."""
    
    response = ai_generate(prompt, temperature=0.3, max_tokens=600, caller="email_agent_respond")
    return response


def write_decision(email_data, classification, response, state):
    platform_lead = classification in ("linkedin_message", "n8n_forum", "upwork", "nafezly", "mostaql")
    if not response and not platform_lead:
        return
    
    existing_items = []
    if DECISIONS_FILE.exists():
        content = DECISIONS_FILE.read_text(encoding="utf-8")
        existing = re.findall(r"## DECISION: (item_\d+)", content)
        if existing:
            existing_items = existing
    
    next_num = 1
    if existing_items:
        nums = [int(x.split("_")[1]) for x in existing_items]
        next_num = max(nums) + 1
    
    item_id = f"item_{next_num:02d}"
    entry_type = "email_reply" if classification == "interested" else "email_followup"
    
    if platform_lead:
        entry = f"""
## DECISION: {item_id}
ACTION: review
TYPE: platform_notification
PLATFORM: {classification}
FROM: {email_data["from"]}
SUBJECT: {email_data["subject"]}
CLASSIFICATION: {classification}
THREAD_ID: {email_data["thread_id"]}
NOTE: Check this platform for a message/lead from this user.
URL: https://www.linkedin.com/messaging/ (if linkedin)

---
"""
    else:
        entry = f"""
## DECISION: {item_id}
ACTION: send
TYPE: {entry_type}
TO: {email_data["from"]}
SUBJECT: Re: {email_data["subject"]}
CLASSIFICATION: {classification}
THREAD_ID: {email_data["thread_id"]}
BODY:
{response}

---
"""
    
    with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
    
    log(f"  → Wrote decision {item_id} to hunt_decisions.md")


def learn_from_email(email_data, classification, response):
    if not response or classification not in ("interested", "question"):
        return
    
    skills_path = WORKSPACE / "skills" / "learning" / "email"
    skills_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_from = re.sub(r"[^a-zA-Z0-9]", "_", email_data["from"].split("<")[0].strip()[:20])
    filename = f"learned_{timestamp}_{safe_from}.json"
    
    skill = {
        "name": f"learning/email/{filename.replace('.json', '')}",
        "type": "email_reply" if classification == "interested" else "email_followup",
        "language": "en",
        "tags": ["email", "learned", classification],
        "uses": 0,
        "version": 1,
        "created": datetime.now().isoformat(),
        "source": {
            "from": email_data["from"],
            "subject": email_data["subject"],
            "classification": classification,
            "response_preview": response[:200],
        },
    }
    
    filepath = skills_path / filename
    filepath.write_text(json.dumps(skill, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  → Learned: saved to {filepath}")


def process_email(email_data, state):
    thread_id = email_data["thread_id"]
    if not thread_id:
        log(f"  [skip] No thread ID: {email_data['subject'][:50]}")
        return
    
    if thread_id in state["threads"]:
        existing = state["threads"][thread_id]
        if existing.get("processed"):
            log(f"  [skip] Already processed: {email_data['subject'][:50]}")
            return
    
    if is_obviously_spam(email_data):
        spam_class = "spam"
        state["threads"][thread_id] = {
            "from": email_data["from"],
            "subject": email_data["subject"],
            "date": email_data["date"],
            "classification": spam_class,
            "reason": "pre-filter: known spam sender/domain",
            "processed": True,
            "responded": False,
        }
        log(f"  [skip] Pre-filtered spam: {email_data['from']} — {email_data['subject'][:50]}")
        save_state(state)
        return
    
    log(f"  Classifying: {email_data['from']} — {email_data['subject'][:60]}")
    classification, reason = classify_email(email_data, state)
    log(f"    → {classification} ({reason[:60] if reason else 'no reason'})")
    
    state["threads"][thread_id] = {
        "from": email_data["from"],
        "subject": email_data["subject"],
        "date": email_data["date"],
        "classification": classification,
        "reason": reason,
        "processed": True,
        "responded": False,
    }
    
    if classification in ("spam", "auto_reply", "other", "platform_github", "platform_microsoft", "platform_netlify"):
        log(f"    -> Skipping ({classification})")
        save_state(state)
        return

    platform_lead = classification in ("linkedin_message", "n8n_forum", "upwork", "nafezly", "mostaql")
    if platform_lead:
        log(f"    -> Platform lead detected! ({classification})")
        state["threads"][thread_id]["platform_lead"] = True
        write_decision(email_data, classification, None, state)
        save_state(state)
        return
    
    if not can_send("replies"):
        log(f"    → Daily reply quota exhausted, skipping")
        save_state(state)
        return
    
    response = generate_response(email_data, classification, state)
    if response:
        state["threads"][thread_id]["responded"] = True
        state["threads"][thread_id]["response"] = response[:100]
        write_decision(email_data, classification, response, state)
        learn_from_email(email_data, classification, response)
        record_sent("replies", f"{email_data['from']}: {email_data['subject'][:40]}")
    
    save_state(state)


def check_followups(state):
    sent_emails = []
    sent_file = WORKSPACE / "sent_applications.log"
    if sent_file.exists():
        content = sent_file.read_text(encoding="utf-8", errors="replace")
        for line in content.split("\n"):
            if "TO:" in line:
                sent_emails.append(line.split("TO:")[-1].strip())
    
    pipeline_file = WORKSPACE / "Application_Pipeline.md"
    if pipeline_file.exists():
        content = pipeline_file.read_text(encoding="utf-8", errors="replace")
        email_matches = re.findall(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", content)
        sent_emails.extend(email_matches)
    
    sent_emails = list(set(sent_emails))
    log(f"Found {len(sent_emails)} sent application addresses to check follow-ups for")
    
    for addr in sent_emails:
        if not can_send("followups"):
            log(f"  → Follow-up quota exhausted")
            break
        
        followup_key = f"followup_{addr}"
        if followup_key in state.get("followups_sent", {}):
            continue
        
        log(f"  Adding follow-up decision for: {addr}")
        prompt = f"""Write a professional follow-up email for Salim Muhammad (AI Automation Engineer).

The recipient is: {addr}
Salim sent an application but got no reply. Write a polite 3-paragraph follow-up offering a free test task (e.g. a 2-day n8n workflow sample).

Rules:
- Polite, not pushy
- Offer a specific small deliverable as a free test
- Sign as "Salim Muhammad"
- Include email: salim.muhammad.work@gmail.com
- 3 paragraphs maximum

Return ONLY the body text."""
        
        response = ai_generate(prompt, temperature=0.3, max_tokens=500, caller="email_agent_followup")
        if not response:
            continue
        
        entry_type = "email_followup"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        item_id = f"followup_{timestamp}_{addr.split('@')[0]}"
        
        entry = f"""
## DECISION: {item_id}
ACTION: send
TYPE: {entry_type}
TO: {addr}
SUBJECT: Following up — quick n8n sample workflow
BODY:
{response}

---
"""
        
        with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        
        state.setdefault("followups_sent", {})[followup_key] = datetime.now().isoformat()
        record_sent("followups", addr)
        log(f"  → Wrote follow-up for {addr}")


def check_replies_inbox(state):
    mail = connect()
    if not mail:
        return
    
    try:
        emails = fetch_emails(mail, "inbox")
        log(f"Fetched {len(emails)} inbox emails from last {DAYS_BACK} days")
        
        replies = [e for e in emails if e["is_reply"]]
        log(f"  Of which {len(replies)} are replies to sent messages")
        
        for em in replies:
            process_email(em, state)
        
        new_emails = [e for e in emails if not e["is_reply"] and "unsubscribe" not in e["body"][:300].lower()]
        log(f"  {len(new_emails)} are new (non-reply, non-newsletter)")
        
        for em in new_emails:
            process_email(em, state)
            
    finally:
        try:
            mail.logout()
        except Exception:
            pass


def check_sent_followups(mail, state):
    if not can_send("followups"):
        log("Follow-up quota exhausted")
        return
    
    emails = fetch_emails(mail, "[Gmail]/Sent Mail", since_days=FOLLOWUP_DAYS + 2)
    log(f"Fetched {len(emails)} sent emails")
    
    sent_to = {}
    for em in emails:
        addr_match = re.search(r"<([^>]+@[^>]+)>", em["from"])
        if addr_match:
            addr = addr_match.group(1)
        else:
            addr = em["from"].strip()
        
        if addr not in sent_to:
            sent_to[addr] = em
    
    replies_inbox = fetch_emails(mail, "inbox", since_days=FOLLOWUP_DAYS + 2)
    replied_addrs = set()
    for em in replies_inbox:
        if em["is_reply"]:
            addr_match = re.search(r"<([^>]+@[^>]+)>", em["from"])
            if addr_match:
                replied_addrs.add(addr_match.group(1))
            else:
                replied_addrs.add(em["from"].strip())
    
    for addr, em in sent_to.items():
        if addr in replied_addrs:
            continue
        
        fw_key = f"followup_{addr}"
        if fw_key in state.get("followups_sent", {}):
            continue
        
        if not can_send("followups"):
            break
        
        log(f"  No reply from {addr} — generating follow-up")
        prompt = f"""Write a follow-up email for Salim Muhammad, an AI Automation Engineer.

Original sent to: {addr}
Subject was: {em["subject"]}
Date sent: {em["date"]}

Write a polite 3-paragraph follow-up. Offer a free test task or 15-min call.
Be concise, professional. Sign as Salim Muhammad with salim.muhammad.work@gmail.com.

Return ONLY the body text."""
        
        response = ai_generate(prompt, temperature=0.3, max_tokens=500, caller="email_agent_followup")
        if not response:
            continue
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        item_id = f"followup_{timestamp}_{addr.split('@')[0]}"
        
        entry = f"""
## DECISION: {item_id}
ACTION: send
TYPE: email_followup
TO: {addr}
SUBJECT: Following up — {em["subject"][:40]}
CLASSIFICATION: follow_up_needed
BODY:
{response}

---
"""
        
        with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        
        state.setdefault("followups_sent", {})[fw_key] = datetime.now().isoformat()
        record_sent("followups", addr)
        log(f"  → Wrote follow-up for {addr}")


def show_status(state):
    threads = state.get("threads", {})
    followups = state.get("followups_sent", {})
    
    print(f"\n  Email Agent State")
    print(f"  {'='*50}")
    print(f"  Last check: {state.get('last_check', 'never')}")
    print(f"  Threads tracked: {len(threads)}")
    print(f"  Follow-ups sent: {len(followups)}")
    print()
    
    classified = {}
    for tid, t in threads.items():
        c = t.get("classification", "unknown")
        classified[c] = classified.get(c, 0) + 1
    
    if classified:
        print(f"  By classification:")
        for c, count in sorted(classified.items(), key=lambda x: -x[1]):
            print(f"    {c}: {count}")
    
    print()
    print(f"  Remaining quotas today:")
    for action in ["replies", "followups", "emails_sent"]:
        remaining = get_remaining(action)
        print(f"    {action}: {remaining}")
    
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Email Agent — Phase 1")
    parser.add_argument("--check-only", action="store_true", help="Fetch only, no AI")
    parser.add_argument("--status", action="store_true", help="Show state")
    parser.add_argument("--reset-state", action="store_true", help="Clear state")
    parser.add_argument("--no-followups", action="store_true", help="Skip follow-up check")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"  EMAIL AGENT — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    state = load_state()
    
    if args.reset_state:
        state = {"threads": {}, "last_check": None, "followups_sent": {}}
        save_state(state)
        log("State reset")
        return
    
    if args.status:
        show_status(state)
        return
    
    state["last_check"] = datetime.now().isoformat()
    save_state(state)
    
    mail = connect()
    if mail:
        try:
            check_replies_inbox(state)
        finally:
            try:
                mail.logout()
            except Exception:
                pass
    else:
        log("IMAP unavailable — skipping inbox scan. Check network and retry later.")
        log("NOTE: Follow-up generation from local files still works.")
    
    if not args.no_followups:
        log("Checking sent applications for follow-ups...")
        check_followups(state)
    
    state["last_check"] = datetime.now().isoformat()
    save_state(state)
    
    print()
    show_status(state)
    print(f"  Done. Check hunt_decisions.md for new decisions.")
    print(f"  Run 'hunt.py --execute' to send approved decisions.")
    print(f"  IMAP unavailable = run again when network is better.")
    print()


if __name__ == "__main__":
    main()
