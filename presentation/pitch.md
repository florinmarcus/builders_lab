# The pitch: what we offer and why us

For Florin and the partner. Built from `research/` and `evals/` only. Prices and claims about other tools are
vendor claims, checked 7 to 19 Nov 2026 (`research/market/existing-solutions.md`, `research/market/trust-check.md`).

## In two sentences

Talk to your phone, in Romanian or English, and it tells you what is happening on your jobs: what came in by
email, what the client approved, what you are owed and when, and what the regulations say. Every answer shows
where it came from, is checked before you hear it, and your data stays private and in London.

## What it does for a builder

- **You don't read your emails.** New job emails are filed by job, and the key facts are pulled out. Ask "what
  came in on Riverside?" and listen.
- **You don't type.** Speak on site, listen to the answer in short chunks. Say "next" for more, "sources" for
  where it came from.
- **Romanian or English.** Ask in Romanian, get Romanian back, with the official UK terms kept in English.
- **It answers the questions that cost money:** payment and pay less notice dates, approved changes with the
  client's own words, what is missing before handover, subcontractor papers, what to do when you run late,
  building regulations, asbestos, CDM.
- **It drafts, you send.** Emails, notices and letters in proper English, ready for you to check.

## Why not just Google or ChatGPT?

- **Google** gives you pages, not an answer about your job. It knows nothing about your emails, your client or
  your dates.
- **ChatGPT or Claude on their own** answer from what they learned in training, or from the open web. They can be
  out of date, they cite things loosely, and they don't know your firm. General chatbots have been seen giving
  wrong or old Approved Document references.
- **We** answer from two places only: your own job emails and documents, and a library of official UK regulations
  with edition dates. If it is not in there, we say "our library doesn't cover that yet".

## Why not set up Claude or Copilot with connectors yourself?

You can, and for simple things you should. What you don't get:

- **The rules library.** About a dozen official documents (Building Regulations, Approved Documents, HSE asbestos
  and CDM guidance, payment law), split by section, with edition dates, searched in a way built for building
  questions.
- **The checks.** Plain code (not AI) checks every answer: every fact has a source, payment dates are calculated,
  "no asbestos" is blocked, approvals need the client's words.
- **The building know-how.** Specialists for payments, delays, variations, paperwork and regulations, each with
  rules a builder needs.
- **The Romanian layer** (below).
- **Someone to set it up and support it**, with the data agreement and paperwork done.

## How our search is different

| | AI on its own | AI searching online | Us |
|---|---|---|---|
| Where answers come from | Training, maybe years old | Whatever pages it finds | Your jobs + official regulations library |
| Edition dates | No | Rarely | Yes, every passage |
| Quotes the section | Sometimes, can invent | Links pages | Section, edition and link; invented citations are checked |
| Says "I don't know" | Rarely | Rarely | Yes, built in |

How it works: the question is searched two ways at once, by meaning and by exact words (so codes like "B1",
"FD30" or "regulation 7" are found), the best 50 passages are ranked again, and only the top 5 go to the AI with
the instruction to answer from them only.

## Honest accuracy

Nobody on the market publishes how often their AI is wrong. We do.

- On 342 builder test questions about regulations, **58% of answers were judged correct and grounded** in the
  latest setup (an AI judge from another company, not yet checked by a person). Up from 31% two days earlier.
- **0 citations to passages that do not exist.**
- **85% of off-topic questions were correctly declined** instead of answered.
- Most failures are documents not in the library yet, not made-up answers. The number goes up as the library
  grows.

Say it plainly: it is not perfect, so it shows you the source and checks itself, and a person still signs.
(Source: `evals/experiments/J1-answers-live-vs-E5.md`, 21 Nov 2026.)

## What others offer and promise

| Who | What | Price | What they promise |
|---|---|---|---|
| StructureGPT, BuildingRegs.app, Struck | Building regulations Q&A in English | Free to £69 a month (StructureGPT) | Cites clauses; none publishes accuracy; terms say check it yourself |
| RAMSReady, Ramsgen, DocGen | AI RAMS | £29 one-off to £49 a month (RAMSReady) | No accuracy guarantee; liability capped at about a year of fees |
| QuickPrice, QuoteSmith and others | AI quotes | Mostly free tiers | "Not liable" for AI prices |
| Tradify, Powered Now, Fergus | Job management apps | £23 to £45 per user a month | No accuracy figures |
| Xero | Accounting | | Security certificates (ISO 27001, SOC 2), on HMRC's digital tax list. No AI accuracy promise |
| Copilot (Microsoft 365) | Searches your inbox, in Romanian | About £16 per user a month (one source) | General tool, no building rules or checks |

**Where we don't overlap:** we don't do quotes, RAMS documents or job scheduling. We sit on top of the email and
tools a firm already has and answer from them, with the rules.

**What we promise (and they don't):** every fact cited; checked by code before you hear it; published test
results; never sends anything for you; never trains on your data; data in London; a data agreement; your data
exported and deleted when you leave. **What we don't promise:** that it is always right. Nobody honest can.

## Romanian: why not just talk to ChatGPT in Romanian?

Any AI can reply in Romanian. The problem is what happens in between.

- **The search is in English.** UK rules are in English. A Romanian question searched as it is finds the wrong
  passages. We first turn Romanian building words into the right UK terms with a building glossary (plain code),
  then search.
- **Terms that don't match.** "Deviz" is not a UK quote. One Romanian building permit is two UK regimes. There is
  no UK "diriginte de șantier". We explain these instead of translating them word for word.
- **Official terms stay in English** in brackets, e.g. "notificare de plată redusă (pay less notice)", so the
  builder can use the right word with clients and councils.
- **Quotes stay in English** with a Romanian translation next to them, so nothing is lost.
- **Anything that leaves the firm is in proper English** (emails, notices, invoices), with a short Romanian
  summary for the builder.
- **The checks work in Romanian too**: "fără azbest" is blocked like "no asbestos".

Be honest: the glossary still needs a review by a Romanian tradesperson (most rows are not yet checked).

## Price (for the pilot)

Pilot: £100 for 3 months. Then £250 setup and £49 a month per firm, plus the firm's own Claude Team plan (about
$25 per person a month). Details: `requirements/business-plan.md`.
