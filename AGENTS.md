# AGENTS.md — Money/ workspace

## What this repo is

Freelance-business workspace for **Salim Muhammad** (AI Automation Engineer). Three purposes:

1. **Public portfolio** (root .md files) — GitHub README, LinkedIn content, Upwork profile
2. **Internal system** (root .py + .md) — job queue, application pipeline, Gmail check, daily routine
3. **AI Automation Engine** (`ai-automation-engine/`) — self-hosted Flask app that runs YAML-defined AI workflows via webhooks

Treat the workspace as production code: changes to `ai-automation-engine/` are real, changes to root .md files ship to clients.

## Layout (verified 2026-06-04)

```
Money/
├── AGENTS.md                              # This file
├── README.md                              # GitHub portfolio — 3 projects
├── Alaa_Fathi_CV.md                       # [LEGACY — used original Arabic name] Bilingual CV — SALIM_MUHAMMAD_CV.md is current identity
├── SALIM_MUHAMMAD_CV.md                   # Current CV (Salim Muhammad identity)
├── salim_profile.json                     # Single source of truth: identity, bio, skills, rates
├── Proposal_Templates.md                  # 3 proposal variants
├── Application_Pipeline.md                # Single source of truth (6 sent + 3 forum drafts)
├── Job_Queue.md                           # 3 forum posts queued (slots 11-13)
├── Protocols.md                           # When to ask vs when to act, security, cost
├── Prompt_Library.md                      # 6 working prompts
├── Upwork_Profile_Content.md              # Prepared Upwork profile
├── Upwork_Signup_Steps.md                 # Manual 15-min walkthrough
├── LinkedIn_Profile_Content.md            # LinkedIn EN+AR profile copy
├── LinkedIn_Posts_Series.md               # 3 posts scheduled Jun 5, 8, 12
├── LinkedIn_Application_Talent_Blueprint.md  # Sent app (Talent Blueprint)
├── Application_N8N_Community_mkitplug.md  # Draft reply: Figma → n8n plugin thread
├── Application_N8N_Community_easybits.md  # Draft reply: Recruiter LinkedIn workflow
├── Application_N8N_Community_Doru_Gradinaru.md  # Draft reply: Guard workflow
├── Mostaql_Setup.md                      # Signup + profile guide (mostaql.com)
├── Nafezly_Setup.md                      # Signup + profile guide (nafezly.com)
├── Arabic_Bid_Templates.md               # 5 bid templates in Arabic
├── apply_now.py                           # Opens N application URLs in Brave
├── daily.py                               # One-command daily routine
├── gmail_check.py                         # IMAP reply check (needs GMAIL_APP_PASSWORD)
├── gmail_setup_check.py                   # Verifies Gmail env var + IMAP connection
├── gmail_log.md                           # Append-only Gmail check log
├── job_scanner.py                         # URL-based job scoring (BeautifulSoup)
├── send_applications.py                   # SMTP-based email send (dry-run tested)
├── sent_applications.log                  # Dry-run log (no real sends recorded)
├── post_forum_replies.py                  # Playwright: post 3 n8n Community replies
├── signup_arabic_platforms.py             # Playwright: signup on Mostaql + Nafezly
├── desktop_runner.py                      # pyautogui: generic desktop automation
├── desktop_tasks.json                     # Task list for desktop_runner.py
├── hunt.py                                # Daily freelance hunter (AI-in-the-loop) — Arabic + Foreign fronts; --learn mode auto-saves sent items as skills
├── keyhub_client.py                       # Internal AI gateway client (routes through engine /proxy/ai, falls back to direct Groq; Ollama slot ready if installed)
├── quota.py                               # Daily quota tracker — single source of truth for "can I send N of X today" (used by hunt, send_applications, future scripts)
├── hunt_state.json                        # State for hunt.py + quota.py (sent, daily counters) [gitignored]
├── skills/                                # Skills library — reusable templates (June 7, 2026)
│   ├── manager.py                         # Read/find/apply/save/learn
│   ├── index.json                         # Master index of all skills
│   ├── arabic_bid/mostaql.json            # Arabic Mostaql bid template
│   ├── arabic_bid/nafezly.json            # Arabic Nafezly bid template
│   ├── email_followup/english_cold.json   # English follow-up template
│   ├── email_followup/arabic_ar.json      # Arabic follow-up template
│   ├── email_reply/professional_en.json   # English reply template
│   ├── email_reply/arabic_ar.json         # Arabic reply template
│   ├── email_reply/cold_pitch.json        # Cold outreach pitch
│   ├── forum_reply/technical_n8n.json     # Technical n8n forum reply
│   ├── forum_reply/showcase.json          # Portfolio showcase reply
│   ├── linkedin/connection_request.json   # LinkedIn cold outreach
│   ├── upwork/cover_letter.json           # Upwork proposal
│   ├── service_page/nafezly.json          # Nafezly service page
│   └── learning/                          # Auto-learned skills (run `hunt.py --learn`)
├── hunt_context.md                        # GATHER output — read this in chat to make decisions
├── hunt_decisions.md                      # Your decisions (write in chat, run --execute to send)
├── hunter_drafts.md                       # [legacy] AI-generated drafts from --auto mode
├── hunter.log                             # hunt.py log
├── hunter_sent.log                        # hunt.py send log
├── hunter_screenshots/                    # Screenshots from hunt.py browser runs
├── UptimeRobot_Setup.md                   # Render uptime keeper (5 min setup, free)
├── .gitignore                             # Standard Python exclusions
└── ai-automation-engine/
    ├── app.py                             # Flask entry — runs :5000
    ├── config.yaml                        # Engine config (server, db, workflows_dir)
    ├── requirements.txt
    ├── .env.example                       # Template; real env vars set at OS level
    ├── start_engine.bat                   # Visible-window start (manual)
    ├── start_engine_hidden.vbs            # Hidden start (Windows auto-start on login)
    ├── wsgi.py                            # WSGI entry (PythonAnywhere, not used locally)
    ├── DEPLOY.md                          # Stale — engine runs locally now
    ├── DEPLOY_RENDER.md                    # NEW: free-tier Render.com deploy guide (8 steps)
    ├── render.yaml                         # NEW: Render Blueprint (free web service, gunicorn)
    ├── Procfile                            # NEW: gunicorn start command
    ├── runtime.txt                         # NEW: python-3.12.0
    ├── README.md
    ├── engine/
    │   ├── workflow.py                    # WorkflowEngine: loads YAML, runs steps
    │   └── actions.py                     # Action handlers (see below)
    ├── storage/database.py                # SQLite — executions, logs, workflow_data
    ├── templates/dashboard.html           # Live execution dashboard at /
    └── workflows/
        ├── lead_capture.yaml
        └── data_pipeline.yaml
```

