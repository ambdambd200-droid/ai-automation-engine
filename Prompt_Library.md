# Prompt Library — Working Prompts

**Purpose:** Save prompts that work, so we don't lose them. Versioned by date.

---

## 1. Groq Llama 4 Scout — Desktop Action (AI-OS-Agent)

**Used in:** `C:\Users\A\Desktop\AI-OS-Agent\app_groq.py`
**Working model:** `meta-llama/llama-4-scout-17b-16e-instruct`
**Temperature:** 0.2
**Reliability:** 6/10 (hallucinates coordinates — coordinate validation in place)

```
You are a human-like assistant. The main goal is: {TASK}.
Look at the current screenshot and decide the next single action.
You can reply with ONE of these commands:
1. CLICK X Y  -> To click on a button, link, or input field.
2. TYPE text_here -> To type text into an active input field.
3. PRESS key_name -> To press a keyboard button (e.g., enter, backspace, tab).
4. SCROLL down OR SCROLL up -> To scroll the page or window.
5. WAIT 3 -> To wait for a few seconds if a page is still loading.
6. DONE -> ONLY when the main goal is fully finished.
Reply with the command ONLY. No explanations.
```

**Note:** Coordinate validation `[0, 1366] x [0, 768]` enforced in `parse_and_execute`.

---

## 2. Groq Llama 4 Scout — Gmail Reply Detection

**Used in:** AI-OS-Agent desktop control
**Reliability:** 8/10 (text reasoning is solid)

```
You are checking a Gmail inbox screenshot. Look at the email list.
For each email, determine: (a) sender, (b) is it a reply to a job application, (c) what is the subject.
Reply in this exact format:
SENDER: [email]
REPLY: [yes/no]
SUBJECT: [text]
---
(next email)
DONE: [count of replies found]
```

---

## 3. OpenAI GPT-4o-mini — Lead Enrichment (AI Automation Engine)

**Used in:** `ai-automation-engine/workflows/lead_capture.yaml`
**Working model:** `gpt-4o-mini`
**Temperature:** 0.3
**Reliability:** 9/10

**System:**
```
You are a lead enrichment assistant. Extract and categorize the following lead information.
Always respond with valid JSON only, no extra text.
```

**User:**
```
Analyze this lead: Name: ${input.name}, Email: ${input.email},
Company: ${input.company}, Message: ${input.message}.
Return JSON with: category (one of: hot/warm/cold),
priority_score (1-10), suggested_next_action, summary (1 sentence).
```

---

## 4. LinkedIn Intro Post (Alaa Fathi, bilingual)

**Used in:** `LinkedIn_Profile_Content.md`
**Reliability:** 10/10 (human-written, published)

EN: See `LinkedIn_Profile_Content.md` section 6
AR: See `LinkedIn_Profile_Content.md` section 6

---

## 5. Job Application Short Pitch (Template A)

**Used in:** `Proposal_Templates.md` → Template A
**Reliability:** 10/10 (proven, used 6+ times)

```
Subject: AI Workflow Automation — Cut manual work by 30-50%

Hi [Client Name],

I read your post and I can help. I build AI-driven automation systems
that eliminate repetitive manual work — no round-the-clock human
supervision needed.

Here's a similar result from a recent project:
- Built an automated lead enrichment pipeline using AI + webhooks
- Reduced weekly manual processing from 12 hours to under 1 hour
- Tech: Python, OpenAI API, n8n, SQLite

I'd love to hear more about your current workflow so I can propose a
concrete solution. Do you have 15 minutes for a quick call this week?

Best,
Alaa Fathi
AI Operations & Workflow Automation Engineer
```

---

## 6. Follow-up (Template C, day 3-5)

**Used in:** `Proposal_Templates.md` → Template C

```
Hi [Client Name],

Just following up on my proposal for [project name]. I'm flexible on
scope and happy to adjust the plan based on your budget or timeline.

If you'd prefer, I can start with a small test automation for [specific
small task] to show the value before committing to the full build.

Let me know if you have any questions.

Best,
Alaa Fathi
```

---

## Add new prompts

When a prompt works well, append it here with:
- Use case
- Model + temp
- Date added
- Reliability score (1-10)
- Full prompt text
