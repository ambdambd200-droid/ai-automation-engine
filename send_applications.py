"""
Send 4 applications via Gmail SMTP — FREE.

Uses Gmail App Password (same env var as gmail_check.py).
Reads application files (Application_*.md), extracts subject + body,
sends via SMTP, logs to Application_Pipeline.md.

Run:
  set GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
  python send_applications.py
"""

import os
import smtplib
import re
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

GMAIL_USER = "ambdambd200@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
WORKSPACE = Path(r"C:\Users\A\Desktop\Money")
SENT_LOG = WORKSPACE / "sent_applications.log"

# Applications to send: (filename, recipient_email, fallback_subject)
APPLICATIONS = [
    {
        "file": "Application_Make_AI_Expert.md",
        "to": "applications@make.com",
        "fallback_subject": "AI Automation Expert — Application",
        "apply_url": "https://make.recruitee.com/o/ai-automation-expert",
    },
    {
        "file": "Application_Mindrift.md",
        "to": "applications@mindrift.ai",
        "fallback_subject": "Freelance Automation Workflow Specialist — Application",
        "apply_url": "https://jobs.workable.com/view/txoV5YSrKBM8BUSZo2Efiv",
    },
    {
        "file": "Application_Sagan_Recruitment.md",
        "to": "recruitment@saganrecruitment.com",
        "fallback_subject": "AI Automation Engineer (HR85702) — Application",
        "apply_url": "https://saganrecruitment.com/job/ai-automation-engineer-hr85702/",
    },
    {
        "file": "Application_Hireza.md",
        "to": "contact@hireza.com",
        "fallback_subject": "AI Automation Specialist (Make.com) — Application",
        "apply_url": "https://hireza.wuaze.com/job/ai-automation-specialist-make-com-expert-n8n-zapier-workflow-for-ai-video-creator-2",
    },
]


def parse_application(filepath):
    """Extract subject and body from an Application_*.md file."""
    text = Path(filepath).read_text(encoding="utf-8")

    # Try to find a "Subject:" or "**Subject:**" line
    subject = None
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^#+\s*Subject:\s*(.+)$", line, re.IGNORECASE)
        if m:
            subject = m.group(1).strip()
            break
        m = re.match(r"^\*\*Subject:\*\*\s*(.+)$", line, re.IGNORECASE)
        if m:
            subject = m.group(1).strip()
            break
        m = re.match(r"^Subject:\s*(.+)$", line, re.IGNORECASE)
        if m:
            subject = m.group(1).strip()
            break

    if not subject:
        subject = "Job Application — AI Automation Engineer"

    # Body = everything after the first "---" separator (or after the metadata header)
    body_start = text.find("---")
    if body_start > 0:
        body = text[body_start + 3 :].strip()
    else:
        body = text

    # Remove leading "## Application Message" or "## Message" headers
    body = re.sub(r"^#+\s*(Application Message|Message|Cover Letter)\s*\n+", "", body, flags=re.IGNORECASE)

    # Convert markdown to plain text (basic — strip bold/italic markers)
    body_plain = re.sub(r"\*\*(.+?)\*\*", r"\1", body)  # **bold** -> bold
    body_plain = re.sub(r"^#+\s*", "", body_plain, flags=re.MULTILINE)  # ## -> ""
    body_plain = re.sub(r"^-\s+", "  - ", body_plain, flags=re.MULTILINE)  # list items

    return subject, body_plain


def send_email(to, subject, body, dry_run=True):
    """Send an email via Gmail SMTP. Logs result."""
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    log_entry = f"[{datetime.now().isoformat()}] TO={to} SUBJECT={subject} "

    if dry_run:
        print(f"\n{'=' * 60}\nDRY RUN (not sent)\n{'=' * 60}")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(f"Body ({len(body)} chars):")
        print("-" * 40)
        print(body[:500] + ("..." if len(body) > 500 else ""))
        print()
        return "DRY_RUN"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to, msg.as_string())
        print(f"  [SENT] {to}: {subject}")
        return "SENT"
    except Exception as e:
        print(f"  [ERROR] {to}: {e}")
        return f"ERROR: {e}"


def log_result(result_line):
    with open(SENT_LOG, "a", encoding="utf-8") as f:
        f.write(result_line + "\n")


def main():
    if not GMAIL_APP_PASSWORD and "--send" in sys.argv:
        print("ERROR: GMAIL_APP_PASSWORD environment variable not set.")
        print("Run: set GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx")
        print("Or use --dry-run to preview without sending.")
        sys.exit(1)

    dry_run = "--send" not in sys.argv

    print("=" * 60)
    print(f"SEND APPLICATIONS — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE SEND'}")
    print("=" * 60)

    for app in APPLICATIONS:
        filepath = WORKSPACE / app["file"]
        if not filepath.exists():
            print(f"\n[SKIP] {app['file']} not found")
            log_result(f"[{datetime.now().isoformat()}] SKIP file_not_found: {app['file']}")
            continue

        subject, body = parse_application(filepath)
        result = send_email(app["to"], subject, body, dry_run=dry_run)
        log_result(f"[{datetime.now().isoformat()}] {app['file']} -> {app['to']} = {result}")

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)
    if dry_run:
        print()
        print("This was a DRY RUN. To actually send, run:")
        print("  python send_applications.py --send")
        print()
        print("Make sure GMAIL_APP_PASSWORD env var is set first:")
        print("  set GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx")
    else:
        print()
        print("Emails sent. Check Gmail Sent folder to verify.")
        print("Update Application_Pipeline.md with the new rows.")


if __name__ == "__main__":
    main()