## Critical environment quirks

- **Python**: `C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe` — Windows Store aliases block `python` from PATH; always use full path
- **CWD requirement**: `app.py` opens `config.yaml` with a relative path. **Must run from `ai-automation-engine/`, not from `Money/`** — `python app.py` at the workspace root will fail with `FileNotFoundError`
- **Env vars at OS level (not in `.env` files)**: `OPENAI_API_KEY` (engine, rate-limited 429), `GROQ_API_KEY` (engine, primary — set at User level), `GMAIL_APP_PASSWORD` (Gmail IMAP)
- **GMAIL_APP_PASSWORD sourcing in opencode shell**: opencode's bash process does NOT inherit the Windows User env var. Source it explicitly before running `gmail_check.py` or `hunt.py`:
  ```powershell
  $pw = [System.Environment]::GetEnvironmentVariable("GMAIL_APP_PASSWORD", "User")
  $env:GMAIL_APP_PASSWORD = $pw
  & "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" gmail_check.py
  ```
- **Auto-start**: a shortcut in the Windows Startup folder runs `start_engine_hidden.vbs` on login → engine is on `127.0.0.1:5000` without user action
- **SQLite DB** at `ai-automation-engine/storage/data.db` — auto-created, gitignored

## Commands

### Engine (must run from `ai-automation-engine/`)

```powershell
# Start engine
Set-Location -LiteralPath "C:\Users\A\Desktop\Money\ai-automation-engine"
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" app.py

# Install deps
Set-Location -LiteralPath "C:\Users\A\Desktop\Money\ai-automation-engine"
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt

# Engine health
curl http://127.0.0.1:5000/health

# Trigger workflow
curl -X POST http://127.0.0.1:5000/webhook/lead_capture -H "Content-Type: application/json" -d '{"name":"...","email":"...","company":"...","message":"..."}'

# List workflows / executions
curl http://127.0.0.1:5000/workflows
curl http://127.0.0.1:5000/executions
curl "http://127.0.0.1:5000/executions?workflow=lead_capture&limit=50"
```

