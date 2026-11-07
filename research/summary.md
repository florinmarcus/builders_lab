# Research summary: construction AI market and sources

Checked 7 Nov 2026. One page. Details and citations are in the linked files. Full report: `reports/Construction AI market and sources.md`.

## Key findings

1. **No Romanian offer exists.** Of about 30 AI tools and a dozen established apps, none offers Romanian Q&A over UK building rules, CDM or tax paperwork. Procore supports Polish, not Romanian. See `market/existing-solutions.md`.
2. **Each single feature is crowded and cheap in English.** Approved Document Q&A with citations (StructureGPT: free, £19, £69 a month). AI RAMS (RAMSReady: £29 one-off, £49 a month). AI quoting apps. AI receptionists (about £39 to £149 a month, unverified). Trades apps cost £25 to £45 per user per month.
3. **The legal core can be ingested.** Legislation, Approved Documents, HSE guidance and HMRC CIS/VAT guidance are under the Open Government Licence v3.0. Commercial use is allowed with attribution and no implied endorsement. See `domain/methodology-sources.md`.
4. **The sources builders quote most cannot be ingested.** British Standards, NHBC Standards, warranty manuals, RIBA Plan of Work, JCT and NEC are commercial copyright. Link and cite them, do not store them. UK law gives no commercial text-mining exception (confirmed March 2026).
5. **Paperwork grows with firm size.** Sole traders: quotes, invoices, CIS statements, scheme certificates, MTD from April 2026 if over £50,000. Small crews: monthly CIS returns and CDM client duties on homeowner jobs, which many may not know they hold. Design-and-build: CDM roles, building control, CHAS Elite, payment notices, handover packs. See `domain/user-levels.md`.
6. **Admin is done at night.** Surveys put it at about 5 to 8 hours a week, mostly evenings. Figures are soft and sponsored by software firms.
7. **The community is large but shrinking.** Romanians are about 5% of UK construction workers and about 19% in London. Our rough estimate: 100,000 to 110,000 people. Old data says two thirds are self-employed. Departures outpace arrivals. See `market/romanian-community.md`.
8. **The best channel is the Romanian Builders Network UK.** Its June 2026 event covered qualifications, CIS and VAT. Next event: 21 Nov 2026, London, 80 places.
9. **A starter glossary has 102 rows.** Only a few are sourced. Key traps: one Romanian building permit equals two UK regimes; "deviz" is not a UK quote; no UK "diriginte de șantier". See `domain/glossary.md`.

## The gap we could fill

A Romanian chat assistant over English UK sources, for small crews and CIS sole traders, not for architects. It would answer the duties small builders miss: CDM client duties on homeowner jobs, CIS returns and statements, reverse-charge invoices, written variations and quotes. Every answer would show the English clause and link. A checked glossary would keep terms right. Delivery where the community already talks, likely WhatsApp (not yet sourced).

Language alone is not a moat. Competitors can add Romanian fast, and builders may already use ChatGPT. The moat would be accuracy on terms and clauses, small-firm focus, and trust through the community.

## Open questions for Florin

1. Which user level first? The research points to small crews (2 to 10) and CIS sole traders, not design-and-build firms. Do you agree?
2. Is Robert's 21st Century Design a contact, a target customer, or only an example?
3. England only at first, or Scotland and Wales too? Scotland and Wales have their own rules.
4. Should we pay for any licence (BSI, NHBC)? Or stay on OGL sources plus links?
5. WhatsApp, web chat, or both for the first version?
6. Do we want legal advice on RAG and copyright before or after a prototype?
7. Can you attend the Romanian Builders Network event on 21 Nov 2026 (£35) to talk to builders?
8. Who can review the glossary? We need a native speaker who works in UK construction.
9. Do we touch quotes and invoices, or stay with rules and paperwork Q&A? Quoting is very crowded.

## Suggested next steps

1. Build a small OGL corpus: Building Regulations 2010, Approved Documents A to T, Manual to the Building Regulations, HSE CDM domestic-client pages and L153, HMRC CIS and reverse charge guidance. Keep edition dates as metadata.
2. Write 30 to 50 test questions in Romanian, as small builders would ask them, with expected English clauses. Use them as the first eval set.
3. Test general models (ChatGPT, Claude) on those questions in Romanian. This shows how big the gap really is.
4. Get the glossary reviewed by a native-speaker tradesperson. Turn it into a structured file for query rewriting.
5. Talk to 5 to 10 Romanian builders (network event, Facebook groups) about pain points and willingness to pay.
6. Check the unverified items: CDM construction phase plan rule, CIS 340, Scottish licence, warranty terms, Facebook group sizes.
7. Get a short legal opinion on the OGL attribution text and on linking to copyrighted standards.
