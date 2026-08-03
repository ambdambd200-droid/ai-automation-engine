# Application Pipeline — Single Source of Truth

**Last updated:** 2026-06-14 (Gmail check + MCP fix)

## Summary

| Channel | Sent | Replies | Pending | Status |
|---|---|---|---|---|
| Direct email (Gmail) | 6 | 0 | 0 | Awaiting follow-up Jun 8 |
| Direct email (dry-runs, sites failed) | 4 | 0 | 0 | Rejected — broken forms |
| n8n Community forum (drafts) | 0 | 0 | 3 | Awaiting user review |
| Mostaql (Arabic) | 0 | 0 | Setup | Need signup + first 3 bids |
| Nafezly (Arabic) | 0 | 0 | Setup | Need signup + first service + 3 bids |
| LinkedIn posts | 0 | 0 | 3 | Scheduled Jun 5, 8, 12 |
| **Total outreach** | **6 sent + 3 forum drafts + Arabic setup pending** | **0** | **9+** | — |

---

## Sent (6) — direct email, awaiting follow-up

| # | Date Sent | Company | Contact | Status | Follow-up Date |
|---|---|---|---|---|---|
| 1 | 2026-06-01 | ZY IMMO Capital | info@zyimmo.de | Sent, no reply | 2026-06-08 |
| 2 | 2026-06-01 | Asiacruit | careers@asiacruit.com | Sent, no reply | 2026-06-08 |
| 3 | 2026-06-01 | Synergy Effect | info@s-e.lt | Sent, no reply | 2026-06-08 |
| 4 | 2026-06-01 | n8nera | n8nera@gmail.com | Sent, no reply | 2026-06-08 |
| 5 | 2026-06-01 | nocodecreative | wayne@nocodecreative.io | Sent, no reply | 2026-06-08 |
| 6 | 2026-06-01 | Nikolaos (n8n e-commerce video) | folafoluwaolaneye@gmail.com | Sent, no reply | 2026-06-08 |

**Last Gmail check:** 2026-06-04 16:12 — 0 replies. Log: `gmail_log.md`.
**Next Gmail check:** 2026-06-08.

---

## Forum drafts (3) — n8n Community, awaiting user review

| # | Target | Thread | Status | Post URL |
|---|---|---|---|---|
| 1 | mkitplug (Michael) | /t/.../297696 Figma → n8n plugin | Draft, awaiting review | — |
| 2 | easybits | /t/.../297970 Recruiter LinkedIn workflow | Draft, awaiting review | — |
| 3 | Doru_Gradinaru | /t/.../296302 Guard workflow | Draft, awaiting review | — |

**Drafts:** `Application_N8N_Community_*.md` (3 files).
**Posting tool:** `python apply_now.py`.

---

## Arabic platform setup — mostaql + nafezly ⭐ NEW PRIMARY CHANNEL

**Why pivot to Arabic platforms:**
- User is in Gaza — Arabic is the native market
- No age minimum strict (16+ on mostaql with parent consent)
- No fake credentials needed — Arabic clients care about portfolio, not degrees
- Geographic fit (Arab clients → Arab freelancer)
- Two platforms = doubled opportunity
- Bidding system = clearer feedback than email

### Mostaql (مستقل) — https://mostaql.com

| Field | Value |
|---|---|
| Status | Setup pending |
| Account | Not yet created |
| Profile | Content drafted (see `Mostaql_Setup.md`) |
| Hourly rate | $8-10/hr (start) |
| Setup guide | `Mostaql_Setup.md` |
| Target | 3 bids in first 48h, 1 service in 7d |

### Nafezly (نفذلي) — https://nafezly.com

| Field | Value |
|---|---|
| Status | Setup pending |
| Account | Not yet created |
| Profile | Content drafted (see `Nafezly_Setup.md`) |
| First service | "n8n workflow" — $25 fixed |
| Setup guide | `Nafezly_Setup.md` |
| Target | 1 service + 3 bids in first 48h |

**Bid templates:** `Arabic_Bid_Templates.md` (5 ready-to-paste templates in Arabic).

### Setup checklist (for both platforms)

- [ ] Mostaql: signup (10 min)
- [ ] Mostaql: profile + portfolio (1h)
- [ ] Mostaql: 3 bids (1h)
- [ ] Nafezly: signup (10 min)
- [ ] Nafezly: profile + portfolio (45 min)
- [ ] Nafezly: 1 service + 3 bids (1.5h)
- [ ] Both: monitor responses daily
- [ ] Add GitHub repo for ai-automation-engine (30 min) — serves as live portfolio

---

## Rejected (4) — sites had broken Apply flows, drafts deleted

| # | Company | URL | Why it failed |
|---|---|---|---|
| 1 | Make (recruitee) | https://make.recruitee.com/o/ai-automation-expect | Apply button broken |
| 2 | Mindrift | https://jobs.workable.com/view/txoV5YSrKBM8BUSZo2Efiv | Registration gated |
| 3 | Sagan Recruitment | https://saganrecruitment.com/job/ai-automation-engineer-hr85702/ | Requires 1-min video (declined) |
| 4 | Hireza | https://hireza.wuaze.com/job/ai-automation-specialist-make-com-expert-n8n-zapier-workflow-for-ai-video-creator-2 | Form loops back |

---

## Future cadence

| When | Action | Tool |
|---|---|---|
| Today | Sign up on Mostaql + Nafezly | Browser |
| Today | Complete both profiles | `Mostaql_Setup.md`, `Nafezly_Setup.md` |
| Today | Add 3 portfolio projects on each | Screenshots from `ai-automation-engine/` |
| 2026-06-05 | Send 3 first bids on Mostaql | `Arabic_Bid_Templates.md` |
| 2026-06-05 | Send 3 first bids on Nafezly | `Arabic_Bid_Templates.md` |
| 2026-06-05 | LinkedIn post 1 (educational) goes live | `LinkedIn_Posts_Series.md` |
| 2026-06-06 | Publish first service on Nafezly (n8n workflow $25) | Nafezly dashboard |
| 2026-06-08 | Re-run Gmail check (5-7 day window) | `python gmail_check.py` |
| 2026-06-08 | If 0 replies on 6 sent apps: send follow-ups | `python send_applications.py` |
| 2026-06-12 | LinkedIn post 3 (case study) goes live | `LinkedIn_Posts_Series.md` |
| Daily | Check Mostaql + Nafezly for responses | Browser |

---

## Notes

The 6 sent applications were sent via Gmail web on Jun 1 (not through
the local `send_applications.py` SMTP script, which was only dry-run tested).
The 4 dry-run entries in `sent_applications.log` are tests of the SMTP
script against the broken-form sites, not actual sends.
