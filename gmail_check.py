"""
Gmail reply check — FREE, no API costs.

Uses IMAP with Gmail App Password (free, set up once).
Filters inbox for replies from known application recipients.

Output: prints reply summary + saves to gmail_log.md

Setup (one-time, free):
  1. Enable 2FA on ambdambd200@gmail.com
  2. Go to https://myaccount.google.com/apppasswords
  3. Create app password for "Mail / Windows Computer"
  4. Copy 16-char password
  5. Set env var: GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

Run:
  python gmail_check.py
"""

import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import os
import sys
from datetime import datetime, timedelta

# Configuration
GMAIL_USER = "ambdambd200@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"
LOG_FILE = "gmail_log.md"

# Application recipients (from Application_Pipeline.md)
RECIPIENTS = [
    "info@zyimmo.de",
    "careers@asiacruit.com",
    "info@s-e.lt",
    "n8nera@gmail.com",
    "wayne@nocodecreative.io",
    "folafoluwaolaneye@gmail.com",
]

# Look back window
DAYS_BACK = 14


def connect():
    if not GMAIL_APP_PASSWORD:
        print("ERROR: GMAIL_APP_PASSWORD environment variable not set.")
        print("Setup: https://myaccount.google.com/apppasswords")
        sys.exit(1)
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        return mail
    except Exception as e:
        print(f"ERROR: Cannot connect to Gmail: {e}")
        sys.exit(1)


def decode_subject(msg):
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or "utf-8", errors="replace")
    return subject or "(no subject)"


def decode_from(msg):
    from_header, encoding = decode_header(msg.get("From", ""))[0]
    if isinstance(from_header, bytes):
        from_header = from_header.decode(encoding or "utf-8", errors="replace")
    return from_header or "(unknown)"


def check_replies():
    mail = connect()
    mail.select("inbox")

    since_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%d-%b-%Y")

    seen_ids = set()
    for recipient in RECIPIENTS:
        try:
            status, data = mail.search(None, f'FROM "{recipient}" SINCE {since_date}')
        except Exception as e:
            print(f"  [warn] Search failed for {recipient}: {e}")
            continue
        if status != "OK" or not data or not data[0]:
            continue
        for num in data[0].split():
            seen_ids.add(num)

    message_ids = sorted(seen_ids)
    replies = []
    for num in message_ids:
        status, msg_data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        replies.append({
            "from": decode_from(msg),
            "subject": decode_subject(msg),
            "date": msg.get("Date", ""),
            "message_id": num.decode(),
        })

    mail.logout()
    return replies


def log_replies(replies):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n## Check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if not replies:
            f.write("_No replies found from application recipients._\n")
        else:
            f.write(f"**{len(replies)} reply/replies found:**\n\n")
            for r in replies:
                f.write(f"- **{r['from']}** — {r['subject']} _({r['date']})_\n")
        f.write("\n---\n")


def main():
    print("=" * 60)
    print(f"GMAIL REPLY CHECK — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Checking inbox for replies from {len(RECIPIENTS)} recipients...")
    print(f"Look-back window: {DAYS_BACK} days")
    print()

    replies = check_replies()

    if not replies:
        print("[OK] No replies found.")
    else:
        print(f"[FOUND] {len(replies)} reply/replies:\n")
        for r in replies:
            print(f"  FROM: {r['from']}")
            print(f"  SUBJ: {r['subject']}")
            print(f"  DATE: {r['date']}")
            print()

    log_replies(replies)
    print(f"Log saved to: {LOG_FILE}")
    print("Update Application_Pipeline.md with new status before next run.")


if __name__ == "__main__":
    main()
