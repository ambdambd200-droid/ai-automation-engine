# Application — n8n Community Forum: Doru_Gradinaru

**Channel:** n8n Community Forum (community.n8n.io) — public reply
**Thread:** Built an importable guard workflow for costly AI/tool calls — looking for n8n feedback
**URL:** https://community.n8n.io/t/built-an-importable-guard-workflow-for-costly-ai-tool-calls-looking-for-n8n-feedback/296302
**Author:** Doru Gradinaru (proceedgate.dev)
**Posted:** 2026-05-20
**Status:** DRAFT — awaiting review

---

## Why this thread

- Doru **explicitly asked for feedback** — clear, low-risk reply target
- Already has 5 replies (decent discussion underway) → adding a substantive new angle stands out
- Subject matches my experience: I run a similar guard pattern in Flask for lead enrichment
- Tags: ai, execute-workflow, workflow-templates → exactly my domain

---

## Existing replies (to avoid repeating)

- nguyenthieutoan: pattern feels natural, template > node for now, asks about Wait-node vs external approval
- OMGItsDerek: agrees sub-workflow approach, agrees on clean v1 + separate review template later
- Doru (OP): planning to keep v1 simple, defer Wait-node review

**Angle to add (not in the existing thread):**
1. Per-user budgets (not just per-workflow)
2. Structured deny logs (who/what/why/when)
3. Fail-closed vs fail-open when the guard itself errors

---

## Forum reply (paste into the reply box on the thread)

```
Doru — solid pattern. I run something similar on the Flask side
for a lead-enrichment pipeline (OpenAI calls behind a webhook).
Three additions I'd suggest for the Guard Sub-workflow:

1. Per-user budgets, not just per-workflow. When a single agent
   is driving many parallel workflows for different users, a
   workflow-level cap hits the wrong person. We tag each call
   with the triggering user/tenant and budget against that. The
   sub-workflow only needs the tag passed in.

2. Structured deny logs. The most useful thing we did was write
   a JSON line for every deny with: who, what tool, why, time.
   Now we can spot patterns (one user hitting rate limits 50x
   in 5 minutes is a real signal, not noise). Easy to ship to
   a SIEM or just a file.

3. A fallback for when the guard itself errors. This is the
   unsexy one but it's bitten us twice: if ProceedGate is down
   or returns a 5xx, does the workflow fail-closed (deny) or
   fail-open (allow)? We'd default to fail-closed for the costly
   stuff, fail-open for the read-only stuff. Worth deciding
   per-tool.

On your three questions:

- Import flow: clear, the JSON + guide combo is good
- Sub-workflow pattern: yes, feels native — I agree with the
  comments above about keeping v1 simple
- Template vs community node: template first. Locking the
  interface in a node this early would block the pattern from
  evolving

Happy to share our Flask-side guard code if useful.

Alaa
ambdambd200@gmail.com
```

---

## Posting instructions

1. Register / log in to community.n8n.io (Discourse)
2. Open the thread URL above
3. Click "Reply" at the bottom of the original post
4. Paste the reply above
5. Click "Reply to Topic"
6. After posting, copy the reply URL and update status below
7. Update `Application_Pipeline.md` with the post URL + date

---

## Status

- [ ] Reviewed by user
- [ ] Posted to forum
- [ ] Reply URL saved
