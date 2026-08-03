#!/usr/bin/env python3
"""
send_email.py — Generic email sender for Salim Muhammad's freelance system.

Usage:
  python send_email.py --to "client@example.com" --subject "Subject" --body "Body text"
  python send_email.py --to "..." --subject "..." --body-file body.txt
  python send_email.py --interactive  # prompts for fields

Environment:
  GMAIL_APP_PASSWORD at OS level (User)
"""

import os
import sys
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
LOG_FILE = WORKSPACE / "email_sent.log"

GMAIL_USER = "salim.muhammad.work@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

if not GMAIL_APP_PASSWORD:
    # Try to read from registry
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as reg:
            val, _ = winreg.QueryValueEx(reg, "GMAIL_APP_PASSWORD")
            if val:
                GMAIL_APP_PASSWORD = val
    except Exception:
        pass


def log_sent(to, subject, status, error=None):
    entry = f"[{datetime.now().isoformat()}] TO={to} SUBJECT={subject} STATUS={status}"
    if error:
        entry += f" ERROR={error}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def send_email(to, subject, body, dry_run=False):
    """Send email via Gmail SMTP."""
    if not GMAIL_APP_PASSWORD:
        return False, "GMAIL_APP_PASSWORD not set in environment"

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if dry_run:
        print(f"\n{'='*60}\nDRY RUN — not sent\n{'='*60}")
        print(f"From: {GMAIL_USER}")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(f"Body ({len(body)} chars):\n{'-'*40}")
        print(body[:500] + ("..." if len(body) > 500 else ""))
        return True, "DRY_RUN"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True, "SENT"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Send email via Gmail SMTP")
    parser.add_argument("--to", help="Recipient email")
    parser.add_argument("--subject", help="Email subject")
    parser.add_argument("--body", help="Email body text")
    parser.add_argument("--body-file", help="Path to file containing body text")
    parser.add_argument("--interactive", action="store_true", help="Prompt for fields")
    parser.add_argument("--dry-run", action="store_true", help="Print instead of sending")
    args = parser.parse_args()

    # Gather fields
    to = args.to
    subject = args.subject
    body = args.body

    if args.interactive or not (to and subject):
        print("=== Email Composer ===")
        to = to or input("To: ").strip()
        subject = subject or input("Subject: ").strip()
        if args.body_file:
            body = Path(args.body_file).read_text(encoding="utf-8")
        elif args.body:
            body = args.body
        else:
            print("Body (end with Ctrl+Z / Ctrl+D on new line):")
            body = sys.stdin.read().strip()

    if not (to and subject and body):
        print("Error: to, subject, and body are required", file=sys.stderr)
        sys.exit(1)

    # Send
    success, result = send_email(to, subject, body, dry_run=args.dry_run)
    log_sent(to, subject, result if success else "FAILED", None if success else result)

    if success:
        status = "OK"
        print(f"[OK] {result}")
    else:
        print(f"[FAILED] {result}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()