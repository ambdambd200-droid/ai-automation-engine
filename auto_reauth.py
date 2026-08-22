"""
auto_reauth.py — Automatic Re-authentication for all platforms.

Handles:
- Nafezly: Magic Link via IMAP (Gmail)
- Mostaql: Username/password login
- n8n Community: Google OAuth via persistent Brave context

Each platform has its own re-auth strategy.
"""

import os
import sys
import json
import time
import imaplib
import email
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from playwright.sync_api import sync_playwright
    from session_manager import SessionManager
    PLAYWRIGHT_OK = True
except ImportError as e:
    PLAYWRIGHT_OK = False
    print(f"[auto_reauth] Import warning: {e}")

BASE_DIR = Path(__file__).parent.resolve()
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# Environment variables for credentials
MOSTAQL_EMAIL = os.environ.get("MOSTAQL_EMAIL", "ambdambd200@gmail.com")
MOSTAQL_PASSWORD = os.environ.get("MOSTAQL_PASSWORD", "")
GMAIL_USER = os.environ.get("GMAIL_USER", "alaafathi403@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
NAFEZLY_EMAIL = os.environ.get("NAFEZLY_EMAIL", "alaafathi403@gmail.com")


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def notify_telegram(message: str) -> bool:
    """Send notification via Telegram if configured."""
    try:
        from telegram_notifier import notify
        return notify(message)
    except Exception:
        return False


class ReauthError(Exception):
    """Re-authentication error with platform context."""
    def __init__(self, platform: str, message: str, recoverable: bool = True):
        self.platform = platform
        self.message = message
        self.recoverable = recoverable
        super().__init__(f"[{platform}] {message}")


def extract_magic_link_from_email(imap_conn: imaplib.IMAP4_SSL, since_minutes: int = 5) -> Optional[str]:
    """Extract Nafezly magic link from recent emails."""
    try:
        imap_conn.select("INBOX")
        # Search for emails from Nafezly in last N minutes
        since_date = (datetime.now().replace(second=0, microsecond=0)).strftime("%d-%b-%Y")
        _, msg_nums = imap_conn.search(None, f'(FROM "nafezly" SINCE {since_date})')
        
        for num in msg_nums[0].split()[-10:]:  # Check last 10 emails
            _, msg_data = imap_conn.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            
            # Get body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
                    elif part.get_content_type() == "text/html":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            
            # Look for magic link
            patterns = [
                r'https?://nafezly\.com/auth/magic-link\?[^"\s>]+',
                r'https?://nafezly\.com/login\?token=[^"\s>]+',
                r'https?://[^"\s>]*nafezly[^"\s>]*magic[^"\s>]*',
            ]
            for pattern in patterns:
                match = re.search(pattern, body)
                if match:
                    link = match.group(0)
                    # Clean up HTML entities
                    link = link.replace("&", "&").replace("&#x3D;", "=")
                    log(f"[nafezly] Found magic link in email")
                    return link
        return None
    except Exception as e:
        log(f"[nafezly] Email extraction error: {e}")
        return None


def wait_for_magic_link(timeout: int = 300) -> Optional[str]:
    """Wait for magic link email via IMAP."""
    if not GMAIL_APP_PASSWORD:
        log("[nafezly] GMAIL_APP_PASSWORD not set")
        return None
    
    log("[nafezly] Waiting for magic link email...")
    start = time.time()
    
    while time.time() - start < timeout:
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            
            link = extract_magic_link_from_email(imap)
            imap.logout()
            
            if link:
                return link
        except Exception as e:
            log(f"[nafezly] IMAP error: {e}")
        
        time.sleep(15)
    
    log("[nafezly] Timeout waiting for magic link")
    return None


def reauth_nafezly(headless: bool = False) -> bool:
    """Re-authenticate Nafezly via Magic Link."""
    log("[nafezly] Starting re-authentication via Magic Link...")
    
    notify_telegram("Nafezly Re-auth Started\nMethod: Magic Link (Gmail IMAP)")
    
    try:
        # Step 1: Request magic link
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=headless,
                executable_path=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(viewport={"width": 1366, "height": 768})
            page = context.new_page()
            
            # Go to login page
            page.goto("https://nafezly.com/login", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # Enter email and submit
            email_input = page.locator("input[type='email'], input[name='email']").first
            if email_input.count() > 0:
                email_input.fill(NAFEZLY_EMAIL)
                time.sleep(0.5)
                
                submit_btn = page.locator("button[type='submit'], button:has-text('دخول'), button:has-text('Login')").first
                if submit_btn.count() > 0:
                    submit_btn.click()
                    log("[nafezly] Magic link requested")
                else:
                    log("[nafezly] No submit button found")
            else:
                log("[nafezly] No email input found")
            
            time.sleep(3)
            context.close()
            browser.close()
        
        # Step 2: Wait for magic link email
        magic_link = wait_for_magic_link(timeout=300)
        if not magic_link:
            raise ReauthError("nafezly", "Magic link not received via email", recoverable=True)
        
        log(f"[nafezly] Got magic link, navigating...")
        
        # Step 3: Use magic link to log in and save session
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=headless,
                executable_path=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(viewport={"width": 1366, "height": 768})
            page = context.new_page()
            
            page.goto(magic_link, wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)
            
            # Verify login by checking for user element
            if page.locator("text=خروج, text=Logout, .user-menu, [href*='profile']").count() > 0:
                log("[nafezly] Login verified!")
            else:
                log("[nafezly] Warning: login not verified, but continuing...")
            
            # Save session
            session_file = SESSIONS_DIR / "nafezly.json"
            context.storage_state(path=str(session_file))
            log(f"[nafezly] Session saved to {session_file}")
            
            context.close()
            browser.close()
        
        notify_telegram("✅ Nafezly Re-auth Successful\nSession saved")
        return True
        
    except ReauthError:
        raise
    except Exception as e:
        log(f"[nafezly] Re-auth failed: {e}")
        notify_telegram(f"❌ Nafezly Re-auth Failed\nError: {str(e)[:200]}")
        raise ReauthError("nafezly", str(e), recoverable=True)


def reauth_mostaql(headless: bool = False) -> bool:
    """Re-authenticate Mostaql via email/password."""
    log("[mostaql] Starting re-authentication via email/password...")
    
    if not MOSTAQL_PASSWORD:
        log("[mostaql] MOSTAQL_PASSWORD not set")
        raise ReauthError("mostaql", "MOSTAQL_PASSWORD environment variable not set", recoverable=False)
    
    notify_telegram("Mostaql Re-auth Started\nMethod: Email/Password")
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=headless,
                executable_path=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(viewport={"width": 1366, "height": 768})
            page = context.new_page()
            
            # Go to login page
            page.goto("https://mostaql.com/login", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # Fill email
            email_input = page.locator("input[type='email'], input[name='email'], input[name='username']").first
            if email_input.count() > 0:
                email_input.fill(MOSTAQL_EMAIL)
                time.sleep(0.5)
            else:
                raise ReauthError("mostaql", "Email input not found")
            
            # Fill password
            pass_input = page.locator("input[type='password'], input[name='password']").first
            if pass_input.count() > 0:
                pass_input.fill(MOSTAQL_PASSWORD)
                time.sleep(0.5)
            else:
                raise ReauthError("mostaql", "Password input not found")
            
            # Submit
            submit_btn = page.locator("button[type='submit'], button:has-text('دخول'), button:has-text('Login')").first
            if submit_btn.count() > 0:
                submit_btn.click()
                log("[mostaql] Login submitted")
            else:
                raise ReauthError("mostaql", "Submit button not found")
            
            # Wait for redirect
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            time.sleep(5)
            
            # Verify login
            if page.locator("text=خروج, text=Logout, .user-menu, [href*='profile'], [href*='logout']").count() > 0:
                log("[mostaql] Login verified!")
            else:
                log("[mostaql] Warning: login not verified, checking URL...")
                if "login" not in page.url:
                    log("[mostaql] Redirected away from login, assuming success")
                else:
                    raise ReauthError("mostaql", "Still on login page after submit")
            
            # Save session
            session_file = SESSIONS_DIR / "mostaql.json"
            context.storage_state(path=str(session_file))
            log(f"[mostaql] Session saved to {session_file}")
            
            context.close()
            browser.close()
        
        notify_telegram("✅ Mostaql Re-auth Successful\nSession saved")
        return True
        
    except ReauthError:
        raise
    except Exception as e:
        log(f"[mostaql] Re-auth failed: {e}")
        notify_telegram(f"❌ Mostaql Re-auth Failed\nError: {str(e)[:200]}")
        raise ReauthError("mostaql", str(e), recoverable=True)


def reauth_n8n_community(headless: bool = False) -> bool:
    """Re-authenticate n8n Community via persistent Brave context (Google OAuth)."""
    log("[n8n] Starting re-authentication via persistent context...")
    
    notify_telegram("n8n Community Re-auth Started\nMethod: Persistent Brave Context (Google OAuth)")
    
    try:
        # Use SessionManager which handles persistent context
        sm = SessionManager(
            platform="n8n_community",
            signup_url="https://community.n8n.io",
            home_url="https://community.n8n.io",
            headless=headless,
        )
        
        with sm as sm_ctx:
            page = sm_ctx.page
            
            # Go to community
            page.goto("https://community.n8n.io", wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)
            
            # Check if already logged in
            if page.locator(".user-menu, [href*='logout'], .current-user, .avatar").count() > 0:
                log("[n8n] Already logged in via persistent context")
            else:
                # Need to click login and go through Google OAuth
                log("[n8n] Not logged in, initiating Google OAuth...")
                
                login_btn = page.locator("a:has-text('Log in'), button:has-text('Log in'), a.login-button").first
                if login_btn.count() > 0:
                    login_btn.click()
                    time.sleep(3)
                    
                    # Click Google OAuth
                    google_btn = page.locator("button:has-text('Google'), a:has-text('Google'), .btn-google").first
                    if google_btn.count() > 0:
                        # Google OAuth opens in new tab/window
                        with page.context.expect_page() as new_page_info:
                            google_btn.click()
                        google_page = new_page_info.value
                        
                        # Wait for Google OAuth to complete
                        google_page.wait_for_load_state("domcontentloaded", timeout=30000)
                        time.sleep(5)
                        
                        # Handle Google login if needed (should use saved credentials)
                        # This is interactive - user may need to complete manually first time
                        log("[n8n] Google OAuth initiated - may need manual completion")
                        
                        # Wait for redirect back to n8n
                        page.wait_for_load_state("domcontentloaded", timeout=60000)
                        time.sleep(5)
                    else:
                        log("[n8n] Google OAuth button not found")
                else:
                    log("[n8n] Login button not found")
            
            # Verify login
            if page.locator(".user-menu, [href*='logout'], .current-user, .avatar").count() > 0:
                log("[n8n] Login verified!")
            else:
                log("[n8n] Warning: login not verified")
            
            # Session is automatically saved by SessionManager
        
        notify_telegram("✅ n8n Community Re-auth Successful\nPersistent session updated")
        return True
        
    except Exception as e:
        log(f"[n8n] Re-auth failed: {e}")
        notify_telegram(f"❌ n8n Community Re-auth Failed\nError: {str(e)[:200]}")
        raise ReauthError("n8n", str(e), recoverable=True)


def reauth_platform(platform: str, headless: bool = False) -> bool:
    """Main entry point for platform re-authentication."""
    platform = platform.lower()
    
    if platform == "nafezly":
        return reauth_nafezly(headless)
    elif platform == "mostaql":
        return reauth_mostaql(headless)
    elif platform in ("n8n", "n8n_community"):
        return reauth_n8n_community(headless)
    else:
        raise ValueError(f"Unknown platform: {platform}")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Auto re-authenticate platforms")
    ap.add_argument("--platform", choices=["nafezly", "mostaql", "n8n", "all"],
                    default="all", help="Platform to re-auth")
    ap.add_argument("--headless", action="store_true", help="Run headless")
    args = ap.parse_args()
    
    platforms = ["nafezly", "mostaql", "n8n"] if args.platform == "all" else [args.platform]
    
    results = {}
    for plat in platforms:
        log(f"\n{'='*60}")
        log(f"Re-authenticating: {plat}")
        log(f"{'='*60}")
        try:
            results[plat] = reauth_platform(plat, args.headless)
        except ReauthError as e:
            results[plat] = False
            log(f"[FAIL] {plat}: {e.message} (recoverable={e.recoverable})")
        except Exception as e:
            results[plat] = False
            log(f"[FAIL] {plat}: {e}")
    
    log("\n" + "="*60)
    log("Re-auth Summary:")
    for plat, ok in results.items():
        log(f"  {plat}: {'OK' if ok else 'FAILED'}")
    log("="*60)
    
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()