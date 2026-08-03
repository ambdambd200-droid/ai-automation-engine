# Architecture — How Automation Actually Works

## ⚠️ Critical: I Cannot Access Your Accounts Directly

I (the AI) have **no way** to log into your accounts. I cannot:
- Log into your n8n Community account
- Log into your Nafezly or Mostaql accounts
- Read your Gmail
- Post anything on your behalf

**Only YOU can do that**, by running scripts on YOUR machine with YOUR credentials.

---

## The 3-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: AI Brain (Render Cloud) — Public              │
│  - ai-automation-engine.onrender.com                    │
│  - Generates AI content (Groq)                          │
│  - Receives webhooks (free, no auth)                    │
│  - Returns JSON to caller                               │
└─────────────────────────────────────────────────────────┘
                         ▲   ▲   ▲
                         │   │   │
                         │   │   └─ /api/n8n/reply
                         │   └───── /api/bid/generate
                         └───────── /api/contact
                                                │
                                                │ HTTPS POST
                                                │
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: Local Automation Scripts — Your Machine      │
│  (YOU run these with YOUR credentials)                 │
│                                                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │ nafezly_   │  │ mostaql_   │  │ post_forum │         │
│  │ agent.py   │  │ agent.py   │  │ _replies   │         │
│  │            │  │            │  │ .py        │         │
│  │ Playwright │  │ Playwright │  │ Playwright │         │
│  │ + Brave    │  │ + Brave    │  │ + Brave    │         │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘         │
│        │               │               │                │
│        └──────┬────────┴───────┬───────┘                │
│               │                │                        │
│        ┌──────▼─────┐    ┌─────▼──────┐                  │
│        │ Engine AI  │    │ Resend API │                  │
│        │ bid text   │    │ (send mail)│                  │
│        └────────────┘    └────────────┘                  │
└─────────────────────────────────────────────────────────┘
                                                │
                                                │ HTTPS / IMAP
                                                ▼
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: External Platforms (where you have accounts) │
│                                                         │
│  - salim.muhammad.work0@gmail.com   ← Resend sender    │
│  - ambdambd190@gmail.com            ← n8n test account │
│  - nafezly.com (account)                              │
│  - mostaql.com (account)                              │
│  - community.n8n.io (account)                         │
│                                                         │
│  Credentials live in:                                  │
│  - Browser saved sessions (Playwright profiles)        │
│  - Gmail App Password (env var, not in code)           │
│  - Resend API key (env var)                            │
│  - GROQ_API_KEY (env var, server-side)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🔐 Where Each Credential Lives

| Credential | Where | Who uses | Format |
|---|---|---|---|
| Nafezly login | Playwright Brave profile | `nafezly_agent.py` | saved session, NOT password |
| Mostaql login | Playwright Brave profile | `mostaql_agent.py` | saved session, NOT password |
| n8n Community | Playwright Brave profile | `post_forum_replies.py` | saved session, NOT password |
| Gmail password | NOT stored | n/a | use App Password instead |
| Gmail App Password | Windows env var `GMAIL_APP_PASSWORD` | `gmail_check.py`, `send_email.py` | 16-char token |
| Resend API key | Windows env var `RESEND_API_KEY` | `engine/send_email_lib.py` | starts with `re_` |
| Groq API key | Render env var `GROQ_API_KEY` | engine `actions.py` | starts with `gsk_` |

**No passwords are stored in code.** Only env vars + browser sessions.

---

## 🤖 How Automation Actually Runs

### Step 1: You (user) opens PowerShell
### Step 2: You run a script like:
```powershell
python nafezly_agent.py --bid <project_url>
```

### Step 3: The script:
1. Opens Brave browser (with your saved session)
2. Goes to Nafezly, logs in via cookie (no password needed)
3. Reads project details
4. Calls engine: `POST /api/bid/generate` → Groq writes Arabic bid
5. Submits bid via Playwright (still logged in via cookie)

### Step 4: Done. You see logs in PowerShell.

---

## ❓ Your Specific Questions

### "كيف راح تدخل الى حسابي على n8n؟"
**I don't.** `post_forum_replies.py` runs on YOUR machine. It opens YOUR Brave with YOUR saved n8n session. It posts on YOUR behalf using your logged-in browser.

### "كيف راح تدخل على حسابي في نفذلي و مستقل؟"
**Same:** `nafezly_agent.py` and `mostaql_agent.py` open YOUR Brave, navigate with YOUR saved sessions.

### "هل هناك شيء نسيته؟"

**YES — 3 things you might have missed:**

| # | What | Why |
|---|---|---|
| 1 | **Render Manual Deploy** — your engine isn't running latest code | Auto-deploy doesn't trigger on free tier; you need to click "Manual Deploy" in Render dashboard |
| 2 | **Playwright Brave profile** — saved session for each platform | Without this, scripts ask for password every run |
| 3 | **ambdambd190@gmail.com ≠ salim.muhammad.work0@gmail.com** | These are SEPARATE accounts. Your n8n test account is one; your Nafezly/Mostaql/Resend account is another. Decide which is which. |

---

## 🎯 To Get Full Automation Working

1. **Once:** Save browser sessions via Playwright (one-time setup)
2. **Daily:** Run scripts manually OR schedule via Windows Task Scheduler / cron
3. **Server side:** Engine runs automatically (Render + GitHub Actions)
4. **Verification:** You see logs / Telegram notifications / review queue at `/review`

---

## ❓ What's Missing For You to Test Now

| # | Need | How |
|---|---|---|
| 1 | Resend sender verified for `salim.muhammad.work0@gmail.com` | Verify domain in Resend (free) |
| 2 | Telegram bot token for `N8N_NOTIFY_WEBHOOK` | Create via @BotFather, set env var |
| 3 | Render Manual Deploy after latest commits | Click button in dashboard |
| 4 | Playwright Brave session saved | Run `nafezly_agent.py --login` once |

---

Last updated: July 30, 2026
