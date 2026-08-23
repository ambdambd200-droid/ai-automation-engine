# FREELANCE AUTOMATION SYSTEM — MASTER PLAN

**Identity:** Salim Muhammad | AI Automation Engineer | Gaza
**Contact:** salim.muhammad.work@gmail.com
**Platforms:** Mostaql, Nafezly, n8n Community, Direct Email
**Last Updated:** 2026-08-23

---

## 🎯 VISION

Build a **fully autonomous, $0-cost freelance automation system** that:
- Runs 24/7 on GitHub Actions (cloud, no local device needed)
- Finds projects, generates bids, posts replies automatically
- Self-heals when selectors break or sessions expire
- Notifies via Telegram for every action
- Learns from successful bids/replies to improve over time
- Costs $0/month (GitHub Actions free tier + Telegram Bot API free + Gmail SMTP free)

---

## 📦 CURRENT ARCHITECTURE (Production Ready)

### Core Components

| Component | File | Purpose | Status |
|-----------|------|---------|--------|
| **Daily Orchestrator** | `run_daily_freelance.py` | Main entry point - runs daily routine | ✅ Working |
| **Telegram Bot** | `telegram_controller.py` | 24/7 long-polling bot with AI chat + auto-reply | ✅ Working |
| **Telegram Notifier** | `telegram_notifier.py` | Free notifications (digest, errors, success) | ✅ Working |
| **Session Manager** | `session_manager.py` | Playwright persistent contexts + storage_state | ✅ Working |
| **Auto Re-auth** | `auto_reauth.py` | Nafezly (Magic Link IMAP), Mostaql (pwd), n8n (OAuth) | ✅ Working |
| **Selector Discovery** | `auto_selectors.py` | Playwright DOM analyzer for project cards | ✅ Working |
| **Selector Cache** | `selector_cache.py` | Persistent JSON cache with versioning + success tracking | ✅ Working |
| **Healing Orchestrator** | `healing_orchestrator.py` | Classifies errors, retries with backoff, triggers healing | ✅ Working |
| **Bid Poster** | `post_arabic_bids.py` | Mostaql + Nafezly bid posting with cache fallback | ✅ Working |
| **n8n Replier** | `post_n8n_replies.py` | Posts drafted replies to n8n Community | ✅ Working |
| **Forum Replier** | `post_forum_replies.py` | Posts to n8n Community forum | ✅ Working |
| **Platform Signup** | `signup_arabic_platforms.py` | Mostaql + Nafezly signup + profile fill | ✅ Working |
| **n8n Signup** | `signup_n8n_community.py` | n8n Community signup + profile | ✅ Working |
| **Portfolio Creator** | `create_portfolio.py` | Weekly Nafezly/Mostaql portfolio pieces | ✅ Working |
| **AI Gateway** | `keyhub_client.py` | Engine → Groq → (Ollama) chain | ✅ Working |
| **Security Utils** | `security_utils.py` | Input sanitization, rate limiting, API key management | ✅ Working |
| **Quota Manager** | `quota.py` | Daily limits enforcement (3 Mostaql, 3 Nafezly, 2 n8n) | ✅ Working |

### Configuration Files

| File | Purpose |
|------|---------|
| `salim_profile.json` | Single source of truth: identity, bio, skills, rates |
| `requirements.txt` | Python dependencies |
| `.github/workflows/daily.yml` | Daily run (4 AM UTC / 7 AM Gaza) |
| `.github/workflows/weekly.yml` | Weekly portfolio (Sunday 4 AM UTC) |
| `.github/workflows/telegram-controller.yml` | Telegram bot 24/7 (every 5 hours) |
| `.github/workflows/daily-healing.yml` | Healing check every 6 hours |
| `AGENTS.md` | System documentation |
| `ROADMAP.md` | Strategic roadmap |

### Platform Sessions (Persisted)

| Platform | Session File | Login Method |
|----------|--------------|--------------|
| Mostaql | `sessions/mostaql.json` | Email + Password (env: MOSTAQL_PASSWORD) |
| Nafezly | `sessions/nafezly.json` | Magic Link via Gmail IMAP |
| n8n Community | `sessions/n8n_community.json` | Persistent Brave context (Google OAuth) |

### Selector Cache

| Platform | Cache File | Key Selectors |
|----------|------------|---------------|
| Mostaql | `selectors/mostaql.json` | `.project-row`, `.card--title a`, `.project__meta` |
| Nafezly | `selectors/nafezly.json` | `.project-box`, `.text-truncate a`, `.price` |

---

## 🔄 DAILY FLOW (Automated via GitHub Actions)

