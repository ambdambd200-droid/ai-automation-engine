"""Debug sentry.py startup - finds where it hangs."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def log(msg):
    print(f"[DEBUG] {msg}", flush=True)

log("1. Starting...")

WORKSPACE = r'C:\Users\A\Desktop\Money'
sys.path.insert(0, WORKSPACE)
sys.path.insert(0, WORKSPACE + '/skills')

log("2. Paths set")

try:
    from quota import can_send, record_sent
    log("3. quota imported OK")
except Exception as e:
    log(f"3. quota IMPORT FAILED: {e}")

try:
    from skills.manager import find_best_skill, apply_skill
    log("4. skills.manager imported OK")
except Exception as e:
    log(f"4. skills.manager IMPORT FAILED: {e}")

try:
    import keyhub_client
    log("5. keyhub_client imported OK")
except Exception as e:
    log(f"5. keyhub_client IMPORT FAILED: {e}")

try:
    from gtts import gTTS
    log("6. gtts imported OK")
except Exception as e:
    log(f"6. gtts IMPORT FAILED: {e}")

log("7. Testing playwright...")
try:
    from playwright.sync_api import sync_playwright
    log("8. playwright imported OK")
except Exception as e:
    log(f"8. playwright IMPORT FAILED: {e}")

log("9. All imports done. Starting browser...")
try:
    pw = sync_playwright().start()
    log("10. Playwright started")
    
    BRAVE_EXE = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
    BRAVE_PROFILE = r'C:\Users\A\AppData\Local\BraveSoftware\Brave-Browser\User Data'
    
    log("11. Launching Brave context...")
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=BRAVE_PROFILE,
        executable_path=BRAVE_EXE,
        headless=False,
        args=['--no-sandbox'],
        viewport={'width': 1366, 'height': 768})
    log("12. Brave context launched")
    
    page = ctx.new_page()
    log("13. Page created")
    
    log("14. Navigating to mostaql.com...")
    page.goto('https://mostaql.com', wait_until='domcontentloaded')
    log(f"15. Mostaql loaded: {page.url}")
    
    ctx.close()
    pw.stop()
    log("16. Done!")
except Exception as e:
    import traceback
    log(f"ERROR: {e}")
    log(traceback.format_exc())
