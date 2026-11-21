# 0014: Pilot business model: Claude Team only, paid pilot, everything stored in London

Date: 21 Nov 2026. Status: accepted. Full plan: `requirements/business-plan.md`.

## Context

Florin will pitch to builders. He stays in his full-time job; a marketing partner finds customers. The goal is a cheap test of whether builders will pay, on about £100 a month for 6 months. The Frankfurt lab RDS that holds the regulations corpus (ADR 0013) is being withdrawn.

## Decision

- **Claude Team only** for firms (business terms and DPA). ChatGPT later, tools only, if a paying firm asks.
- **Email through Claude's own connectors** (Gmail, Microsoft 365). Our demo Gmail tool (ADR 0002, ADR 0005) is replaced for real firms. Own email servers are custom work at the Large firm level.
- **Prices:** pilot 3 firms at £100 for 3 months; Standard £250 setup plus £49 a month; pilot firms that stay £39 a month for a year; Large firm priced after discovery, sold only after the pilot.
- **Legal:** limited company in the partner's name, code licensed by Florin, profit 50/50; cyber and professional indemnity insurance; liability capped at 12 months' fees; DPA in the pilot agreement; Excel export and deletion within 30 days when a firm leaves.
- **Regulations corpus moves to the London server's own Postgres** (with pgvector). Re-ranking still calls Frankfurt (no Bedrock re-rank in London, ADR 0013). This changes the "where vectors live" part of ADR 0013 once done (parking lot N17).
- **Stop rule:** at month 6, switch off unless 3 firms pay full price and use it weekly.

## Options considered

- **Claude and ChatGPT from day one:** wider market, but double the testing and support; ChatGPT gets no plugin.
- **Free pilot:** easier to sign, but tells us nothing about price.
- **Per-person price:** small firms would drop users. Per firm is simpler to sell.
- **Our own Gmail link:** needs Google's security review for outside firms; Claude's connector costs us nothing.
- **Keep the corpus on RDS:** about £12 to £25 a month (guess) once the lab is gone, and data in a second region.
- **Strip personal data before it reaches Claude:** helps for names in our database, but the builder types straight into Claude, replies cannot be filled back in, free text is not fully caught, and pseudonymised data is still personal data. Kept as an extra layer for later, not the main protection.

## Consequences

- No Google review, no OAuth build for email in the pilot. Microsoft 365 needs the firm's admin at install.
- The London server may need the next size up (about £14 more a month) for the corpus.
- Business costs (accountant, insurance) are bigger than hosting; real quotes needed.
- Insurance and the cap must be in place before the first paying firm. **Changed 21 Nov 2026 (Florin):** the company, accountant and insurance wait until after the pilot; the pilot runs on a strict agreement. Cloud now about £20 to £30 a month, about £40 to £60 once pilots start (guess).