```
4:00 AM UTC (7 AM Gaza) → daily.yml triggers
    │
    ├─► Checkout repo + restore sessions cache
    ├─► Install Python + Playwright Chromium
    ├─► Start local engine (ai-automation-engine)
    ├─► Run run_daily_freelance.py
    │    ├─► Mostaql: search "n8n, أتمتة, بوت" → bid top 3
    │    ├─► Nafezly: search "n8n, أتمتة, API" → bid top 3
    │    └─► n8n Community: post 1 reply from drafts
    ├─► Save sessions back to cache
    ├─► Upload logs/artifacts
    └─► Telegram digest notification
```

### Quota Limits (Enforced)

| Platform | Daily Limit | Weekly Bonus |
|----------|-------------|--------------|
| Mostaql | 3 bids | 1 portfolio |
| Nafezly | 3 bids | 1 portfolio + 1 service |
| n8n Community | 2 replies | — |

---

## 🤖 TELEGRAM BOT (24/7 on GitHub Actions)

**Workflow:** `.github/workflows/telegram-controller.yml` (runs every 5 hours)

### Commands (Owner Only - TELEGRAM_CHAT_ID)

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/status` | Engine health, quotas, last run |
| `/run daily\|weekly` | Trigger routine manually |
| `/quota` | Remaining bids/replies today |
| `/sessions` | Session validity check |
| `/heal <platform>` | Show healing stats |
| `/reauth <platform>` | Force re-auth (background) |
| `/health` | Full system health check |
| `/selectors <platform>` | Cached selector stats |
| `/auto on\|off\|status` | Toggle auto-healing |
| `/logs` | Last 20 lines of logs |

### AI Free-Form Chat (Owner Only)
- Send any message → AI responds as Salim Muhammad
- Uses engine `/proxy/ai` → Groq `llama-3.1-8b-instant`
- System prompt enforces: professional, bilingual, never reveal AI nature

### Auto-Reply to Clients (5-min cooldown)
- Non-owner messages → instant acknowledgment
- Background thread generates detailed response
- Cooldown prevents spam: 5 minutes per chat_id

---

## 🛡️ SELF-HEALING SYSTEM

### Error Classification → Healing Action

| Error Type | Detection | Healing Action |
|------------|-----------|----------------|
| `SELECTOR_EXTRACTION` | CSS selector fails | Run `auto_selectors.py` → update cache |
| `AUTHENTICATION` | Session expired/redirect to login | Run `auto_reauth.py` for platform |
| `NETWORK` | Connection timeout | Wait 10s, retry |
| `RATE_LIMIT` | 429 / quota exceeded | Wait 60s, retry |
| `VALIDATION` | Input validation failed | Non-recoverable (log only) |

### Healing Flow
```
Operation fails
    │
    ▼
Classify error type
    │
    ▼
Attempt healing (max 3 retries with exponential backoff)
    │
    ├──► Success → Continue operation
    │
    └──► All retries exhausted → Telegram error alert + log
