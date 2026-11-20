---
name: payment-notice-check
description: Use for Marcus Limited (the building firm) when the builder asks about payment notices, pay less notices, payment applications or final dates on a job, or what happens if a notice is missed (UK Construction Act).
---

# Payment notice check

Read `../../shared/rules.md` first.

1. Call `get_payment_dates` for the job. Never work out the dates yourself.
2. Say the next deadline first, in one line: what, by when, who gives it, for which contract.
3. Then each contract's current cycle: due date, payment notice by, pay less notice by, final date for payment, and who gives each notice (`who_gives_notices`).
4. For what the law says (for example "what if I miss it?"), call `search_regulations` and answer only from the passages: Construction Act ss110A, 110B and 111. Cite section and edition date.
5. Note that the dates come from the contract terms stored for the job. Ask the builder to check them against the signed contract.
6. Offer a draft payment notice or pay less notice email. Never send it.
