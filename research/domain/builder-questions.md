# Hard everyday questions for a small UK building firm

Date: 20 Nov 2026. Made by a Claude Code subagent asked to think as a small repair and refurbishment firm (5 to 30 people, council and housing-association flats, England). It read `research/summary.md`, `research/interviews/` (builder-1), `research/domain/asbestos.md`, `council-contracting.md`, `user-levels.md`, the corpus inventories, `requirements/prototype.md` and `corpus/sources.yaml`. No web search.

**Status: a working list, not research findings.** Where a point comes from a repo file, that file is named. "(guess)" marks the subagent's own judgement as a builder, with no source. Use it to choose the demo corpus and to write test questions; check each answer against the documents.

## Top 20, ranked by how often × cost of a wrong answer

| # | Question (builder's words) | Theme | How often | Corpus ids |
|---|---|---|---|---|
| 1 | Can I start ripping out / drilling here? Does the survey cover this room? | Asbestos | daily (builder-1) | car2012, hse-hsg264, hse-l143, hse-asbestos-duty, hse-hsg227 |
| 2 | The lads found something that looks like asbestos. What now? | Asbestos | weekly (guess) | hse-asbestos-em1, car2012, hse-asbestos-essentials |
| 3 | Licensed, notifiable or non-licensed asbestos work? Can my men do it? | Asbestos | weekly (guess) | hse-nnlw, hse-asbestos-licensing, hse-asbestos-essentials, hse-l143, car2012 |
| 4 | Who is the CDM client on a homeowner job? Do I need a plan? An F10? | CDM | weekly (summary.md, user-levels.md) | cdm2015, hse-cdm-domestic-clients, hse-l153, hse-cis80 |
| 5 | Awaab's Law job: what deadlines, what must I record? | Damp and mould | weekly (council-contracting.md) | awaab-guidance-phase1/2, awaab-consolidated, awaab-triage-phase2 |
| 6 | Do I need building control for this wall, bathroom, windows? | Building control | weekly | br2010, br-approval, ada, ba1984 |
| 7 | Flat entrance fire door in a council block: what rating, who checks? | Fire | weekly on council work (sources.yaml) | fser-fire-doors, adb, fser2022, fso2005 |
| 8 | Pipes and cables through compartment walls: what fire stopping? | Fire | weekly (guess) | adb, br2010 |
| 9 | VAT or "reverse charge" on this invoice? | VAT | every invoice (user-levels.md) | vat-drc-guide, hmrc-vatrevcon |
| 10 | Deduct 20%, 30% or nothing from this sub? Verified? | CIS | monthly (builder-1: "complications with CIS") | hmrc-cis-340, govuk-cis-contractor |
| 11 | Paid less: was the pay less notice on time? Can I suspend or adjudicate? | Payment | monthly | hgcra1996-p2, scheme-cc-1998 |
| 12 | What goes in the RAMS for dust, silica, lead, ladders? | Site safety | daily (guess) | mhswr1999, coshh2002, wah2005, HSE leaflets |
| 13 | What asbestos training do my men need, how often? | Asbestos | monthly (asbestos.md) | hse-asbestos-training, hse-l143, car2012 |
| 14 | Is this electrical, gas or window job notifiable? Can my man sign it off? | Building control | weekly | adp, cps-schemes, gsiur1998, adj |
| 15 | Void flat EICR shows Code 1/2 defects: what before re-let? | Electrical safety | weekly (council-contracting.md) | ess2020, ess-guidance |
| 16 | Smoke and CO alarms in this void, or with a new boiler? | Fire | weekly (guess) | scoar2015, scoar-guidance, adj, adb |
| 17 | Nothing paid this month: do I still file the CIS return? | CIS | monthly | cis-amd-2026, govuk-cis-contractor |
| 18 | Client OK'd the extra on WhatsApp: is it binding? | Contracts | weekly (summary.md) | not in corpus |
| 19 | Which VAT rate: 20%, 5% or 0%? | VAT | monthly (guess) | vat-notice-708 |
| 20 | Homeowner signed at home: can he cancel in 14 days? | Consumer law | monthly | not in corpus (user-levels.md cites the 2013 Regulations) |

## Demo set chosen (20 Nov 2026)

Already parsed: br2010, adb (volume 1), hse-hsg264, hse-hsg227. Added: car2012, cdm2015, hgcra1996-p2 (legislation XML); hse-cdm-domestic-clients, fser-fire-doors, awaab-guidance-phase1, hmrc-cis-340, vat-drc-guide (web pages); hse-l143 and hse-asbestos-em1 (PDFs, parked: their layout needs parser work). The subagent's estimate: these cover about 15 of the 20; the next tier (cps-schemes, adp, ess-guidance, scoar-guidance, vat-notice-708, hse-nnlw, br-approval) brings it to about 18.

## Gaps the corpus cannot answer

- Contract formation and variations (18): no contract-law source; JCT and NEC are paid.
- Consumer law (20): Consumer Contracts Regulations 2013 and Consumer Rights Act 2015 not harvested.
- Paid British Standards the rules point to (BS 8214, BS EN 1634, BS 7671, BS 5250): link only.
- Hazardous waste (asbestos consignment notes), PUWER, LOLER, PPE, workplace rules: not harvested.
- Employment status, right to work, employers' liability insurance: not in corpus.