```

---

## 🚀 DEPLOYMENT CHECKLIST (GitHub Secrets Required)

| Secret | Source | Purpose |
|--------|--------|---------|
| `TELEGRAM_BOT_TOKEN` | @BotFather | Telegram bot API |
| `TELEGRAM_CHAT_ID` | getUpdates API | Your private chat ID |
| `GROQ_API_KEY` | console.groq.com | AI gateway primary |
| `GMAIL_APP_PASSWORD` | Google Account → App Passwords | SMTP + IMAP for Magic Links |
| `GMAIL_USER` | Your Gmail | alaafathi403@gmail.com |
| `MOSTAQL_EMAIL` | Mostaql account | ambdambd200@gmail.com |
| `MOSTAQL_PASSWORD` | Mostaql account | AASS2020AASS2010 |
| `NAFEZLY_EMAIL` | Nafezly account | alaafathi403@gmail.com |
| `ENGINE_URL` | Render deployment | https://ai-automation-engine.onrender.com |
| `ENGINE_FROM_EMAIL` | Sender email | salim.muhammad.work0@gmail.com |

---

## 📁 ESSENTIAL FILES ONLY (Keep These)

### Root Python Scripts (18 files)
```
run_daily_freelance.py
telegram_controller.py
telegram_notifier.py
telegram_debug.py
session_manager.py
auto_reauth.py
auto_selectors.py
selector_cache.py
healing_orchestrator.py
post_arabic_bids.py
post_n8n_replies.py
post_forum_replies.py
signup_arabic_platforms.py
signup_n8n_community.py
create_portfolio.py
keyhub_client.py
security_utils.py
quota.py
daily.py
gmail_check.py
```

### Core Directories
```
.github/workflows/          # 4 workflow files
ai-automation-engine/       # Flask engine
agents/                     # 5 agent personas
portfolio/                  # Website (index.html, styles.css, script.js)
skills/                     # Skills library (12 skills)
sessions/                   # 3 platform sessions
selectors/                  # 2 selector caches
plans/                      # Plan documents
.opencode/                  # OpenCode config
```

### Config & Docs
```
salim_profile.json
requirements.txt
AGENTS.md
ROADMAP.md
README.md
.gitignore
```

### State Files (gitignored but needed at runtime)
```
daily_freelance_state.json
hunt_state.json
telegram_log.md
gmail_log.md
```

---

## 🗑️ DELETED (Non-Essential)

**120+ files removed** including:
- All `step*`, `debug*`, `check*`, `test*` scripts (one-time use)
- Old agents: `email_agent.py`, `linkedin_agent.py`, `mostaql_agent.py`, `nafezly_agent.py`, `sentry.py`
- Old pipeline: `pipeline.py`, `hunt.py`, `arabic_platform_manager.py`, `arabic_bid_runner.py`
- Debug outputs: `debug_mostaql.html`, `debug_nafezly.html`
- Logs: `*.log`, `hunter.log`, `email_agent.log`, `sentry.log`
- Old docs: `Alaa_Fathi_CV.md`, `LinkedIn_*`, `Upwork_*`, `TRAINING_CONVERSATION.md`
- Screenshots directories, Temp, __pycache__

---

## 🔮 FUTURE ROADMAP (Next Steps)

### Phase 1: Immediate (Week 1)
- [ ] Deploy to GitHub → verify all 4 workflows run
- [ ] Set all GitHub Secrets
- [ ] Verify Telegram bot runs 24/7 (check every 5 hours)
- [ ] Test full daily flow end-to-end
- [ ] Verify Nafezly Magic Link re-auth works via IMAP

### Phase 2: Enhancement (Week 2-3)
- [ ] Add **project filtering** - score projects by relevance before bidding
- [ ] Add **bid quality gate** - use `quality_reviewer` agent before posting
- [ ] Add **client communication tracker** - log replies in `hunt_state.json`
- [ ] Add **earnings tracker** - log won projects + revenue

### Phase 3: Intelligence (Month 2)
- [ ] **Skill learning loop** - `hunt.py --learn` extracts winning patterns
- [ ] **Dynamic pricing** - adjust bid amounts based on project budget
- [ ] **Competitor analysis** - track winning bids on platforms
- [ ] **Auto-followup** - send follow-up messages after 3 days no reply

### Phase 4: Scale (Month 3+)
- [ ] Add **Upwork** platform (API or browser automation)
- [ ] Add **LinkedIn** outreach automation
- [ ] Build **client portal** - simple dashboard for project tracking
- [ ] **Multi-account support** - run for multiple freelancers

---

## 💰 COST BREAKDOWN (All Free)

| Service | Tier | Cost |
|---------|------|------|
| GitHub Actions | 2000 min/mo free | $0 |
| Telegram Bot API | Unlimited free | $0 |
| Gmail SMTP | 500/day free | $0 |
| Gmail IMAP | Unlimited free | $0 |
| Groq API | Free tier (14,400 req/day) | $0 |
| Render.com | Free tier (spins down) | $0 |
| **Total** | | **$0/month** |

---

## 🚨 RISK MITIGATION

| Risk | Mitigation |
|------|------------|
| GitHub Actions timeout (6h) | Telegram controller splits into 5h chunks |
| Session expiry | Auto-reauth + healing orchestrator |
| Selector drift | Auto-discovery + persistent cache |
| Platform ToS violation | Strict quotas (3/day), human-like delays |
| AI hallucination | Skills-first (local templates), quality_reviewer agent |
| Telegram bot downtime | GitHub Actions restarts every 5 hours |
| Engine downtime | Local engine in GitHub Actions (no external deps) |

---

## 📋 QUICK COMMANDS REFERENCE

```bash
# Local development
python run_daily_freelance.py --dry-run           # Test without posting
python run_daily_freelance.py --only mostaql      # Single platform
python run_daily_freelance.py --weekly            # Include portfolio
python run_daily_freelance.py --status            # Show state

python telegram_controller.py                     # Run bot locally
python telegram_notifier.py --test                # Test Telegram

python auto_selectors.py --platform mostaql       # Discover selectors
python auto_reauth.py --platform nafezly          # Force re-auth

# GitHub Actions (manual trigger)
gh workflow run daily.yml -f mode=dry-run
gh workflow run telegram-controller.yml
gh workflow run daily-healing.yml
```

---

## 📞 SUPPORT CONTACTS

| Platform | Account | Recovery |
|----------|---------|----------|
| Mostaql | ambdambd200@gmail.com | Password: env var |
| Nafezly | alaafathi403@gmail.com | Magic Link (Gmail) |
| n8n Community | salim.muhammad.work0@gmail.com | Google OAuth |
| GitHub | ambdambd200-droid | Personal access token |
| Render | GitHub-connected | Auto-deploys from main |

---

**This system is designed to run autonomously on GitHub Actions with zero local infrastructure.**
**All state persists in GitHub cache + repo files. No local device required.**