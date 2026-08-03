"""
Gmail App Password setup verifier.

Tests if GMAIL_APP_PASSWORD env var is set and works.
Does NOT create the password — you must do that in the browser.

Setup (one-time, 2 minutes):
  1. Enable 2FA on ambdambd200@gmail.com if not already
     https://myaccount.google.com/signinoptions/two-step-verification
  2. Go to https://myaccount.google.com/apppasswords
  3. Sign in, app name = "Money Workspace"
  4. Click Create
  5. Copy the 16-char password (looks like "abcd efgh ijkl mnop")
  6. Set env var permanently (Windows):
     - Win+R -> sysdm.cpl -> Advanced -> Environment Variables
     - New (User variable):
         Variable name: GMAIL_APP_PASSWORD
         Variable value: <paste 16-char password>
     - OK, OK
  7. Close + reopen PowerShell
  8. Run: python gmail_setup_check.py

Run:
  python gmail_setup_check.py
"""

import os
import imaplib
import sys

GMAIL_USER = "ambdambd200@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"


def main():
    print("=" * 60)
    print("GMAIL APP PASSWORD SETUP CHECK")
    print("=" * 60)
    print()

    if not GMAIL_APP_PASSWORD:
        print("[FAIL] GMAIL_APP_PASSWORD env var is NOT set.")
        print()
        print("To fix, follow the 8 steps in this file's docstring.")
        print("Or open: https://myaccount.google.com/apppasswords")
        print()
        print("After setting the env var, close + reopen PowerShell,")
        print("then re-run this script.")
        sys.exit(1)

    masked = GMAIL_APP_PASSWORD[:4] + "*" * 8 + GMAIL_APP_PASSWORD[-4:]
    print(f"[OK] GMAIL_APP_PASSWORD is set: {masked}")
    print(f"     Length: {len(GMAIL_APP_PASSWORD)} chars")
    print()

    if len(GMAIL_APP_PASSWORD.replace(" ", "")) != 16:
        print(f"[WARN] Expected 16 chars (with or without spaces). Got {len(GMAIL_APP_PASSWORD)}.")
        print("       The script will still try to connect, but it may fail.")
        print()

    print(f"Testing IMAP connection to {IMAP_SERVER}...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("inbox")
        print(f"[OK] Connected to {GMAIL_USER} inbox")
        mail.logout()
        print()
        print("=" * 60)
        print("SETUP COMPLETE — gmail_check.py will work now.")
        print("=" * 60)
    except Exception as e:
        print(f"[FAIL] Could not connect: {e}")
        print()
        print("Common causes:")
        print("  - 2FA not enabled on the account")
        print("  - Password copied with extra whitespace")
        print("  - Password revoked (create a new one)")
        print("  - Account has unusual security alerts (check email)")
        sys.exit(1)


if __name__ == "__main__":
    main()
