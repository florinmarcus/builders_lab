---
name: variation-log
description: Use when the builder asks "what changes did the client approve?", "show me the variations", "build the variation list", or before a final account or invoice. Lists every approved change on a job from emails and chat exports, with the client's own words.
---

# Variation log

Read `../../shared/rules.md` first.

1. Find the job: `list_jobs` if the builder did not name it, then `get_job`.
2. From the job's facts, take `approval` facts. Also list `discussion` facts separately as "talked about, not approved".
3. If the facts look incomplete, `search_job_documents` for words like approve, agreed, go ahead, extra, change.
4. Answer as a table: change, amount (ex VAT), approved by, date, channel (email or WhatsApp), exact quote, source.
5. Total the approved amounts only. Never count a discussion as approved.
6. Offer next steps as drafts: a variation summary email to the client, or a draft invoice line in Xero.
