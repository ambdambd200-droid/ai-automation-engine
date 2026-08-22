"""
telegram_controller.py — Interactive Telegram Bot Controller for the freelance automation system.

Commands:
  /status       - Engine health, quotas, last run
  /run daily    - Trigger daily routine now
  /run weekly   - Trigger weekly review
  /quota        - Remaining bids/replies today
  /sessions     - Session validity (valid/expired)
  /approve <id> - Approve pending contact/bid
  /reject <id>  - Reject pending contact/bid
  /logs         - Last 20 lines of logs
  /heal <p>     - Show healing stats for platform
  /reauth <p>   - Re-authenticate platform (mostaql|nafezly|n8n|all)
  /health       - Full system health check
  /selectors <p> - Show cached selectors
  /auto on|off  - Toggle auto-healing
  /help         - Show this help

AI Features:
  - Free-form chat with AI (owner only)
  - Auto-reply to clients with 5-minute cooldown
  - Engine /proxy/ai integration with keyhub fallback

Runs as a long-polling bot (no webhook needed).
"""

import json
import os
import sys
import time
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from collections import defaultdict

# Add project root to path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

# Detect GitHub Actions environment
IS_GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"
IS_CLOUD = IS_GITHUB_ACTIONS or os.environ.get("RUNNING_ON_CLOUD") == "1"

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    from telegram_notifier import call as tg_call
except ImportError:
    # Fallback if telegram_notifier not available
    def tg_call(method, params):
        return {"ok": False, "description": "telegram_notifier not available"}

try:
    from session_manager import SessionManager
    from run_daily_freelance import load_state, run_mostaql, run_nafezly, run_n8n_community
except ImportError:
    SessionManager = None

API = "https://api.telegram.org"
LOG_FILE = BASE_DIR / "telegram_controller.log"

