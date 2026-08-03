# Application — n8n Community Forum: easybits

**Channel:** n8n Community Forum (community.n8n.io) — public reply
**Thread:** Recruiter friend was losing half her day to manually typing LinkedIn profiles into a sheet — built her a workflow that ends the retyping
**URL:** https://community.n8n.io/t/recruiter-friend-was-losing-half-her-day-to-manually-typing-linkedin-profiles-into-a-sheet-built-her-a-workflow-that-ends-the-retyping/297970
**Author:** easybits
**Posted:** 2026-06-03
**Tags:** workflow-building, slack, google-sheets, ai
**Status:** DRAFT — awaiting review

---

## Why this thread

- Subject matches what I built: lead enrichment pipeline (Python + OpenAI + webhooks)
- 0 replies yet, 19 views (very fresh) → first thoughtful reply will be the visible one
- Concrete technical improvements I can offer (rate-limit, dedupe, confidence score)
- Tags include "ai" + "google-sheets" + "slack" → same toolchain I use

---

## Forum reply (paste into the reply box on the thread)

```
This is the right problem to solve. I built a similar pipeline
(Python + OpenAI + Sheets) for a lead-gen client last month and
ran into the same traps. A few things that would extend what
you've got:

1. Rate-limit + backoff. LinkedIn profile endpoints are sensitive
   — the scraper will 429 you within 10-15 requests if you go
   too fast. Add a sleep + exponential backoff in the HTTP node,
   and a "resumable" flag in the sheet so you can pick up after
   a throttle instead of restarting.

2. A confidence / parse-quality score. Not every profile parses
   cleanly. Names with non-ASCII characters, multi-location
   people, and senior folks with 5+ jobs break naive extractors.
   I have the LLM output a 0-1 confidence score, and the workflow
   only writes rows above 0.7. Below that, it flags the row for
   manual review instead of polluting the sheet.

3. Dedupe by LinkedIn URL + name. The same recruiter will often
   search the same company twice in a week. Without a dedupe
   step you'll double-process the same person and waste API
   calls.

One more: send the recruiter a Slack ping (or a brief email
summary) when a batch finishes, with counts of "clean",
"low-confidence", and "errors". The recruiter trusts the
pipeline more when they can see those numbers.

Happy to share the Python enrichment code if useful.

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
