# Mock data for the demo

Agreed with Florin, 19 Nov 2026. All people, firms, addresses and numbers are invented.
Outside parties use `*.example.com` addresses (reserved, cannot belong to anyone).
Phone numbers use Ofcom's drama range `07700 900xxx`.

## Firm

**Oakline Build Ltd**, a small general builder in the made-up town of Hollowell.

| Person | Role | Persona alias |
|---|---|---|
| Dan Oakley | Owner (the builder in the demo) | – (the inbox owner) |
| Mike Turner | Site lead | `+mike` |
| Jamie Cole | Apprentice | `+jamie` |

## Jobs

### 1. Smith bathroom, 14 Oak Street (private client, Sarah Smith)

| # | When | From | What | Attachment |
|---|---|---|---|---|
| 1 | 14 Oct | Sarah Smith | Enquiry: bathroom refit | – |
| 2 | 20 Oct | Dan | Quote sent | Quote Q-1042, £6,850 + VAT |
| 3 | 22 Oct | Sarah Smith | Accepts quote, asks for start date | – |
| 4 | 4 Nov | Dan | Rotten joists found, extra £640 | Variation VO-01 |
| 5 | 4 Nov | Sarah Smith | "Yes, go ahead with the joists" (demo moment 2) | – |
| 6 | 12 Nov | Aqua Flow Plumbing | Plumber's invoice | Invoice AF-339, £1,180 |
| 7 | 17 Nov | Spark Right Electrical | "Certificate to follow" | – (stays missing) |
| 8 | today | Sarah Smith | "When do you finish? Please send the final bill." | – (moments 5, 6) |

### 2. Patel rear extension, 3 Mill Lane (Raj and Meera Patel)

| # | When | From | What | Attachment |
|---|---|---|---|---|
| 9 | 16 Oct | Architect | Drawing issue sheet, rev C | Drawings note |
| 10 | 23 Oct | Hollowell Building Control | Plans approved with conditions | Approval notice |
| 11 | 6 Nov | Structural engineer | Beam for kitchen wall removal | Engineer's letter |
| 12 | 13 Nov | Meera Patel | "Can we also take out the dining-room wall?" | – (sets up moment 4) |
| 13 | today | Hollowell Building Control | Foundation inspection booked 24 Nov | – |

### 3. Flat 12, Riverside House (council void, Hollowell District Council)

| # | When | From | What | Attachment |
|---|---|---|---|---|
| 14 | 28 Oct | Council repairs | Works order WO-2026-4471, schedule-of-rates lines, target 27 Nov | Works order |
| 15 | 29 Oct | Council repairs | Asbestos survey (HSG264 layout) | R&D survey |
| 16 | 5 Nov | Council repairs | Gas capped, keys at housing office | Gas capping note |
| 17 | today | Council repairs | "Please confirm you will finish by 27 Nov" | – |

The survey is built to test "never say no asbestos":
kitchen floor tiles, chrysotile found; hall textured ceiling, sampled, none found;
bedroom 2 locked, not accessed, presumed. Scope: kitchen and bathroom only.

### Not linked to a job

| # | When | From | What |
|---|---|---|---|
| 18 | 10 Nov | BuildMart Supplies | Order confirmation |
| 19 | today | Trade newsletter | Newsletter |

## Required items per job type (our mock list, not a legal rule)

- **Bathroom refit:** signed quote, approved variations, electrical certificate, subcontractor invoices, final photos.
- **Extension:** building control approval, structural calculations, foundation inspection, party wall agreement, completion certificate.
- **Council void:** works order, asbestos survey covering the work area, gas capping or safety record, electrical test, completion photos.

## How it runs (ADR 0005)

- **Inbox:** the builder's own Gmail. Address set in `.env` (`BUILDER_INBOX`), never in the repo.
- **Label:** every mock or simulated email carries the Gmail label `oakline-demo`. Nothing outside it is touched.
- **Reset:** delete everything labelled `oakline-demo` (emails and drafts), empty the database, re-import emails 1–18 except the "today" ones. Same start every time.
- **Today batch:** import the "today" emails (8, 13, 17, 19), all at once or one by one.
- **Live simulator:** send from the allowed sender address (`.env`, `SIMULATOR_SENDERS`) to `<inbox>+<persona>@gmail.com`. The simulator re-imports it with the persona as sender, labels it and deletes the original. Emails from any other sender are ignored.

| Alias | Shows as |
|---|---|
| `+sarah` | Sarah Smith (customer, Smith bathroom) |
| `+meera` | Meera Patel (customer, Patel extension) |
| `+council` | Hollowell District Council repairs |
| `+bc` | Hollowell Building Control |
| `+mike` | Mike Turner (site lead) |
| `+jamie` | Jamie Cole (apprentice) |