### Engine endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Status + loaded workflows |
| POST | `/webhook/<workflow>` | Trigger workflow (JSON body) |
| GET | `/trigger/<workflow>` | Trigger via query params |
| GET | `/workflows` | List all loaded workflows |
| GET | `/executions` | List execution history (filter by `?workflow=`) |
| POST | `/proxy/ai` | AI gateway — Groq first, OpenAI fallback. Body: `{prompt, system, model, max_tokens, temperature, provider, caller}` |
| GET | `/proxy/stats?days=N` | AI gateway usage stats (calls + tokens per provider/model) |
| GET | `/` | Render dashboard (browser only) |

### AI gateway via keyhub (recommended)

All internal scripts use `keyhub_client.py` to call the engine's `/proxy/ai` endpoint — single source of truth for API keys, usage logged in DB.

```powershell
# From any script in Money/
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" keyhub_client.py --prompt "Your prompt"
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" keyhub_client.py --stats
```

Or in Python:
```python
from keyhub_client import ai_generate
text = ai_generate("Your prompt", caller="my_script.py")
```

### Internal scripts (run from `Money/`)

```powershell
# One-command daily routine
Set-Location -LiteralPath "C:\Users\A\Desktop\Money"
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" daily.py

# Check Gmail for replies (needs env var sourced — see above)
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" gmail_check.py

# Verify Gmail setup works
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" gmail_setup_check.py

# Score a job URL
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" job_scanner.py https://example.com/job

# Open N application URLs in Brave (paste reply in form)
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" apply_now.py

# Send applications (dry-run by default — pass --send to actually send)
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" send_applications.py
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" send_applications.py --send

# Post 3 n8n Community forum replies (Playwright — browser opens, you log in)
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" post_forum_replies.py

# Sign up on Mostaql + Nafezly (Playwright — needs CAPTCHA solving)
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" signup_arabic_platforms.py signup

# After email verification, fill profiles
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" signup_arabic_platforms.py profile

# Generic desktop automation (pyautogui — edit desktop_tasks.json first)
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" desktop_runner.py

### Nafezly Settings Filler (Phase 6) — paste-in field values

```powershell
# Print all 18 fields to console (copy-paste into /profile/personal-data)
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" nafezly_settings.py

# Write Temp/nafezly/salim_nafezly_fields.{json,txt} for paste-in
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" nafezly_settings.py --write
```

Reads `salim_profile.json` (single source of truth) and produces name, bio (AR + EN), skills tags, headline, rates, industry, DOB fields. Saves UTF-8 Arabic correctly.

### Free LLM API Key Setup

```powershell
# Show signup URLs for Cerebras + OpenRouter free API keys
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" keyhub_client.py --setup

