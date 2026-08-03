# Plan: Autonomous Email Agent — Phase 1

## Goal
A self-improving email agent that checks Gmail, classifies each message (interested / question / reject / spam / follow-up-needed), generates a professional AI response, sends it, and learns from each interaction by storing patterns in the skills library.

## Approach
Build a single `email_agent.py` script that:
1. Connects via IMAP (reuses `gmail_check.py` authentication)
2. Scans all inbox messages from the last N days
3. For each unseen/recent email: extracts body + subject + sender
4. Classifies using `keyhub_client.ai_generate()` with a structured prompt
5. Based on classification:
   - **interested**: Generate reply with next steps + pricing
   - **question**: Answer + ask clarifying questions
   - **negotiation**: Discuss price within limits
   - **reject**: Polite thank-you (no further action)
   - **spam/auto**: Skip
   - **follow_up_needed**: Generate follow-up to a sent app with no reply
6. Writes the generated response to `hunt_decisions.md` for user review (not auto-send for safety)
7. Tracks every thread in `email_agent_state.json` (conversation history, classification, sent/not)
8. After send, saves the successful exchange as a skill in `skills/learning/email/`

## Files touched
- **NEW** `email_agent.py` — main agent (~350 lines)
- **NEW** `email_agent_state.json` — thread state database (gitignored)
- **MODIFY** `.gitignore` — add `email_agent_state.json`
- **MODIFY** `skills/index.json` — new learned email patterns indexed
- **MODIFY** `quota.py` — if email_agent needs its own quota

## Key decisions
- **Decision:** Write classified replies to `hunt_decisions.md` instead of auto-sending
  **Alternatives considered:** Auto-send via SMTP; draft mode in Gmail
  **Why this one:** User review prevents AI mistakes; matches existing `hunt.py` workflow
- **Decision:** Use `keyhub_client.ai_generate()` for classification + response
  **Alternatives considered:** Local rules; regex-based classification
  **Why this one:** AI handles Arabic + English, nuance, and context; zero cost via Groq
- **Decision:** Flat JSON state file, not SQLite
  **Alternatives considered:** SQLite, YAML
  **Why this one:** Simple, grepable, less overhead; matches skills/ convention
- **Decision:** Check all inbox, not just known recipients
  **Alternatives considered:** Only known recipients (current gmail_check.py behavior)
  **Why this one:** New clients may reply from unknown addresses; wider net

## Risks / unknowns
- Gmail App Password may expire or be revoked
- IMAP rate limits if inbox is large (Gmail: ~2500 queries/day)
- AI classification may mislabel a spam as a real lead (false positive is OK, false negative is bad)
- User must review + approve in hunt_decisions.md — agent does not auto-send

## Rollback plan
Delete `email_agent.py` and `email_agent_state.json`; revert to existing `gmail_check.py`

---

## Critique round (self)

### Architecture & Design
- Tight coupling to IMAP — fine for Gmail, need a provider abstraction if adding Outlook later
- State file uses thread_id (message_id without angle brackets) as unique key — OK for now

### Correctness & Edge-Case
- Multi-reply threads where user already replied manually → agent should detect and skip
- Arabic emails need correct charset detection (IMAP returns =?UTF-8?B? encoded subjects)

### Simplicity & Risk
- Single file for now; refactor into module if it grows past 500 lines
- Key risk: AI hallucinating a reply that sounds wrong — mitigated by user review gate

### Addressed critiques
- Multi-reply detection → scan "Re:" prefix and check state file for existing entry
- Arabic encoding → use `email.header.decode_header()` which already handles it
