---
name: subcontractor-pack-check
description: Use when the builder asks whether subcontractors' paperwork is in order: insurance in date, RAMS received, certificates. For example "are my subbies' papers OK on the office job?".
---

# Subcontractor pack check

Read `../../shared/rules.md` first.

1. Call `list_missing_items` for the job. Look at the subcontractor items (RAMS, insurance).
2. For each insurance certificate, give the insurer details from `get_job` documents and the expiry date. Flag "expired" and "expiring soon" first.
3. List what is missing by subcontractor.
4. Offer draft emails to each subcontractor asking for the missing or renewed papers. Never send.
5. Do not judge or rank subcontractors. Report the papers only.
