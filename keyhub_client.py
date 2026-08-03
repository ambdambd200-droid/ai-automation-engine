"""
keyhub_client.py — Internal AI gateway client for the Money/ workspace.

Uses the AI Automation Engine's /proxy/ai endpoint as a centralized
key holder. Falls back to direct Groq if the engine is down.
Falls back to local Ollama (phi-3-mini) if both cloud providers fail
(offline mode).

Provider chain (July 23, 2026, card-free):
  1. Engine /proxy/ai (Groq + Gemini)
  2. Direct Groq (bypass engine)
  3. Direct OpenRouter (free `:free` models, 50 req/day)
  4. Google AI Studio (Gemma 3 4B = 14,400 req/day, no card)
  5. Local Ollama (offline fallback, phi-3-mini by default)

Cerebras was tested on 2026-07-23 and EXCLUDED — requires a credit card
even for the "free" tier (402 Payment Required on all models for new
accounts without a card on file).

All providers in the active chain → no credit card required.
Signups: Groq (console.groq.com), OpenRouter (openrouter.ai — 50 free req/day),
Gemma (aistudio.google.com — 14,400 req/day).

Usage:
  from keyhub_client import ai_generate

  text = ai_generate("Your prompt here")
  text = ai_generate("...", provider="groq")
  text = ai_generate("...", provider="openrouter")
  text = ai_generate("...", provider="gemma")  # free 14400/day
  ai_generate(...)  # auto chain

Setup:
  - Engine must be running at 127.0.0.1:5000
  - GROQ_API_KEY, GEMINI_API_KEY at OS level
  - Optional: OPENROUTER_API_KEY (signup, free 50/day)
  - Engine auto-starts via Startup folder VBS
  - Ollama is optional: install once with `winget install Ollama.Ollama`
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _ensure_user_env(keys_to_pull=None):
    """Read User-level env vars from Windows registry into os.environ.

    When a script is launched from a process that hasn't received the
    latest user environment (e.g. opencode shell, vscode terminal after
    a manual setx), `os.environ.get(...)` returns None even though the
    variable is set at the OS level. This helper bridges that gap by
    reading from HKCU\\Environment via winreg.
    """
    if keys_to_pull is None:
        keys_to_pull = ["GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
                        "CEREBRAS_API_KEY", "HUGGINGFACE_API_KEY"]
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as reg:
            for k in keys_to_pull:
                if os.environ.get(k):
                    continue
                try:
                    val, _ = winreg.QueryValueEx(reg, k)
                    if val:
                        os.environ[k] = val
                except FileNotFoundError:
                    pass
    except Exception:
        pass


_ensure_user_env()

ENGINE_URL = os.environ.get("ENGINE_URL", "http://127.0.0.1:5000")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
CEREBRAS_URL = "https://api.cerebras.ai/v1"
OPENROUTER_URL = "https://openrouter.ai/api/v1"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.4
DEFAULT_PROVIDER = os.environ.get("AI_PROVIDER", "auto")
DEFAULT_MODEL = os.environ.get("AI_MODEL", "llama-3.3-70b-versatile")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini-3.8b")
CEREBRAS_DEFAULT_MODEL = os.environ.get("CEREBRAS_MODEL", "gpt-oss-120b")
OPENROUTER_DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
ENABLE_OLLAMA = os.environ.get("DISABLE_OLLAMA", "0") != "1"
DEFAULT_SYSTEM = (
    "You are Salim Muhammad, an AI Automation Engineer and freelance consultant "
    "specializing in n8n, Python, API integrations, and bots. "
    "You write in clear, professional English or Arabic as needed. "
    "Be concise, results-oriented, and friendly. Never mention being an AI. "
    "Always sign off as Salim."
)

CALLER_NAME = Path(sys.argv[0] if sys.argv and sys.argv[0] else "unknown").stem


def _engine_alive() -> bool:
    try:
        import requests
        r = requests.get(f"{ENGINE_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _call_engine(prompt: str, system: str, model: Optional[str], max_tokens: int,
                 temperature: float, provider: str, caller: str) -> Optional[dict]:
    import requests
    try:
        r = requests.post(
            f"{ENGINE_URL}/proxy/ai",
            json={
                "prompt": prompt,
                "system": system,
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "provider": provider,
                "caller": caller,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def _call_groq_direct(prompt: str, system: str, model: Optional[str], max_tokens: int,
                      temperature: float) -> Optional[str]:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        resp = client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None


# ---------- SKILLS-FIRST MODE ----------
def _try_skill(prompt: str) -> Optional[str]:
    """Try to match a local skill template before calling any API.

    Scan skills/index.json for templates that match the prompt. If
    a matching template is found, return its content. Otherwise
    return None (continue to API chain).

    Tier 0 in the chain — $0, offline, no API key needed.
    """
    index_path = Path(__file__).resolve().parent / "skills" / "index.json"
    if not index_path.exists():
        return None
    try:
        idx = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return None

    skills = idx.get("skills", [])
    if not skills:
        return None

    prompt_lower = prompt.lower()
    best = None
    best_score = 0

    # Handle both dict format (skills keyed by name) and list format (skills as list)
    if isinstance(skills, dict):
        skill_items = list(skills.values())
    else:
        skill_items = skills

    for s in skill_items:
        if not isinstance(s, dict):
            continue
        score = 0
        s_name = s.get("name", "").lower()
        s_tags = [t.lower() for t in s.get("tags", [])]
        s_type = s.get("type", "").lower()

        # type match
        if s_type and s_type in prompt_lower.replace("_"," "):
            score += 1

        # tag match
        for tag in s_tags:
            if tag in prompt_lower:
                score += 1
                if tag in ("arabic", "ar", "mostaql", "nafezly"):
                    score += 1  # platform-specific boost extra

        # loose keyword
        keywords = ["bid", "proposal", "cover", "letter", "follow", "up", "n8n",
                    "reply", "forum", "followup", "cold", "nafezly", "mostaql",
                    "snippet", "evaluation", "motivate"]
        for kw in keywords:
            if kw in s_name or kw in (s_tags or []) + [s_type]:
                if kw in prompt_lower:
                    score += 0.5

        if score > best_score:
            best = s
            best_score = score

    if best and best_score >= 1.0:
        skill_path = Path(__file__).resolve().parent / best.get("path", "")
        if skill_path.exists():
            try:
                data = json.loads(skill_path.read_text(encoding="utf-8"))
                template = data.get("template", "")
                if template:
                    print(f"  [SKILL] {best['name']} (tier 0, $0)")
                    return template
            except Exception:
                pass
        print(f"  [SKILL] {best['name']} matched but file missing or empty")
        return None

    return None
# ---------- END SKILLS-FIRST ----------


def _ollama_alive() -> bool:
    """Check if local Ollama server is up (fast probe, 1 sec)."""
    if not ENABLE_OLLAMA:
        return False
    try:
        import requests
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def _call_ollama(prompt: str, system: str, model: Optional[str], max_tokens: int,
                 temperature: float) -> Optional[str]:
    """Call local Ollama (offline fallback).

    Uses the OpenAI-compatible /v1/chat/completions endpoint exposed
    by Ollama 0.3.3+. This makes the API identical to Groq/OpenAI.
    """
    if not _ollama_alive():
        return None
    use_model = model or OLLAMA_MODEL
    try:
        from openai import OpenAI
        client = OpenAI(api_key="ollama", base_url=f"{OLLAMA_URL}/v1")
        resp = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=DEFAULT_TIMEOUT,
        )
        text = resp.choices[0].message.content.strip()
        if text:
            print(f"  [OLLAMA] Used {use_model} (offline)")
        return text
    except Exception as e:
        print(f"  [OLLAMA ERROR] {e}")
        return None


def ai_generate(
    prompt: str,
    system: str = DEFAULT_SYSTEM,
    model: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    provider: str = DEFAULT_PROVIDER,
    caller: Optional[str] = None,
) -> Optional[str]:
    """Generate text via the internal AI gateway.

    Tries providers in order:
      1. Engine (cloud or local) — /proxy/ai endpoint
      2. Direct Groq — bypasses engine
      3. Direct Cerebras — OpenAI-compatible, 14,400 req/day free
      4. Direct OpenRouter — routes to any `:free` model, 50-1000 req/day
      5. Local Ollama — offline fallback (phi-3-mini by default)

    Force a specific provider by setting `provider="ollama"`, "groq",
    "cerebras", "openrouter", etc.
    Set provider="auto" for the default chain above.
    Returns the generated text, or None if all providers fail.
    """
    if not prompt or not prompt.strip():
        return None
    caller = caller or CALLER_NAME
    provider = (provider or "auto").lower()

    if provider == "ollama":
        return _call_ollama(prompt.strip(), system, model, max_tokens, temperature)

    # OpenRouter deferred until a key is set (free signup, no card)
    if provider == "openrouter":
        _ensure_user_env()
        if not os.environ.get("OPENROUTER_API_KEY"):
            print("  [OPENROUTER] No key set (free signup at openrouter.ai) — skipped")
            return None
        return _call_openrouter_direct(prompt, system, model, max_tokens, temperature)

    # Cerebras = dead end (needs card)
    if provider == "cerebras":
        print("  [CEREBRAS] Disabled (needs credit card — user chose skills-first path)")
        return None

    if provider in ("auto", "groq", "gemini", ""):
        # TIER 0: Skills library ($0, offline, always first)
        if provider == "auto":
            skill = _try_skill(prompt.strip())
            if skill:
                return skill

        # TIER 1: Engine (Groq + Gemini via proxy)
        if _engine_alive():
            result = _call_engine(
                prompt.strip(), system, model, max_tokens, temperature,
                "gemini" if provider == "gemini" else provider, caller,
            )
            if result and "result" in result:
                return result["result"]

        # TIER 2: Direct Groq
        direct = _call_groq_direct(prompt, system, model, max_tokens, temperature)
        if direct:
            return direct

        # TIER 3: Local Ollama (offline, optional)
        if provider == "auto":
            ollama_out = _call_ollama(
                prompt.strip(), system, model, max_tokens, temperature
            )
            if ollama_out:
                return ollama_out

    return None


def ai_generate_json(
    prompt: str,
    system: str = DEFAULT_SYSTEM,
    model: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.2,
    **kwargs,
) -> Optional[dict]:
    """Like ai_generate, but parses the response as JSON."""
    text = ai_generate(prompt, system=system, model=model,
                       max_tokens=max_tokens, temperature=temperature, **kwargs)
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip().startswith("```") else "\n".join(lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def get_stats(days: int = 7) -> dict:
    """Get proxy usage stats from the engine."""
    import requests
    try:
        r = requests.get(f"{ENGINE_URL}/proxy/stats?days={days}", timeout=5)
        return r.json() if r.status_code == 200 else {"error": "engine not reachable"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test the keyhub client")
    parser.add_argument("--prompt", default="Say 'hello from keyhub' in 5 words or less.")
    parser.add_argument("--stats", action="store_true", help="Show proxy stats")
    parser.add_argument("--provider", default="auto", help="auto|groq|gemini|cerebras|openrouter|ollama")
    parser.add_argument("--ollama-only", action="store_true", help="Force Ollama fallback only")
    parser.add_argument("--ollama-status", action="store_true", help="Show Ollama status")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions for Cerebras/OpenRouter signups")
    args = parser.parse_args()

    if args.ollama_status:
        alive = _ollama_alive()
        print(f"Ollama alive: {alive}")
        print(f"Ollama URL: {OLLAMA_URL}")
        print(f"Default model: {OLLAMA_MODEL}")
        if alive:
            try:
                import requests
                r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
                tags = r.json().get("models", [])
                print(f"Available models ({len(tags)}):")
                for t in tags:
                    print(f"  - {t.get('name')}")
            except Exception as e:
                print(f"  (could not list models: {e})")
    elif args.setup:
        print("=== Free LLM API Setup ===\n")
        print("Already configured:")
        print(f"  GROQ_API_KEY: {'YES' if os.environ.get('GROQ_API_KEY') else 'NO — set it'}")
        print(f"  GEMINI_API_KEY: {'YES' if os.environ.get('GEMINI_API_KEY') else 'NO — set it'}\n")
        print("To add:")
        print("  Cerebras (14400 req/day free):")
        print("    1. Signup: https://cloud.cerebras.ai")
        print("    2. Get API key from dashboard")
        print("    3. Set: [System.Environment]::SetEnvironmentVariable('CEREBRAS_API_KEY','key','User')\n")
        print("  OpenRouter (50-1000 req/day free):")
        print("    1. Signup: https://openrouter.ai")
        print("    2. Get API key from https://openrouter.ai/keys")
        print("    3. Set: [System.Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY','key','User')\n")
        print("Then run any generate command. The chain is:")
        print("  1. Engine /proxy/ai (Gemini primary / Groq fallback)")
        print("  2. Direct Groq")
        print("  3. Direct Cerebras (if CEREBRAS_API_KEY set)")
        print("  4. Direct OpenRouter (if OPENROUTER_API_KEY set)")
        print("  5. Ollama (if running)")
    elif args.ollama_only:
        print("Engine alive:", _engine_alive())
        print("Ollama alive:", _ollama_alive())
        print(f"Prompt: {args.prompt}")
        result = ai_generate(args.prompt, provider="ollama", caller="keyhub_test")
        print(f"Result: {result}")
    elif args.stats:
        print(json.dumps(get_stats(), indent=2))
    else:
        print(f"Engine alive: {_engine_alive()}")
        print(f"Ollama alive: {_ollama_alive()}")
        print(f"Provider: {args.provider}")
        print(f"Prompt: {args.prompt}")
        result = ai_generate(args.prompt, provider=args.provider, caller="keyhub_test")
        print(f"Result: {result}")
