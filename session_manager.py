"""
session_manager.py — Playwright session persistence for freelance platforms.

Pattern:
  1. First run:  opens browser to signup URL, user signs up manually,
                  presses ENTER in terminal, session is saved.
  2. Next runs:  loads saved session, browser opens already logged in.

Usage:
  from session_manager import SessionManager
  with SessionManager("mostaql", signup_url="https://mostaql.com/signup",
                      home_url="https://mostaql.com/") as sm:
      page = sm.page
      # interact with page...

Uses persistent Brave profile (user's actual browser) for Google OAuth platforms.
Uses standard chromium launch with storage_state for other platforms.
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

try:
    from playwright.sync_api import sync_playwright, BrowserContext, Page
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False
    print("[session_manager] ERROR: playwright not installed.", file=sys.stderr)
    print("[session_manager] Run: pip install playwright && playwright install chromium",
          file=sys.stderr)

BASE_DIR = Path(__file__).parent.resolve()
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# Default browser executable and profile.
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

# Platforms that work better with persistent context (Google OAuth)
PERSISTENT_CONTEXT_PLATFORMS = set()  # Empty - use standard chromium for all

HEADLESS = os.environ.get("SESSION_HEADLESS", "false").lower() in ("true", "1", "on")


class SessionManager:
    """
    Wraps Playwright with storage_state persistence OR persistent Brave profile.

    Attributes:
        platform: short name (e.g. "mostaql")
        signup_url: page to open on first run
        home_url: page to open on subsequent runs (where logged-in user lands)
        session_file: Path to storage_state.json
        page: Playwright Page object (only after __enter__)
    """

    def __init__(self, platform: str, signup_url: str, home_url: str,
                 headless: bool = None, slow_mo_ms: int = 60,
                 wait_for_seconds_after_signup: int = 5):
        self.platform = platform
        self.signup_url = signup_url
        self.home_url = home_url
        self.headless = headless if headless is not None else HEADLESS
        self.slow_mo = slow_mo_ms
        self.wait_after_signup = wait_for_seconds_after_signup
        self.session_file = SESSIONS_DIR / f"{platform}.json"
        self.metadata_file = SESSIONS_DIR / f"{platform}.meta.json"
        self._context = None
        self.page = None
        self._pw = None
        self._is_persistent = False

    def has_session(self) -> bool:
        return self.session_file.exists() and self.session_file.stat().st_size > 100

    def _load_metadata(self) -> dict:
        if self.metadata_file.exists():
            try:
                return json.loads(self.metadata_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_metadata(self, **kwargs):
        meta = self._load_metadata()
        meta.update(kwargs)
        meta["platform"] = self.platform
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.metadata_file.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def __enter__(self):
        if not PLAYWRIGHT_OK:
            raise RuntimeError("Playwright not installed. See error above.")
        self._pw = sync_playwright().start()
        
        # Use persistent Brave profile only for platforms that need Google OAuth
        use_persistent = (
            not self.headless and 
            Path(r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data").exists() and 
            Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe").exists() and
            self.platform in PERSISTENT_CONTEXT_PLATFORMS
        )
        
        if use_persistent:
            print(f"[session_manager:{self.platform}] Using persistent Brave profile (Google OAuth)")
            self._context = self._pw.chromium.launch_persistent_context(
                user_data_dir=r"C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data",
                executable_path=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
                viewport={"width": 1366, "height": 768},
            )
            self._is_persistent = True
            self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
            
            if self.has_session():
                print(f"[session_manager:{self.platform}] Saved session exists; persistent context has cookies.")
                self.page = self._context.new_page()
                try:
                    self.page.goto(self.home_url, wait_until="domcontentloaded", timeout=30000)
                    meta = self._load_metadata()
                    created = meta.get("created_at", "?")
                    print(f"[session_manager:{self.platform}] Opened home page. Session created at {created}")
                    return self
                except Exception as e:
                    print(f"[session_manager:{self.platform}] Navigation error: {e}")
                    print("[session_manager] Continuing with persistent context...")
            else:
                print(f"[session_manager:{self.platform}] Using persistent Brave profile (no saved session)")
                self.page = self._context.new_page()
        else:
            # Standard chromium launch with Brave executable
            print(f"[session_manager:{self.platform}] Using standard chromium launch (Brave executable)")
            launch_kwargs = {"headless": self.headless, "slow_mo": self.slow_mo}
            if not self.headless and Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe").exists():
                launch_kwargs["executable_path"] = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
            elif not self.headless:
                launch_kwargs.pop("executable_path", None)
            browser = self._pw.chromium.launch(**launch_kwargs)
            if self.has_session():
                print(f"[session_manager:{self.platform}] Loading saved session from {self.session_file}")
                self._context = browser.new_context(storage_state=str(self.session_file))
                self.page = self._context.new_page()
                try:
                    self.page.goto(self.home_url, wait_until="domcontentloaded", timeout=30000)
                    meta = self._load_metadata()
                    created = meta.get("created_at", "?")
                    print(f"[session_manager:{self.platform}] Opened home page. Session created at {created}")
                    return self
                except Exception as e:
                    print(f"[session_manager:{self.platform}] Saved session may be invalid: {e}")
                    print("[session_manager] Falling back to fresh signup...")
                    try:
                        self._context.close()
                    except Exception:
                        pass
            # First-run or fallback: open signup URL, let user complete signup
            print(f"\n{'='*60}")
            print(f"[session_manager:{self.platform}] NO SAVED SESSION.")
            print(f"[session_manager:{self.platform}] Opening signup page in visible browser.")
            print(f"[session_manager:{self.platform}] Please complete the signup/login manually.")
            print(f"[session_manager:{self.platform}] After you are logged in and on the platform home,")
            print(f"[session_manager:{self.platform}] come back here and press ENTER to save the session.")
            print(f"{'='*60}\n")
            self._context = browser.new_context()
            self.page = self._context.new_page()
            try:
                self.page.goto(self.signup_url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"[session_manager] Warning: signup_url failed to load: {e}")
            # Give user time to complete signup
            print(f"\nWaiting up to {self.wait_after_signup} minutes for signup completion...")
            print("(Press ENTER here once you are logged in to save the session early,")
            print(" or wait the full timeout.)")
            # Try a short interactive wait first (5 seconds). If no input arrives,
            # fall back to polling the URL until login completes or timeout.
            interactive_succeeded = False
            try:
                import threading
                user_input_holder = [None]
                def read_input():
                    try:
                        user_input_holder[0] = input(">>> Press ENTER after you complete signup/login: ")
                    except EOFError:
                        pass
                t = threading.Thread(target=read_input, daemon=True)
                t.start()
                t.join(timeout=5)
                if user_input_holder[0] is not None:
                    print("[session_manager] Saving session immediately on user input.")
                    interactive_succeeded = True
            except Exception:
                pass
            if not interactive_succeeded:
                print(f"[session_manager] No immediate input — polling page until login completes...")
                # Poll: check if URL has changed from signup page, save when ready.
                deadline = time.time() + (self.wait_after_signup * 60)
                last_url = ""
                while time.time() < deadline:
                    try:
                        if not self.page or self.page.is_closed():
                            break
                        cur_url = self.page.url
                        # Stop polling when we're on a logged-in page
                        if "community.n8n.io" in cur_url and "/session/" not in cur_url \
                           and "/signup" not in cur_url and "/login" not in cur_url \
                           and "accounts.google" not in cur_url:
                            print(f"[session_manager] Detected logged-in page: {cur_url[:80]}")
                            break
                        if cur_url != last_url:
                            print(f"  watching: {cur_url[:80]}")
                            last_url = cur_url
                    except Exception as poll_err:
                        print(f"  poll error: {poll_err}")
                        break
                    time.sleep(2)
                # Wait for the page to settle
                time.sleep(2)
                self._save_session(browser)
                return self
            return self

    def _save_session(self, browser):
        if self._is_persistent:
            print(f"[session_manager:{self.platform}] Persistent context - cookies already saved in Brave profile.")
            return
        state = self._context.storage_state(path=str(self.session_file))
        self._save_metadata(
            created_at=datetime.now(timezone.utc).isoformat(),
            signup_url=self.signup_url,
            home_url=self.home_url,
            cookies=len(state.get("cookies", [])),
            origins=len(state.get("origins", [])),
        )
        print(f"[session_manager:{self.platform}] Saved session to {self.session_file}")
        print(f"[session_manager:{self.platform}] (cookies={len(state.get('cookies', []))}, "
              f"origins={len(state.get('origins', []))})")

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._pw:
                self._pw.stop()
        except Exception:
            pass

    def screenshot(self, name: str = None) -> Path:
        if not self.page:
            raise RuntimeError("Page not initialized. Use 'with' context.")
        name = name or f"{self.platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = BASE_DIR / "screenshots" / name
        path.parent.mkdir(exist_ok=True)
        self.page.screenshot(path=str(path))
        return path

    def save_session_now(self):
        """Save the current session state without exiting."""
        if not self._context:
            raise RuntimeError("Context not initialized.")
        if self._is_persistent:
            print(f"[session_manager:{self.platform}] Persistent context - cookies already saved in Brave profile.")
            return
        state = self._context.storage_state(path=str(self.session_file))
        self._save_metadata(
            updated_at=datetime.now(timezone.utc).isoformat(),
            cookies=len(state.get("cookies", [])),
            origins=len(state.get("origins", [])),
        )
        print(f"[session_manager:{self.platform}] Re-saved session.")


def list_sessions():
    """Print all saved sessions and their metadata."""
    if not SESSIONS_DIR.exists():
        print("No sessions directory.")
        return
    print(f"\n=== Saved Sessions ({SESSIONS_DIR}) ===")
    for f in sorted(SESSIONS_DIR.glob("*.json")):
        if f.name.endswith(".meta.json"):
            continue
        meta_path = f.with_name(f.stem + ".meta.json")
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        size_kb = f.stat().st_size / 1024
        print(f"\n  {f.name} ({size_kb:.1f} KB)")
        for k, v in meta.items():
            print(f"    {k}: {v}")


def delete_session(platform: str):
    """Remove a saved session."""
    sf = SESSIONS_DIR / f"{platform}.json"
    mf = SESSIONS_DIR / f"{platform}.meta.json"
    for p in (sf, mf):
        if p.exists():
            p.unlink()
            print(f"Deleted: {p}")
    print(f"Session for '{platform}' cleared.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Manage saved Playwright sessions")
    ap.add_argument("--list", action="store_true", help="List all saved sessions")
    ap.add_argument("--delete", metavar="PLATFORM", help="Delete a specific session")
    args = ap.parse_args()
    if args.list:
        list_sessions()
    elif args.delete:
        delete_session(args.delete)
    else:
        ap.print_help()