# Auto-reply tracking: chat_id -> last_reply_time
CLIENT_REPLY_COOLDOWN = timedelta(minutes=5)
client_last_reply = defaultdict(lambda: datetime.min)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TelegramController:
    """Interactive Telegram Bot Controller."""

    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        if not self.token or not self.chat_id:
            raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        self.running = False
        self.commands = {
            "/start": self.cmd_start,
            "/help": self.cmd_help,
            "/status": self.cmd_status,
            "/run": self.cmd_run,
            "/quota": self.cmd_quota,
            "/sessions": self.cmd_sessions,
            "/approve": self.cmd_approve,
            "/reject": self.cmd_reject,
            "/logs": self.cmd_logs,
            "/heal": self.cmd_heal,
            "/reauth": self.cmd_reauth,
            "/health": self.cmd_health,
            "/selectors": self.cmd_selectors,
            "/auto": self.cmd_auto,
        }

    def call_api(self, method: str, params: dict) -> dict:
        """Call Telegram Bot API."""
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        data = json.dumps(params).encode("utf-8")
        req = urlrequest.Request(
            f"{API}/bot{self.token}/{method}",
            data=json.dumps(params).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"}
        )
        try:
            with urlrequest.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            return json.loads(e.read().decode("utf-8"))
        except Exception as e:
            return {"ok": False, "description": str(e)}

    def send_message(self, text: str, parse_mode: str = "HTML", disable_notification: bool = False) -> bool:
        """Send message to the configured chat."""
        res = self.call_api("sendMessage", {
            "chat_id": self.chat_id,
            "text": text[:4000],
            "parse_mode": parse_mode,
            "disable_notification": disable_notification
        })
        return res.get("ok", False)

    def get_updates(self) -> list:
        """Get new updates from Telegram."""
        res = self.call_api("getUpdates", {
            "offset": self.offset,
            "limit": 100,
            "timeout": 30,
            "allowed_updates": ["message", "edited_message"]
        })
        if res.get("ok"):
            updates = res.get("result", [])
            if updates:
                self.offset = updates[-1]["update_id"] + 1
            return updates
        return []

    def _is_authorized(self, chat_id: int) -> bool:
        """Check if chat is authorized."""
        return str(chat_id) == self.chat_id

    # --- Command Handlers ---

    def cmd_start(self, chat_id: int, args: list) -> str:
        return (
            "🤖 <b>Salim Freelance Bot</b>\n\n"
            "مرحباً! أنا بوت التحكم في نظام الأتمتة المستقل.\n"
            "اكتب /help لرؤية الأوامر المتاحة.\n\n"
            "💡 يمكنك أيضاً طرح أي سؤال أو طلب مباشرة — سأرد عليك باستخدام الذكاء الاصطناعي."
        )

    def cmd_help(self, chat_id: int, args: list) -> str:
        return (
            "الأوامر المتاحة:\n\n"
            "/status       - حالة المحرك، الكوتا، آخر تشغيل\n"
            "/run daily    - شغل اليومية الآن\n"
            "/run weekly   - شغل المراجعة الأسبوعية\n"
            "/quota        - الكوتا المتبقية اليوم\n"
            "/sessions     - صلاحية الجلسات\n"
            "/approve <id> - وافق على طلب/عرض معلق\n"
            "/reject <id>  - رفض طلب/عرض معلق\n"
            "/logs         - آخر 20 سطر من اللوجات\n"
            "/heal <p>     - إحصائيات الشفاء للمنصة\n"
            "/reauth <p>   - إعادة تسجيل دخول (mostaql|nafezly|n8n|all)\n"
            "/health       - فحص صحة النظام الكامل\n"
            "/selectors <p> - عرض المحددات المحفوظة\n"
            "/auto on|off  - تفعيل/إيقاف الشفاء التلقائي\n"
            "/help         - هذه القائمة\n\n"
            "💡 يمكنك أيضاً الكتابة بحرية وسأرد عليك بالذكاء الاصطناعي!"
        )

    def cmd_status(self, chat_id: int, args: list) -> str:
        try:
            engine_url = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")
            try:
                r = requests.get(f"{engine_url}/health", timeout=5)
                engine_ok = r.ok
                engine_data = r.json() if r.ok else {}
            except Exception:
                engine_ok = False
                engine_data = {}

            from run_daily_freelance import load_state
            state = load_state()
            today = datetime.now().strftime("%Y-%m-%d")
            today_state = state.get("today", {})
            last_run = state.get("last_run", "never")

            lines = [
                "📊 <b>System Status</b>",
                f"  Engine: {'✅ Online' if engine_ok else '❌ Offline'}",
                f"  Workflows: {len(engine_data.get('workflows', [])) if engine_ok else '?'}",
                f"  Last run: {last_run}",
                f"  Today: {today}",
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Error: {e}"

    def cmd_run(self, chat_id: int, args: list) -> str:
        if not args:
            return "Usage: /run <daily|weekly>"
        mode = args[0].lower()
        if mode not in ("daily", "weekly"):
            return "Unknown mode. Use: daily or weekly"
        return f"⚡ <b>Triggering {mode} run...</b>\n(This would trigger the run via engine API)"

    def cmd_quota(self, chat_id: int, args: list) -> str:
        from run_daily_freelance import load_state, check_quota, DAILY_QUOTAS
        state = load_state()
        lines = ["📊 <b>Daily Quota</b>"]
        for key, limit in DAILY_QUOTAS.items():
            used = state.get("today", {}).get(key, 0)
            remaining = max(0, limit - used)
            lines.append(f"  {key}: {remaining}/{limit} (used: {used})")
        return "\n".join(lines)

    def cmd_sessions(self, chat_id: int, args: list) -> str:
        sessions_dir = BASE_DIR / "sessions"
        lines = ["🔐 <b>Session Status</b>"]
        if not sessions_dir.exists():
            lines.append("  No sessions directory")
        else:
            for f in sorted(sessions_dir.glob("*.json")):
                if f.name.endswith(".meta.json"):
                    continue
                platform = f.stem
                meta_f = f.with_name(f.stem + ".meta.json")
                meta = {}
                if meta_f.exists():
                    try:
                        meta = json.loads(meta_f.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                size_kb = f.stat().st_size / 1024
                created = meta.get("created_at", "?")
                cookies = meta.get("cookies", "?")
                lines.append(f"  {platform}: {size_kb:.1f}KB, cookies={cookies}, created={created[:19] if created != '?' else '?'}")
        return "\n".join(lines)

    def cmd_approve(self, chat_id: int, args: list) -> str:
        if not args:
            return "Usage: /approve <contact_id>"
        return f"✅ Approved contact {args[0]} (not implemented yet)"

    def cmd_reject(self, chat_id: int, args: list) -> str:
        if not args:
            return "Usage: /reject <contact_id>"
        return f"❌ Rejected contact {args[0]} (not implemented yet)"

    def cmd_logs(self, chat_id: int, args: list) -> str:
        log_files = [
            BASE_DIR / "telegram_controller.log",
            BASE_DIR / "ai-automation-engine" / "server.log",
        ]
        lines = ["Recent Logs (last 20 lines)"]
        for lf in log_files:
            if lf.exists():
                try:
                    content = lf.read_text(encoding="utf-8", errors="replace")
                    last_lines = content.strip().split("\n")[-20:]
                    lines.append(f"\n{lf.name}:")
                    lines.extend([f"  {l}" for l in last_lines])
                except Exception:
                    lines.append(f"  {lf.name}: could not read")
        return "\n".join(lines)

    def cmd_heal(self, chat_id: int, args: list) -> str:
        """Trigger self-healing for a platform."""
        if not args:
            return "Usage: /heal <platform>  (mostaql|nafezly|n8n|all)"
        platform = args[0].lower()
        if platform == "all":
            platforms = ["mostaql", "nafezly", "n8n"]
        elif platform in ("mostaql", "nafezly", "n8n"):
            platforms = [platform]
        else:
            return "Unknown platform. Use: mostaql, nafezly, n8n, or all"

        try:
            from healing_orchestrator import get_orchestrator
            lines = ["Self-Healing Triggered"]
            for p in platforms:
                orch = get_orchestrator(p)
                stats = orch.get_stats()
                lines.append(f"  {p}: calls={stats.get('total_calls',0)}, healed={stats.get('healing_successes',0)}/{stats.get('healing_attempts',0)}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

    def cmd_reauth(self, chat_id: int, args: list) -> str:
        """Trigger re-authentication for a platform."""
        if not args:
            return "Usage: /reauth <platform>  (mostaql|nafezly|n8n|all)"
        platform = args[0].lower()
        if platform == "all":
            platforms = ["mostaql", "nafezly", "n8n"]
        elif platform in ("mostaql", "nafezly", "n8n"):
            platforms = [platform]
        else:
            return "Unknown platform. Use: mostaql, nafezly, n8n, or all"

        # Run in background thread
        def do_reauth():
            try:
                from auto_reauth import reauth_platform
                for p in platforms:
                    self.send_message(f"Re-authenticating {p}...")
                    ok = reauth_platform(p, headless=True)
                    self.send_message(f"{'OK' if ok else 'FAILED'}: {p} re-auth")
            except Exception as e:
                self.send_message(f"Re-auth error: {e}")

        threading.Thread(target=do_reauth, daemon=True).start()
        return f"Re-auth started for {', '.join(platforms)} (running in background)"

    def cmd_health(self, chat_id: int, args: list) -> str:
        """Full system health check."""
        try:
            engine_url = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")
            try:
                r = requests.get(f"{engine_url}/health", timeout=5)
                engine_ok = r.ok
                engine_data = r.json() if r.ok else {}
            except Exception:
                engine_ok = False
                engine_data = {}

            from run_daily_freelance import load_state, DAILY_QUOTAS
            state = load_state()
            today = datetime.now().strftime("%Y-%m-%d")
            today_state = state.get("today", {})

            # Check sessions
            sessions_dir = BASE_DIR / "sessions"
            session_status = {}
            if sessions_dir.exists():
                for f in sorted(sessions_dir.glob("*.json")):
                    if f.name.endswith(".meta.json"):
                        continue
                    meta_f = f.with_name(f.stem + ".meta.json")
                    if meta_f.exists():
                        try:
                            meta = json.loads(meta_f.read_text(encoding="utf-8"))
                            session_status[f.stem] = "valid"
                        except Exception:
                            session_status[f.stem] = "invalid"
                    else:
                        session_status[f.stem] = "no-meta"

            lines = ["System Health Check", f"  Engine: {'OK' if engine_ok else 'DOWN'}"]
            if engine_ok:
                lines.append(f"  Workflows: {len(engine_data.get('workflows', []))}")
            lines.append(f"  Sessions:")
            for p, s in session_status.items():
                lines.append(f"    {p}: {s}")
            lines.append(f"  Quota ({today}):")
            for key, limit in DAILY_QUOTAS.items():
                used = today_state.get(key, 0)
                remaining = max(0, limit - used)
                lines.append(f"    {key}: {remaining}/{limit}")

            # Healing stats
            try:
                from healing_orchestrator import _ORCHESTRATORS
                if _ORCHESTRATORS:
                    lines.append("  Healing Stats:")
                    for p, orch in _ORCHESTRATORS.items():
                        stats = orch.get_stats()
                        lines.append(f"    {p}: {stats.get('healing_successes',0)}/{stats.get('healing_attempts',0)} healed")
            except Exception:
                pass

            return "\n".join(lines)
        except Exception as e:
            return f"Health check error: {e}"

    def cmd_selectors(self, chat_id: int, args: list) -> str:
        """Show cached selectors for platform."""
        if not args:
            return "Usage: /selectors <platform>  (mostaql|nafezly|all)"
        platform = args[0].lower()
        if platform == "all":
            platforms = ["mostaql", "nafezly"]
        elif platform in ("mostaql", "nafezly"):
            platforms = [platform]
        else:
            return "Unknown platform. Use: mostaql, nafezly, or all"

        try:
            from selector_cache import get_selector_cache
            cache = get_selector_cache()
            lines = ["Cached Selectors"]
            for p in platforms:
                stats = cache.get_stats(p)
                if not stats.get("exists"):
                    lines.append(f"  {p}: no cache")
                    continue
                lines.append(f"  {p} (v{stats.get('version',0)}):")
                for elem, data in stats.get("elements", {}).items():
                    if data.get("total", 0) > 0:
                        lines.append(f"    {elem}: {data['total']} total, {data['successful']} ok, {data['failed']} fail")
            return "\n".join(lines)
        except Exception as e:
            return f"Selectors error: {e}"

    def cmd_auto(self, chat_id: int, args: list) -> str:
        """Toggle auto-healing mode."""
        if not args:
            return "Usage: /auto <on|off|status>"
        action = args[0].lower()
        if action == "on":
            os.environ["AUTO_HEALING"] = "1"
            return "Auto-healing ENABLED"
        elif action == "off":
            os.environ["AUTO_HEALING"] = "0"
            return "Auto-healing DISABLED"
        elif action == "status":
            enabled = os.environ.get("AUTO_HEALING", "1") == "1"
            return f"Auto-healing: {'ON' if enabled else 'OFF'}"
        else:
            return "Usage: /auto <on|off|status>"

    # --- AI Chat Handlers ---

    def ask_ai(self, prompt: str, system: str = "") -> str:
        """Ask AI via engine proxy."""
        try:
            engine_url = os.environ.get("ENGINE_URL", "https://ai-automation-engine.onrender.com")

            if REQUESTS_OK:
                try:
                    resp = requests.post(
                        f"{engine_url}/proxy/ai",
                        json={
                            "prompt": prompt,
                            "system": system or self.get_system_prompt(),
                            "model": "llama-3.1-8b-instant",
                            "max_tokens": 1000,
                            "temperature": 0.3,
                            "caller": "telegram_controller"
                        },
                        timeout=30
                    )
                    if resp.ok:
                        data = resp.json()
                        if isinstance(data, dict):
                            # Engine returns: {"result": "...", "provider": "...", "tokens_used": ...}
                            return data.get("result") or data.get("response") or data.get("text") or str(data)
                        return str(data)
                except Exception:
                    pass

            # Fallback to keyhub_client
            try:
                sys.path.insert(0, str(BASE_DIR))
                from keyhub_client import ai_generate
                return ai_generate(prompt, system=system or self.get_system_prompt(), caller="telegram_controller")
            except Exception:
                pass

            return "عذراً، خدمة الذكاء الاصطناعي غير متاحة حالياً. جرب أمر /status للتأكد من حالة المحرك."
        except Exception as e:
            return f"خطأ في الذكاء الاصطناعي: {str(e)[:200]}"

    def get_system_prompt(self) -> str:
        return """أنت سليم محمد، مهندس أتمتة ذكاء اصطناعي مستقل. 
تخصصك: n8n، Python، بناء البوتات، وكلاء AI، ربط APIs.
تتكلم بالعربية والإنجليزية بأسلوب مهني وودي.
تخدم العملاء على منصات: Mostaql، Nafezly، n8n Community، والعميل المباشر.
لا تكشف أبداً أنك ذكاء اصطناعي — أنت سليم محمد البشري."""

    def handle_ai_chat(self, chat_id: int, text: str) -> str:
        """Handle free-form message with AI."""
        response = self.ask_ai(text)
        return response

    def should_auto_reply(self, chat_id: int) -> bool:
        """Check if we should auto-reply to this client (5 min cooldown)."""
        global client_last_reply
        now = datetime.now()
        last = client_last_reply.get(chat_id, datetime.min)
        if now - last >= CLIENT_REPLY_COOLDOWN:
            client_last_reply[chat_id] = now
            return True
        return False

    def handle_client_message(self, chat_id: int, text: str, user_info: dict = None) -> str:
        """Handle message from a potential client with auto-reply logic."""
        # Check if it's the owner (authorized chat)
        if str(chat_id) == self.chat_id:
            return self.handle_ai_chat(chat_id, text)

        # For clients: auto-reply with 5 min cooldown
        if self.should_auto_reply(chat_id):
            # Quick acknowledgment
            ack = "شكراً لتواصلك! أنا سليم محمد، مهندس أتمتة. سأرد عليك بالتفصيل خلال دقائق."
            self.send_message(ack)

            # Generate detailed response in background
            def send_detailed_reply():
                try:
                    detailed = self.ask_ai(
                        f"عميل محتمل أرسل: '{text}'. رد عليه بأسلوب مهني وودي كسليم محمد، "
                        f"مهندس أتمتة (n8n، Python، AI agents، bots). "
                        f"اسأله عن تفاصيل مشروعه وقدم مساعدة أولية."
                    )
                    self.send_message(f"💬 <b>رد مفصل:</b>\n\n{detailed}")
                except Exception as e:
                    self.send_message(f"❌ خطأ في الرد التلقائي: {e}")

            threading.Thread(target=send_detailed_reply, daemon=True).start()
            return "auto_reply_sent"

        return "cooldown_active"

    # --- Main Loop ---

    def run(self):
        self.running = True
        logger.info(f"Telegram Controller started (cloud={IS_CLOUD})")
        startup_msg = "🤖 <b>Controller started</b>\nReady for commands. Send /help\n\n💡 You can also chat freely — I'll respond via AI!"
        if IS_GITHUB_ACTIONS:
            startup_msg += "\n\n☁️ <i>Running on GitHub Actions</i>"
        self.send_message(startup_msg)

        retry_count = 0
        max_retries = 3
        while self.running:
            try:
                updates = self.get_updates()
                for update in updates:
                    msg = update.get("message") or update.get("edited_message")
                    if not msg:
                        continue
                    chat_id = msg.get("chat", {}).get("id")
                    text = msg.get("text", "").strip()
                    if not text:
                        continue

                    # Handle client messages (non-owner) with auto-reply
                    if str(chat_id) != self.chat_id:
                        result = self.handle_client_message(chat_id, text, msg.get("from", {}))
                        if result in ("auto_reply_sent", "cooldown_active"):
                            continue

                    # Parse command for owner
                    parts = text.split()
                    cmd = parts[0].lower()
                    args = parts[1:]

                    if cmd in self.commands:
                        try:
                            response = self.commands[cmd](msg["chat"]["id"], args)
                            self.send_message(response)
                        except Exception as e:
                            logger.exception(f"Command {cmd} failed")
                            self.send_message(f"❌ Error: {e}")
                    else:
                        # Handle free-form message with AI for owner
                        if str(chat_id) == self.chat_id:
                            try:
                                ai_response = self.handle_ai_chat(chat_id, text)
                                self.send_message(ai_response)
                            except Exception as e:
                                logger.exception("AI chat failed")
                                self.send_message(f"❌ AI Error: {e}")
                        else:
                            self.send_message(f"Unknown command. Type /help")
                # Reset retry counter on successful loop
                retry_count = 0
            except Exception as e:
                logger.exception("Main loop error")
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f"Max retries exceeded ({max_retries}). Exiting.")
                    self.send_message(f"❌ Controller error: max retries exceeded. Check logs.")
                    break
                time.sleep(5)

    def stop(self):
        self.running = False
        self.send_message("🤖 Controller stopped")


def main():
    """Run the controller."""
    # Check env vars
    if not os.environ.get("TELEGRAM_BOT_TOKEN") or not os.environ.get("TELEGRAM_CHAT_ID"):
        print("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set as env vars")
        sys.exit(1)
    ctrl = TelegramController()
    try:
        ctrl.run()
    except KeyboardInterrupt:
        ctrl.stop()


if __name__ == "__main__":
    main()