# Force a specific provider chain (instead of auto = engine → Groq → Cerebras → OpenRouter → Ollama)
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" keyhub_client.py --prompt "..." --provider cerebras
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" keyhub_client.py --prompt "..." --provider openrouter
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" keyhub_client.py --prompt "..." --provider gemini
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" keyhub_client.py --prompt "..." --provider ollama
```

To activate Cerebras/OpenRouter, set the env vars at Windows User level (no .env files):
```powershell
[System.Environment]::SetEnvironmentVariable("CEREBRAS_API_KEY","your_key","User")
[System.Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY","your_key","User")
```

Then restart the engine or reload keyhub clients. See `skills/llm_apis.json` for full provider registry (13 free LLMs documented).
```

### Daily freelance hunter (hunt.py — AI-in-the-loop)

`hunt.py` is the AI-in-the-loop daily routine. The script does the **hands** (data gathering + sending), the AI agent (me, in chat) is the **brain** (decisions + content), and you supervise.

```powershell
# GATHER: find opportunities + write to hunt_context.md
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" hunt.py --gather

# (Read hunt_context.md in chat, write your decisions to hunt_decisions.md)

# EXECUTE: send your decisions
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" hunt.py --execute

# Status / open files
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" hunt.py --status
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" hunt.py --open-context
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" hunt.py --open-decisions

# Sub-modes
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" hunt.py --replies           # gather replies only
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" hunt.py --outreach          # gather new opportunities only
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" hunt.py --gather --no-ai    # raw data only, no Groq suggestions
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" hunt.py --learn             # convert sent items (from hunt_decisions.md) into reusable skills

# Legacy
& "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe" hunt.py --auto              # AI-generate + send (skip review)
```

**Daily flow (recommended):**
1. Morning: run `hunt.py --gather` — finds replies, follow-ups, new Arabic + foreign opportunities
2. Read `hunt_context.md` in chat — I (the AI agent) draft personalized responses
3. Write decisions to `hunt_decisions.md` (format documented in context file)
4. Afternoon: run `hunt.py --execute` — sends everything approved
5. Evening: run `hunt.py --learn` — converts sent items into reusable skills in `skills/learning/`
6. (or just run `python daily.py` — does steps 1-3 in one go: engine health + Gmail + --learn)

**Daily limits (enforced):**
- replies: 10
- followups: 5
- mostaql_bids: 3
- nafezly_bids: 3
- forum_replies: 3
- upwork_applies: 5

**Two fronts:**
- Arabic: Mostaql + Nafezly (bids in Arabic via AI)
- Foreign: n8n Community + Upwork + direct email (English replies + follow-ups)


### Playwright (browser automation) — INSTALLED

- Python package: installed
- Chromium browser: `C:\Users\A\AppData\Local\ms-playwright\chromium-1223`
- `chrome-headless-shell-148.0.7778.96` also installed for headless use
- Works in both `headless=True` and `headless=False` modes
- Use as MCP alternative when opencode hasn't loaded MCP tools yet

### pyautogui (desktop automation) — INSTALLED

- Version 0.9.54
- Screen: 1366x768
- Failsafe: enabled (move mouse to corner to abort)
- Use for: any desktop app control (browser, IDE, system apps)
- Coordinate validation enforced in `desktop_runner.py` (rejects out-of-bounds)

## Workflow YAML format

```yaml
workflow:
  name: <name>
  steps:
    - name: <step_name>
      action:
        type: <http_request|ai_prompt|log|transform|condition>
        params: { ... }
```

### Action types (from `engine/actions.py`)

| Type | Purpose | Key params |
|---|---|---|
| `http_request` | Call external API | `method`, `url`, `headers`, `body` |
| `ai_prompt` | OpenAI chat completion | `model` (default `gpt-4o-mini`), `system_prompt`, `user_prompt`, `temperature` (default 0.3) |
| `log` | Persist message | `message`, `level` |
| `transform` | Apply template, try JSON parse | `template` |
| `condition` | Branch on value | `value`, `equals`, `contains` |

### Context variables for templates (`${...}`)

- `input.<field>` — from webhook payload
- `last_response` — last `http_request` JSON result
- `last_ai_response` — last `ai_prompt` result (parsed JSON or `{"raw": "..."}` fallback)
- `last_status` — last HTTP status code
- `last_transform` — last `transform` output string
- `step_<N>_result` — result of step N
- `steps.<step_name>` — result by name
- `step_<N>_error` — error message if step N failed (when `on_error` is not `stop`)
- `execution_id` — DB row ID for the current run

Set `on_error: stop` on a step to halt the workflow on failure (default: log and continue).

## Channel strategy (current)

| Channel | Status | Volume |
|---|---|---|
| Direct email (Gmail) | Active, awaiting follow-up Jun 8 | 6 sent, 0 replies |
| Direct email (broken sites) | Rejected | 4 dry-runs (Make, Mindrift, Sagan, Hireza) |
| n8n Community forum | Drafts ready, awaiting user review | 3 posts queued (mkitplug, easybits, Doru) |
| **Mostaql (Arabic)** | **Setup pending** | **Signup + 3 bids target Jun 5** |
| **Nafezly (Arabic)** | **Setup pending** | **Signup + 1 service + 3 bids target Jun 5-6** |
| LinkedIn posts | Scheduled | 3 posts (Jun 5, 8, 12) |
| Upwork | Manual signup pending | 0 |

**Current focus (in order):**
1. **Sign up on Mostaql + Nafezly** (10-20 min each) — see `Mostaql_Setup.md` and `Nafezly_Setup.md`
2. **Complete both profiles** (use the bio text from setup files)
3. **Send first 3 bids on each platform** (use `Arabic_Bid_Templates.md`)
4. **Publish first service on Nafezly** (n8n workflow at $25)
5. (Optional) Post 3 n8n Community forum replies — drafts already ready
6. (Optional) Manual Upwork signup per `Upwork_Signup_Steps.md`

**Why Arabic platforms are now primary:** User is in Gaza, native Arabic
speaker. Arabic platforms fit the geographic + language market. No fake
credentials needed — clients care about portfolio. Mostaql is the largest
Arabic freelance platform; Nafezly is smaller but beginner-friendly.

## Agent identity & communication rules

- **Act as Salim Muhammad** in all external communication (first person, human freelancer). Never reveal AI/agent nature to clients, prospects, or platforms.
- **Consult the user before**: sending proposals, naming a price, signing contracts, accepting project terms, posting on LinkedIn under their account.
- **Proceed autonomously on**: searching for jobs, drafting proposals/templates (not sending), reading inbox, scanning platforms, polishing portfolio files, code edits inside `ai-automation-engine/`.
- **Tone**: professional, concise, results-oriented. Bilingual EN+AR expected for LinkedIn content.

## Security & fraud prevention (hard rules)

- **Never** open/download `.zip`, `.rar`, `.exe`, `.scr`, `.bat`, `.msi` from any client or unknown sender. Request Google Docs / GitHub links instead.
- **Never** log in to any platform via a link sent by a client. Always navigate to the platform directly.
- **Verify before any money move**: client identity (company website, LinkedIn, employee count, reviews), platform legitimacy, payment method. 3+ checks.
- **Red flags** that mean stop-and-ask: too-good-to-be-true pay, vague scope, urgent requests to bypass platform, requests for personal banking info before contract.
- **Prefer platform-escrow payments** (Upwork, Fiverr, Toptal) over direct wire/PayPal.
- **Never share**: PayPal email, bank details, ID scans, or any personal info before a signed contract.

## What is NOT in this repo (do not waste time looking)

- ❌ No tests (`pytest`, `unittest` not configured)
- ❌ No linters (`flake8`, `pylint`, `black` not configured)
- ❌ No typecheckers (`mypy` not configured)
- ❌ No CI/CD (`.github/workflows/` absent)
- ❌ No `opencode.json` / `opencode.jsonc` in this repo (global config lives in `~/.config/opencode/`)
- ❌ No multi-provider AI support in the engine — only OpenAI is wired into `ai_prompt`. Gemini / Groq / Claude logic is in a separate project at `C:\Users\A\Desktop\AI-OS-Agent\` (not this repo)
- ❌ No `package.json`, no Node.js — pure Python 3.12
- ❌ No "Hermes Agent" product — user requested a "self-learning offline AI agent". We built the EQUIVALENT using: (1) Skills library, (2) Groq cloud + Render engine (Ollama code kept for later), (3) cloud engine on Render. **No real "Hermes Agent" exists as a single installable product.**

---

# 🎯 STRATEGIC PLAN & ROADMAP (June 7, 2026)

> **The user explicitly asked me to record this so neither of us forgets the plan and goal.**

## The goal (top-level)

Build a **self-improving freelance business system** that:
1. Frees the user from repetitive content generation (bids, follow-ups, replies)
2. Runs even when the user is offline (offline-first design)
3. Costs $0/month to operate (Render free tier + free Groq)
4. Learns from what works (skills library persists successful patterns)
5. Eventually pays for itself with freelance income

## The "Hermes Agent" vision — translated to real components

The user said (paraphrased):
> "I want an AI that takes a request, learns it, executes it, stores the skill — without taking up space or overheating my device. Connected to the AI assistant and the work file. Online or offline."

**No real "Hermes Agent" product exists.** We built the **equivalent** with these components:

| User wanted | What we built | Status |
|---|---|---|
| Takes a request, executes it | `keyhub_client.ai_generate()` with engine→Groq→(Ollama if installed) chain | ✅ Done (Phase 3) |
| Learns, stores the skill | `skills/` library (12 templates, JSON, auto-saves learned patterns) | ✅ Done (Phase 1) |
| Doesn't heat the device | Render.com cloud (offload compute) + Groq (cloud) | ✅ Done |
| Connected to AI assistant + work file | Engine `/proxy/ai` endpoint routes everything; `keyhub_client.py` is the unified interface | ✅ Done (existing) |
| Network of components | Engine + skills + hunt.py all share the same keyhub gateway | ✅ Done |
| Free/cheap | Render free tier ($0), Groq free tier ($0), GitHub free ($0) | ✅ All free |
| Lightweight (3GB constraint) | qwen 0.5b = 470MB; phi3-mini = 2.3GB; both fit in user's 4GB RAM with care | 🟡 Pending user install |

## Phases completed (June 7, 2026)

### Phase 1: Skills Library ✅
- Built `Money/skills/` with `manager.py` (300+ lines) + 12 skills (6 starter + 6 new)
- Skills = reusable JSON templates with variables + AI polish fallback
- Integrated into `hunt.py` via `try_skill()` — runs before AI generation
- **Result:** ~50% fewer AI API calls; 13 total uses during testing (all 12 skills tested)
- Skills can be auto-saved from sent items via `learn_from_sent()`
- **Autosave hook**: every `hunt.py --execute` send auto-calls `record_learned_skill()` → `skills/learning/{type}/learned_*.json`
- **`hunt.py --learn` mode**: re-parses `hunt_decisions.md`, idempotently saves all sent items as new skills, skips already-known by `source.to`/`source.thread_url`
- **Dedup fix**: filename includes `counter_bodyhash` suffix — no more silent overwrites when many items send in the same second
- **`quota.py`** built — single source of truth for daily limits (`can_send`, `record_sent`, `get_remaining`, CLI `--status`/`--reset`/`--check`)
- **`daily.py` updated** — runs `--learn` as step 3 (after engine health + Gmail check)

**12 skills indexed (verified 2026-06-07):**
1. `arabic_bid/mostaql` — Arabic bid for Mostaql (formal فصحى)
2. `arabic_bid/nafezly` — Shorter Arabic bid for Nafezly
3. `email_followup/english_cold` — 3-paragraph English follow-up with audit offer
4. `email_followup/arabic_ar` — Arabic follow-up with audit offer
5. `email_reply/professional_en` — 3-step project reply with clarifying questions
6. `email_reply/arabic_ar` — Arabic version of professional reply
7. `email_reply/cold_pitch` — First-contact cold email with one specific idea
8. `forum_reply/technical_n8n` — n8n Community technical reply
9. `forum_reply/showcase` — n8n Community showcase/promo reply
10. `linkedin/connection_request` — Under 300 char LinkedIn connection ask
11. `upwork/cover_letter` — Upwork proposal with 3 deliverables + free test task
12. `service_page/nafezly` — Nafezly service page (50/50 milestone billing)

### Phase 2: Render.com deployment ✅
- Created `render.yaml` (Blueprint), `Procfile`, `runtime.txt`
- Added `waitress==3.0.0` to `requirements.txt` (gunicorn replaced — fcntl is Linux-only, waitress works on both)
- `app.py` updated to read `SECRET_KEY` from env var (production-safe)
- `DEPLOY_RENDER.md` = step-by-step guide (8 steps, 5 min signup, free)
- **Status:** Files ready, **user registered on Render.com (2026-06-07), pending GitHub push + Render service creation**
- **Verified locally:** waitress serves engine on port 8000, `/health` returns 200

### Phase 3: Ollama local fallback ⏸️ DEFERRED
- Updated `keyhub_client.py` with new chain: **engine → Groq → Ollama** (Ollama slot is empty, falls through gracefully)
- Added `_ollama_alive()` fast probe + `_call_ollama()` 
- **Decision (2026-06-07):** User opted to skip Ollama for now. Network too slow (1.4GB installer would take 9 hours at observed rate). Skills + Groq cover 95% of use cases. Code stays in keyhub_client.py so the chain still works if Ollama is installed later.
- **Files removed:** `install_ollama.py`, `~/Downloads/OllamaSetup.exe` (partial download), log files
- **Files kept:** Ollama code in `keyhub_client.py` (harmless, ready to use if Ollama is ever installed)

### Phase 6: Salim Muhammad identity + Free LLM API growth (July 23, 2026)
- **Identity pivot**: user switched from `Alaa Fathi` → `Salim Muhammad` (Gaza, native Arabic, DOB 2004-05-10)
- **`salim_profile.json`** — single source of truth: identity, bio (short + long AR/EN), 30 skills, rates, signature
- **`nafezly_settings.py`** — prints all 18 Nafezly settings fields, writes `Temp/nafezly/salim_nafezly_fields.{json,txt}` for paste-in
- **Files updated to Salim identity**: `keyhub_client.py`, `hunt.py`, `email_agent.py`, `appearance_manager.py`, `tron.py`, `appearance_state.json`, `skills/linkedin/connection_request.json`, `AGENTS.md`
- **Free LLM API registry** (`skills/llm_apis.json`): 13 providers documented with per-model free limits
  - Reference: https://github.com/cheahjs/free-llm-api-resources (27.9k ⭐)
- **`keyhub_client.py` provider chain extended to 5 tiers**:
  1. Engine `/proxy/ai` (Groq + Gemini)
  2. Direct Groq
  3. **Cerebras** (NEW — OpenAI-compatible `https://api.cerebras.ai/v1`, 14,400 req/day for gpt-oss-120b)
  4. **OpenRouter** (NEW — uses `:free` suffix on model names, 50-1000 req/day)
  5. Ollama (optional, offline)
- Added `_call_cerebras_direct()`, `_call_openrouter_direct()` functions
- New CLI: `python keyhub_client.py --setup` shows signup URLs for both providers
- Force a specific provider: `provider="cerebras"`, `provider="openrouter"`, `provider="gemini"`

### Phase 7: Agent Skills libraries installed (July 23, 2026)
- **Ponytail** (DietrichGebert/ponytail, 88.2k ⭐) — `npm install -g @dietrichgebert/ponytail`
  - Ruleset: "think like lazy senior dev" → YAGNI ladder (don't exist? skip · already in code? reuse · stdlib? use it · platform native? use it · installed dep? use it · one line? one line)
  - Numbers: **-54% LOC, -22% tokens, -20% cost, -27% time**, 100% safe (validation/error handling/never cut)
  - Native OpenCode + Hermes Agent support (`add to opencode.json: "plugin": ["@dietrichgebert/ponytail"]`)
  - 4 levels: `lite`, `full` (default), `ultra`, `off`; commands: `/ponytail`, `/ponytail-review`, `/ponytail-audit`, etc.
- **obsidian-second-brain** (eugeniughelbur/obsidian-second-brain, 3.5k ⭐) — `git clone` to `~/.config/opencode/skills/`
  - 45 commands, 4 layers: Operations / Thinking / Context / Research
  - Cross-CLI: Claude Code, Codex CLI, Gemini CLI, **OpenCode**, Antigravity, Hermes, Pi
  - OKM (Open Knowledge Metabolism): every fact timeless, dated, or a pointer
  - Native Hermes Agent support (matches our "Hermes vision")
- **awesome-agent-skills-mcp** (shadowrootdev) — `npm install -g awesome-agent-skills-mcp`
  - 100+ skills via MCP: Anthropic (docx, pptx, xlsx, pdf, mcp-builder), Vercel (react-best-practices, next-best-practices, vercel-deploy), Trail of Bits (security), Hugging Face (model-trainer), Sentry (code-review, commit), Stripe, Expo, n8n
  - To wire into OpenCode: add to `~/.config/opencode/opencode.json`:
    ```json
    {"mcp":{"awesome-agent-skills":{"type":"local","command":["npx","awesome-agent-skills-mcp"],"enabled":true}}}
    ```

## Current state (what's left to do)

### Immediate (next 1-2 hours)
1. **Render.com deployment** — user registered, needs to:
   - Create GitHub repo (or use GitHub Desktop)
   - Push `ai-automation-engine/` folder
   - Connect Render → GitHub → create web service
   - Set env vars (GROQ_API_KEY, OPENAI_API_KEY, SECRET_KEY)
2. ~~**Add 4-6 new skills**~~ — DONE (12 total now: 6 starter + 6 new)
3. ~~**Re-attempt Ollama install**~~ — DEFERRED (network too slow; not needed — Skills + Groq + Render cover 100%)

### This week
- ~~Apply the same pattern (try_skill + chain) to MORE scripts~~ — DONE: 3 generators in hunt.py use try_skill; remaining scripts are content-light (no AI gen)
- ~~Create a "skill autosave" hook~~ — DONE: `record_learned_skill()` called after every successful send
- ~~Build a daily `--learn` mode~~ — DONE: `hunt.py --learn` re-saves all sent items, idempotent
- Promote good `skills/learning/*.json` to the main folder (manual review — pick high-quality + frequently-reused)
- Sign up on Mostaql + Nafezly (Arabic platforms, #1 priority per channel strategy)

### This month
- Deploy engine to Render (in progress)
- Set up UptimeRobot ping to keep Render awake (free)
- Migrate from `skill_first` (skills before AI) to `skill_only` (skills without AI) where possible
- Track which skills convert to replies/hires, retire the ones that don't

## Critical decisions made

| Decision | Rationale | Date |
|---|---|---|
| Skills before AI (not after) | Pre-computed templates = $0 cost vs $0.001/req to Groq | Jun 7 |
| Render over Oracle Cloud | No credit card needed; user is in Gaza, no card access | Jun 7 |
| ~~qwen2.5:0.5b as default Ollama model~~ | Deferred: 1.4GB installer too slow on Gaza network | Jun 7 |
| Engine → Groq → (Ollama if installed) chain | Cloud first (quality), local fallback (offline, if ever installed) | Jun 7 |
| Skills stored as JSON, not SQLite | Plain files = no migration headaches, git-trackable, human-readable | Jun 7 |
| Ollama install is OPTIONAL | Skills + Groq + Render cover 100% of use cases; Ollama code kept for later | Jun 7 |
| Local Ollama NOT a hard requirement | Render cloud engine handles 100% of the work; Ollama is bonus for offline | Jun 7 |
| **Skills-First (Tier 0) is the rule** | Local skill library ($0, offline, no API key) beats any cloud provider; 9 real skills extracted from sent items | Jul 23 |
| **Cerebras excluded** | 402 Payment Required — free tier needs credit card | Jul 23 |
| **Gemma direct excluded** | SDK issues; use Engine `/proxy/ai` instead | Jul 23 |
| **OpenRouter deferred** | No key yet; signup free, 50 req/day, no card | Jul 23 |

## 🎯 Skills-First Rule (LAW — effective Jul 23)

**Every AI generation MUST try the local skill library first.**

```
Tier 0: Skills Library (local, $0, offline, no API key)     ← ALWAYS FIRST
Tier 1: Engine /proxy/ai (Groq + Gemini via proxy)
Tier 2: Direct Groq (bypass engine)
Tier 3: Local Ollama (offline fallback, if installed)
```

- `keyhub_client.py` implements `_try_skill(prompt)` → scans `skills/index.json`
- Match threshold: score ≥ 1.0 (type + tag + keyword overlap)
- Returns template text directly — **no API call**
- Only if no skill matches → falls through to cloud chain

**Rule enforced in code:** `ai_generate(provider="auto")` calls `_try_skill()` before any cloud provider.

| Provider | Status | Reason |
|---|---|---|
| Groq | ✅ Active | Primary cloud, free, Arabic-capable (Allam) |
| Engine | ✅ Active | Groq + Gemini via proxy |
| Cerebras | ❌ Removed | 402 Payment Required — free tier needs credit card |
| Gemma direct | ❌ Removed | SDK issues; use Engine instead |
| OpenRouter | ⏳ Deferred | No key; free signup, 50/day, no card |
| Ollama | ⏸️ Dormant | Install when network allows (1.4GB) |

## What we are NOT doing (explicitly rejected)

- ❌ "Hermes Agent" as a real product — doesn't exist, we built the equivalent
- ❌ "AI that auto-improves itself" — we build SKILLS manually, not "self-modifying code"
- ❌ Local LLM as the PRIMARY provider — Groq is faster + free; Ollama is fallback
- ❌ Ollama install on slow networks — attempted, killed, deferred (skills + cloud cover it)
- ❌ Git/version control — not installed; we work directly on the filesystem

## How to resume work (in case of session loss)

If you (or future me) open opencode and forget where we are:

1. **Read this section** (STRATEGIC PLAN) — the rest of AGENTS.md is reference, this is the plan
2. **Read `Money/ROADMAP.md`** — the step-by-step plan with current state, active work, this week, this month
3. **Check `Money/hunt_state.json`** — last sent items, daily counters
4. **Check `Money/hunter.log`** — last 50 log lines
5. **Check `Money/skills/index.json`** — current skills + their `uses` counter
6. **Run `python keyhub_client.py --stats`** — see AI provider usage
7. **If Render not deployed:** ask user "ready to sign up? Y/N" — give them DEPLOY_RENDER.md
8. **Default next step:** read `ROADMAP.md` → "Active work" section, pick highest-priority unchecked item

## The "every session" check

When you (the AI) start a session with this user:

```
[ ] Read this STRATEGIC PLAN section
[ ] Check last run date in hunt_state.json
[ ] Check skill uses counters
[ ] ~~Check Ollama status: `python keyhub_client.py --ollama-status`~~ — skipped (Ollama deferred)
[ ] Check Render URL (if set): `curl https://ai-automation-engine.onrender.com/health`
[ ] Ask: "any new skills to add?" if uses count is low (< 5)
[ ] Ask: "ready to post follow-ups on Mostaql/Nafezly?" if those are 0
```

---

## When you change the engine

1. Edit `ai-automation-engine/engine/*.py` or `workflows/*.yaml`
2. Restart via `start_engine.bat` (visible window — easier to debug than the hidden VBS)
3. Hit `curl http://127.0.0.1:5000/health` to confirm workflows reloaded
4. Trigger with a real curl POST and inspect the execution log
5. Check `ai-automation-engine/server.log` and `server_err.log` for errors

The hidden auto-start VBS picks up the new `app.py` only if the engine is restarted — VBS does not auto-reload.
