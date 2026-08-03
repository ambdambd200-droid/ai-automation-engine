"""Engine email sender — Gmail SMTP (free, no domain verification, no third-party).

Replaces Resend Web API. Why Gmail SMTP:
- GMAIL_APP_PASSWORD already configured locally (no setup needed)
- 500 emails/day limit (more than enough for portfolio use)
- Works from any machine (local + GitHub Actions)
- No third-party dependency

Setup (Windows):
    setx GMAIL_APP_PASSWORD "your_app_password"
    setx ENGINE_FROM_EMAIL "alaafathi403@gmail.com"

For personal notifications (engine status, daily digests), use telegram_notifier.py
instead — Telegram is fully free and works without email.
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

FROM_EMAIL = os.environ.get("ENGINE_FROM_EMAIL", "alaafathi403@gmail.com")
FROM_NAME = os.environ.get("ENGINE_FROM_NAME", "Salim Muhammad")


def send_email(to, subject, body, dry_run=False, html=False):
    """Send an email via Gmail SMTP. Returns True on success.

    Args:
        to: recipient email (str or list)
        subject: email subject
        body: email body (plain text or HTML)
        dry_run: if True, print to console instead of sending
        html: if True, send as HTML
    """
    if isinstance(to, str):
        recipients = [to]
    else:
        recipients = list(to)

    if dry_run:
        print(f"[DRY-RUN] From: {FROM_NAME} <{FROM_EMAIL}>")
        print(f"[DRY-RUN] To: {recipients}")
        print(f"[DRY-RUN] Subject: {subject}")
        print(f"[DRY-RUN] Body ({'HTML' if html else 'text'}, {len(body)} chars):\n{body[:300]}...")
        return True

    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not app_password:
        raise RuntimeError(
            "GMAIL_APP_PASSWORD not set. "
            "Get one from https://myaccount.google.com/apppasswords "
            "then: setx GMAIL_APP_PASSWORD \"your_password\""
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))
    msg["To"] = ", ".join(recipients)
    if html:
        msg.attach(MIMEText(body, "html", "utf-8"))
    else:
        msg.attach(MIMEText(body, "plain", "utf-8"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(FROM_EMAIL, app_password)
            server.sendmail(FROM_EMAIL, recipients, msg.as_string())
        return True
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(
            f"Gmail SMTP auth failed. Check GMAIL_APP_PASSWORD is a valid App Password "
            f"(not your normal password). Error: {e}"
        )
    except (smtplib.SMTPException, OSError) as e:
        raise RuntimeError(f"Gmail SMTP error: {e}")
