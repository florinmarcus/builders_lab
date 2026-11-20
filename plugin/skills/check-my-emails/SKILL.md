---
name: check-my-emails
description: Use only for Marcus Limited (the building firm) work, when the builder asks to check the firm's emails or what came in on its jobs (e.g. "check my emails" in the Builders project). Fetches new job emails through BuildersMCP, files them by job and records the key facts. Not for personal email.
---

# Check my emails

Read `../../shared/rules.md` first.

1. Call `sync_inbox` (builders connector).
2. For each email in `emails_needing_facts`, read the body and every attachment's text, then call `save_facts` once:
   - `job`: the job ref if the email clearly belongs to one job (use `filed_to` if it is right). Leave it out if unsure.
   - `attachments`: each attachment's `document_type` and dates (`document_date`, `expires_on` for insurance and certificates).
   - `facts`: approvals (client's own words), discussions that are NOT approvals, amounts, key dates, asbestos items (one per sample, result exactly as written, plus the survey scope), certificates promised, instructions, requests. Every fact has a short summary and a quote copied word for word, with `attachment_id` when the quote is from an attachment.
   - Nothing worth recording (an order confirmation): call with an empty `facts` list so it is not offered again.
3. If `save_facts` rejects items, read the reason, fix only those, and call it again for that email.
4. If `more_waiting` is true, call `sync_inbox` again.
5. Tell the builder what came in, grouped by job: sender, date, one line each. Then anything that needs action today (deadlines, requests, expired papers). Mention emails you could not file.
