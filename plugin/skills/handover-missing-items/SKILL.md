---
name: handover-missing-items
description: Use when the builder asks "what's still missing before I can finish/hand over this job?", "can I close this job?", or wants a completion checklist.
---

# What's missing before handover

Read `../../shared/rules.md` first.

1. Call `list_missing_items` for the job.
2. List missing items first, then expired or expiring items, then what is in place, each with its source.
3. For pending items, check `get_job` facts for promises (for example "certificate to follow next week") and say who promised what, and when.
4. Say clearly that the list is the firm's own checklist, not a legal requirement.
5. Offer draft chase emails for missing items. Never send.
