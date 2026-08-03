# Application — n8n Community Forum: mkitplug (Michael)

**Channel:** n8n Community Forum (community.n8n.io) — public reply
**Thread:** I built a free Figma plugin that sends design data to n8n — looking for agencies
**URL:** https://community.n8n.io/t/i-built-a-free-figma-plugin-that-sends-design-data-to-n8n-looking-for-agencies-to-build-real-workflows-with/297696
**Author:** Michael (mkitplug) — n8n dev, built MKitFlow
**Posted:** 2026-06-01
**Status:** DRAFT — awaiting review

---

## Why this thread

- Michael is **explicitly looking for 2-3 agencies** to pilot with — direct call for collaboration
- The plugin sends Figma frame data to n8n webhooks → directly compatible with my Flask engine
- 0 replies yet → first good reply will stand out
- Figma + n8n is a niche where most responders are agencies, not solo builders

---

## Forum reply (paste into the reply box on the thread)

```
Hey Michael,

Nice work — I've been looking for exactly this kind of bridge. The
"click a button in Figma, data lands in n8n" pattern removes the
worst step in the loop (manual export → email → re-import).

Quick context on me: I run a small automation studio. Most of my
clients are solo founders and small agencies. A few still do the
"screenshot the frame, paste into Notion, write a ticket by hand"
dance every week.

What I'd love to pilot with you: a design-token-to-GitHub workflow.
The use cases I can think of off the top:

- A design system maintainer who copies color/typography values
  into a styles repo by hand
- A dev shop that wants design changes to trigger Jira tickets
  with frame previews attached
- An agency that generates client handoff PDFs manually

One technical question: does the plugin send the full frame tree
recursively, or just top-level metadata? I have a Flask webhook
receiver with OpenAI enrichment, and I want to make sure my schema
won't choke on nested layers.

Happy to be one of your pilot agencies if you have bandwidth.
I'm in GMT+3, can jump on a quick call this week.

Alaa
ambdambd200@gmail.com
```

---

## Posting instructions

1. Register / log in to community.n8n.io (Discourse)
2. Open the thread URL above
3. Click "Reply" at the bottom of the original post
4. Paste the reply above
5. Click "Reply to Topic" (not "Create New Topic" — that would make a new thread)
6. After posting, copy the reply URL and update status below
7. Update `Application_Pipeline.md` with the post URL + date

---

## Status

- [ ] Reviewed by user
- [ ] Posted to forum
- [ ] Reply URL saved
