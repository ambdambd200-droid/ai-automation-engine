# Alaa Fathi — AI Operations & Workflow Automation Engineer

**AI Operations | Prompt Engineering | API Integration | No-Code/Low-Code Architecture**

📍 Egypt · Remote-first · Available for freelance projects · ambdambd200@gmail.com

---

## 👋 About Me

I build automated systems that save businesses **10–40+ hours of manual work per week**. Instead of hiring more staff, I design AI-driven workflows that operate 24/7 — no continuous human oversight required.

With a hybrid skill set spanning **traditional code (Python/JavaScript)** and **no-code/low-code platforms (n8n, Make, Zapier)**, I bridge the gap between full custom development and drag-and-drop simplicity. Every solution I deliver is documented, secure, and built to scale.

**What makes me different:**
- I don't just deploy tools — I engineer the prompt logic, the data flow, and the error handling
- Every workflow I build has a clear audit trail and monitoring dashboard
- I optimize for *reliability* first, *features* second

---

## 🛠️ Core Competencies

| Domain | Skills |
|--------|--------|
| **AI Workflow Automation** | End-to-end pipelines from trigger → AI processing → output |
| **Prompt Engineering** | Multi-step prompt chains, JSON-structured output, validation loops |
| **API Integration & Webhooks** | REST APIs, OAuth, webhook listeners, rate-limit handling |
| **No-Code / Low-Code** | n8n, Make (Integromat), Zapier, Airtable, Notion |
| **AI Agents Deployment** | Autonomous agents for lead routing, classification, monitoring |
| **Backend & Data** | Python, Flask, SQLite, JSON, Git, Linux/Bash |

---

## 🚀 Featured Projects

### 1. AI Workflow Automation Engine *(self-hosted, production-ready)*

A complete self-hosted automation platform that accepts webhooks, runs multi-step AI workflows, and logs every execution. Built because most cloud automation tools are either too expensive or too locked-in.

**Architecture:**
- **Backend:** Flask + Python 3.12
- **Workflows:** YAML-defined (declarative, version-controlled)
- **AI:** OpenAI API integration (GPT-4o-mini for cost efficiency)
- **Storage:** SQLite (no external DB needed)
- **Frontend:** Live execution dashboard (HTML/JS)
- **Deployment:** Auto-start on Windows login, runs locally on `127.0.0.1:5000`

**Workflow actions supported:**
1. `http_request` — call any external API with templated payloads
2. `ai_prompt` — run structured LLM calls (system + user prompts)
3. `transform` — apply templates and extract JSON fields
4. `condition` — branch on values (e.g. priority_score > 8)
5. `log` — persist step results to the execution history

**Example workflow — `lead_capture.yaml`:**
- Receives lead via webhook
- Logs the raw input
- Calls GPT-4o-mini to enrich (category, priority score, suggested action)
- Branches on priority score
- Persists the enriched lead to SQLite

**What this proves:** I can build production-grade automation infrastructure, not just configure Zapier zaps.

**Stack:** `Python` · `Flask` · `YAML` · `OpenAI API` · `SQLite` · `JavaScript`

→ Code in [`ai-automation-engine/`](./ai-automation-engine/)

---

### 2. AI-OS-Agent *(vision-controlled desktop automation)*

A desktop AI agent that takes a screenshot, reasons about the next action with a vision-language model, and executes mouse/keyboard commands via `pyautogui`. Used as the hands-on layer for jobs that don't have an API.

**Features:**
- Vision LLM integration (Gemini / OpenRouter / **Groq Llama 4 Scout**)
- Privacy mode (auto-blurs sensitive regions before sending screenshots)
- "Switch window" mode (uses existing app, no duplicate launches)
- Configurable per-instruction confirmation prompts
- Coordinate validation (rejects clicks outside screen bounds)
- Fast execution (0.15s moveTo, 0.02s type interval)

**Supported actions:** `CLICK (x y)` · `TYPE text` · `PRESS key` · `SCROLL n` · `DONE`

**What this proves:** I can integrate modern VLMs into real workflows with reliability engineering (input validation, retry logic, error handling).

**Stack:** `Python` · `Groq API` · `Llama 4 Scout (17B VLM)` · `pyautogui` · `MCP`

---

### 3. Lead Capture & Enrichment Pipeline

End-to-end pipeline that turns a raw contact form submission into a categorized, scored, ready-to-route lead — without a human in the loop.

**Flow:**
1. Webhook receives `{name, email, company, message}`
2. AI classifies as `hot / warm / cold` and assigns a 1-10 priority score
3. Conditional branch: high-priority leads trigger a Telegram notification
4. All enriched data persists to SQLite with full audit trail
5. Dashboard shows real-time execution history

**Impact (simulated metrics):** Reduces manual lead processing from ~12 hours/week to under 1 hour/week (~92% time saved).

**What this proves:** I can deliver full vertical slices — webhook → AI → branching → persistence → UI — in a single self-contained project.

**Stack:** `Python` · `Flask` · `OpenAI GPT-4o-mini` · `Telegram Bot API` · `SQLite` · `HTML/JS`

---

## 💼 Services

| Service | What you get |
|---------|--------------|
| **Workflow Audit & Design** | Analysis of your manual processes + automation blueprint |
| **Custom Automation Build** | End-to-end AI workflows deployed and documented |
| **Prompt Systems** | Multi-step prompt chains with structured output and validation |
| **Integration Setup** | Connect your CRM, email, database, messaging tools |
| **Maintenance & Optimisation** | Monitoring, refactoring, scaling existing automations |
| **Desktop AI Agents** | Vision-controlled automation for tasks without APIs |

**Engagement models:** fixed-price, milestone-based, or hourly. Remote only.

---

## 📚 What I'm Learning Right Now

- **Browser-Use** — DOM-based AI browser automation (no more hallucinated pixel coordinates)
- **Set-of-Mark (SoM)** — pre-process screenshots into numbered element lists for VLMs
- **Self-hosted LLM deployment** — for clients with strict data-residency requirements

---

## 📫 Contact

- **Email:** ambdambd200@gmail.com
- **GitHub:** [github.com/alaafathi](https://github.com/alaafathi)
- **LinkedIn:** linkedin.com/in/alaa-fathi-2b3100413
- **Active platforms:** Working Nomads · We Work Remotely

---

## 📊 Repository Stats

This profile is actively maintained. Recent updates:
- ✅ 6 freelance job applications sent (Working Nomads + We Work Remotely)
- ✅ LinkedIn profile updated with bilingual content + 3 project showcases
- ✅ AI Automation Engine v1.0 deployed locally with auto-start
- ✅ AI-OS-Agent v1.0 (Groq-powered) deployed for desktop automation

Last updated: 2026-06-04
