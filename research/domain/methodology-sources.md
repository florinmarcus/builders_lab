# UK methodology and rule sources for the RAG store

Checked 7 Nov 2026. Not legal advice. Get legal advice before launch.

## Rule of thumb

- **Ingest in full:** Crown copyright under the Open Government Licence v3.0 (OGL). This covers legislation, Approved Documents, HSE guidance and HMRC guidance.
- **Link and summarise only:** commercial copyright. This covers British Standards, NHBC, warranty manuals, RIBA, JCT, NEC and scheme sites. Store metadata, clause numbers and links. Do not store the text.

OGL v3.0 allows commercial use "in your own product or application". Conditions: attribution, and no suggestion of official status or endorsement. Rights end on breach. Logos, personal data and third-party rights are not covered. [OGL v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)

Default attribution: "Contains public sector information licensed under the Open Government Licence v3.0." HSE prefers: "Contains public sector information published by the Health and Safety Executive and licensed under the Open Government Licence." [HSE copyright](https://www.hse.gov.uk/help/copyright.htm)

## Source table

| Source | Covers | Free / paid | Format | Licence | Can we ingest? | URL |
|---|---|---|---|---|---|---|
| Building Regulations 2010, GPDO 2015 and other Acts/SIs | Legal requirements, permitted development | Free | HTML, PDF, XML | OGL v3.0, Crown and database right | **Yes**, with attribution | https://www.legislation.gov.uk/help#licence |
| Approved Documents A to T, Regulation 7 (England) | Statutory guidance | Free | PDF, merged searchable PDF | OGL v3.0 except where stated | **Yes**. Cite but do not copy British Standard extracts inside them | https://www.gov.uk/government/collections/approved-documents |
| Manual to the Building Regulations (2020) | Plain guide to the regs | Free | PDF | OGL v3.0 (GOV.UK) | **Yes** | https://www.gov.uk/government/collections/approved-documents |
| HSE guidance (L153 CDM 2015, CIS and INDG leaflets) | CDM duties, site H&S | Free online; printed books paid | HTML, PDF | OGL, except Law Poster suite, Accident Book, photos, film | **Yes**, text only. Strip images | https://www.hse.gov.uk/help/copyright.htm ; https://books.hse.gov.uk/copyright |
| HSE Romanian leaflets (CIS59, INDG410, migrant worker pages) | Welfare, working in UK | Free | HTML, PDF | OGL | **Yes**, but old (2007 to 2010) | https://www.hse.gov.uk/PUBNS/cis59r.htm ; https://www.hse.gov.uk/migrantworkers/languages/romanian/worker/ |
| HMRC CIS and VAT reverse charge guidance (VAT Notice 708, VATREVCON manual) | CIS, DRC VAT | Free | HTML | OGL v3.0 | **Yes** | https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services ; https://www.gov.uk/hmrc-internal-manuals/vat-reverse-charge-for-building-and-construction-services-manual ; https://www.gov.uk/guidance/buildings-and-construction-vat-notice-708 |
| gov.uk CIS and competent person scheme pages | CIS duties, self-certification | Free | HTML | OGL v3.0 | **Yes** | https://www.gov.uk/what-you-must-do-as-a-cis-contractor ; https://www.gov.uk/guidance/competent-person-scheme-current-schemes-and-how-schemes-are-authorised |
| Scottish Technical Handbooks (April 2026) | Scottish building standards | Free | HTML, PDF | Likely OGL (unverified) | Likely yes (unverified) | https://www.gov.scot/collections/building-standards/ |
| Wales Approved Documents, NI Technical Booklets | Devolved rules | Free | PDF | Assumed OGL/Crown (unverified) | Not checked | Not researched |
| NHBC Standards 2026 | Warranty technical standards | Free to read | HTML, PDF | All rights reserved. Internal or personal use only | **No**, link only | https://www.nhbc.co.uk/terms-of-use |
| LABC Warranty Technical Manual | Warranty standards | Free download behind form | PDF | Terms not found | **Assume no** | https://www.labcwarranty.co.uk/technical-manual-downloads |
| Premier Guarantee Technical Manual v17 | Warranty standards (from 1 Jan 2026) | Free download | PDF | Terms not found | **Assume no** | https://www.premierguarantee.com/en/technical-standards.html |
| RIBA Plan of Work 2020 | Stages 0 to 7 | Overview free | PDF | © RIBA, all rights reserved | **No**. Stage names can be paraphrased | https://riba.org/about-us/terms-of-use |
| British Standards (BSI) | Codes of practice, e.g. BS 7671 | Paid | PDF | BSI copyright; tailored licences | **No**, without a licence. Cite the number only | https://bsigroup.com/about-bsi/legal/intellectual-property-statement ; https://knowledge.bsigroup.com/pages/licensing |
| JCT 2024 contracts | Building contracts | Paid | Print, digital | Commercial copyright; AI terms not found | **No** | https://corporate.jctltd.co.uk/jct-2024-edition-available-contracts/ |
| NEC4 contracts | Engineering/building contracts | Paid | Print, digital | Licence needed to amend wording | **No** | https://www.neccontract.com/copyright |
| SSIP Core Criteria | What prequalification assesses | Free to read | HTML | Terms not checked | Summarise facts only | https://ssip.org.uk/ssip-core-criteria/ |
| SafeContractor, CHAS, Constructionline | Accreditation document lists | Free to read | HTML | Commercial (not checked) | Summarise facts only | https://www.safecontractor.com/contractor-accreditation/ssip/core-ssip-topics-covered |
| Planning Portal, CITB, FMB | Planning guides, training, contract templates | Mixed | HTML, PDF | Not checked | Not checked. Prefer GOV.UK and legislation for planning | https://www.planningportal.co.uk ; https://www.citb.co.uk ; https://www.fmb.org.uk |

## Current editions and changes to track

- Approved Document B (fire): updated 16 Sept 2026. What changed was not checked. [GOV.UK](https://www.gov.uk/government/collections/approved-documents)
- Approved Document T (toilets): added 3 Nov 2025. [GOV.UK](https://www.gov.uk/government/collections/approved-documents)
- The collection page "last updated" date did not match newer documents. Check each publication page. [GOV.UK](https://www.gov.uk/government/collections/approved-documents)
- Building Safety Regulator became a standalone body on 27 Jan 2026, with HSE support until Dec 2026. [Norton Rose Fulbright](https://connections.nortonrosefulbright.com/post/102m2l3/building-safety-regulator-key-changes-from-january-2026)
- Some Gateway 2 rules relaxed for rooftop telecoms work from 1 Sept 2026. Cladding remediation still needs full Gateway 2. [NFRC](https://www.nfrc.co.uk/resource/changes-to-the-building-safety-regime.html)
- Staged Gateway 2 applications now possible for phased higher-risk buildings. [Wedlake Bell](https://wedlakebell.com/insights/building-safety-act/staged-hrb-building-control-approvals-updated-guidance/)
- Scotland: April 2026 handbooks apply to warrants submitted on or after 6 April 2026. [gov.scot](https://www.gov.scot/collections/building-standards/)
- NHBC Standards 2026 apply to homes with foundations from 1 Jan 2026. [LexisNexis](https://www.lexisnexis.co.uk/legal/news/nhbc-publishes-updated-technical-standards-for-new-home-construction-in-2026)
- JCT 2016 withdrawn from sale 31 March 2025. [isurv](https://www.isurv.com/info/1190/jct_2024_and_2016_compared)
- VAT reverse charge started 1 March 2021 (planned for Oct 2020, so older material can be wrong). [Build UK](https://builduk.org/reverse-vat-a-practical-guide/?print=pdf)

## Legal background on RAG

- UK commercial text and data mining still needs a licence. The s29A exception is for non-commercial research only. In March 2026 the government said it will not widen it. [Faegre Drinker](https://www.faegredrinker.com/zh/insights/publications/2026/3/copyright-and-ai-in-the-uk-implications-for-rights-holders-and-developers), [DLA Piper](https://www.dlapiper.com/en/insights/blogs/mse-today/2026/tdm-and-training-ai-models)
- Getty v Stability AI (High Court, Nov 2025): model weights were not infringing copies. This helps training more than RAG, because RAG stores and returns real text. [Hamlins](https://hamlins.com/insight/high-court-delivers-landmark-judgment-on-generative-ai-and-copyright/)
- Each RAG step may count as reproduction in some EU laws. Untested. [IBA](https://www.ibanet.org/Copyrights-silent-frontier)
- No UK case or IPO guidance on RAG found.

## Design notes for ingestion

- Keep edition date, nation and effective date as chunk metadata. Transitional rules depend on dates.
- Chunk by regulation and by Approved Document section.
- Do not present answers as official guidance (OGL condition).
- Retrieve in English, answer in Romanian, always show the English clause and link (fits ADR 0001).
- For contracts, a later option is to hold the user's own licensed contract for their own use. Needs legal advice.
- SSIP and scheme document checklists: write our own words from public criteria.

## Not yet checked

- L153 current edition. Expected URL https://www.hse.gov.uk/pubns/books/l153.htm (not fetched).
- CIS 340 page (expected at gov.uk/government/publications/construction-industry-scheme-cis-340, not fetched).
- gov.scot licence statement. Wales and NI sources.
- LABC Warranty and Premier Guarantee terms. NHBC TRM end user licence. JCT terms. FMB template terms. Planning Portal terms.
- HSE translated leaflets index (hse.gov.uk/languages). CITB Romanian material.
