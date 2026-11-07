# UK construction methodology and rule sources for a RAG knowledge base, and their licence terms (as of Nov 2026)

Research date: 7 Nov 2026. Budget-limited pass (about 20 tool calls). Items marked "not verified" were not fetched in this pass and need checking before use.

## Summary table

| Source | Covers | Publisher | Format | Free / paid | Licence / reuse | Commercial AI ingestion allowed? | URL |
|---|---|---|---|---|---|---|---|
| Building Regulations 2010 (and other Acts/SIs) | Legal requirements for building work, England (and Wales pre-devolution) | The National Archives (legislation.gov.uk) | HTML, PDF, XML | Free | OGL v3.0, Crown and database right; EUR-Lex derived content under Commission Decision 2011/833/EU | Yes, with attribution (OGL permits commercial use and adaptation) | https://www.legislation.gov.uk/help#licence |
| Approved Documents A–T and 7 (England) | Statutory guidance on meeting the Building Regulations | MHCLG on GOV.UK | PDF (plus merged searchable PDF) | Free | OGL v3.0 except where stated; Crown copyright | Yes, with attribution; watch third-party material (e.g. referenced BS extracts) | https://www.gov.uk/government/collections/approved-documents |
| HSE guidance (L153 CDM 2015 guidance, CIS leaflets, INDG) | CDM 2015 duties, construction H&S | Health and Safety Executive | HTML, PDF; printed books via HSE Books | Most free online; printed books paid | OGL for website Crown material and printed products, except Law Poster suite, Accident Book, some multimedia, photos/film | Yes for text, with HSE attribution; exclude posters, photos, Accident Book | https://www.hse.gov.uk/help/copyright.htm ; https://books.hse.gov.uk/copyright |
| HSE translated leaflets (Romanian) | e.g. CIS59 welfare facilities, INDG410, migrant worker pages | HSE | HTML, PDF | Free | OGL (as HSE material) | Yes, with attribution; translations are old | https://www.hse.gov.uk/pubns/cis59r.htm ; https://www.hse.gov.uk/migrantworkers/languages/romanian/worker/ |
| HMRC CIS and VAT domestic reverse charge guidance | CIS 340, reverse charge rules, VAT Notice 708, VATREVCON manual | HMRC on GOV.UK | HTML | Free | OGL v3.0 (GOV.UK standard) | Yes, with attribution | https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services ; https://www.gov.uk/hmrc-internal-manuals/vat-reverse-charge-for-building-and-construction-services-manual |
| Scottish Technical Handbooks (domestic / non-domestic) | Scottish building standards | Scottish Government | HTML, PDF | Free | Likely OGL (gov.scot) – not verified | Likely yes – not verified | https://www.gov.scot/collections/building-standards/ |
| NHBC Standards 2026 | Technical requirements for NHBC-warranted new homes | NHBC | HTML (nhbc-standards.co.uk), PDF | Free to read | All rights reserved; download only for internal/personal use; no commercial use without licence | No, without a licence from NHBC | https://www.nhbc.co.uk/terms-of-use |
| LABC Warranty Technical Manual | Warranty technical standards | LABC Warranty | PDF (download behind form) | Free download | Terms not found | Unknown; assume no without permission | https://www.labcwarranty.co.uk/technical-manual-downloads |
| Premier Guarantee Technical Manual v17 | Warranty technical standards (homes quoted from 1 Jan 2026) | Premier Guarantee | PDF | Free download | Terms not found | Unknown; assume no without permission | https://www.premierguarantee.com/en/technical-standards.html |
| RIBA Plan of Work 2020 | Project stages 0–7 | RIBA | PDF | Overview free to download | © RIBA 2020, all rights reserved; no reproduction without permission | No, without written permission | https://www.architecture.com/-/media/GatherContent/Test-resources-page/Additional-Documents/2020RIBAPlanofWorkoverviewpdf ; https://riba.org/about-us/terms-of-use |
| British Standards (BSI) | Codes of practice and product standards | BSI | PDF via BSI Knowledge | Paid | Copyright owned by BSI; commercial use needs a licence; licences tailored per customer | No, without a negotiated licence | https://bsigroup.com/about-bsi/legal/intellectual-property-statement ; https://knowledge.bsigroup.com/pages/licensing |
| JCT 2024 contracts | Standard building contracts | JCT | Print, digital | Paid | Commercial copyright (JCT); AI terms not found | No, assume not | https://corporate.jctltd.co.uk/jct-2024-edition-available-contracts/ |
| NEC4 contracts | Standard engineering/building contracts | NEC (Thomas Telford) | Print, digital | Paid | Copyright; licence needed to amend wording; digital licences allow search/view/copy/print by authorised users | No, assume not | https://www.neccontract.com/copyright |
| SSIP Core Criteria | What prequalification schemes assess (policy, risk assessments, method statements, competence) | SSIP | HTML | Free to read | Terms not checked | Facts (criteria list) can be summarised; check terms before copying text | https://ssip.org.uk/ssip-core-criteria/ |
| SafeContractor / CHAS / Constructionline guidance | Document lists for accreditation | Private scheme operators | HTML | Free to read | Commercial copyright (not checked) | Summarise facts only | https://www.safecontractor.com/contractor-accreditation/ssip/core-ssip-topics-covered |
| Planning Portal, CITB, FMB | Planning/PD guidance; training; contract templates | Planning Portal (TerraQuest JV), CITB, FMB | HTML, PDF | Mixed | Not verified in this pass | Not verified | https://www.planningportal.co.uk ; https://www.citb.co.uk ; https://www.fmb.org.uk |

## Building Regulations, Approved Documents and the post-Grenfell regime (England; other nations)

### Takeaway
Legislation and Approved Documents are Crown copyright under OGL v3.0, so they are the safest core of a commercial RAG corpus (attribution required; no implied endorsement). The Approved Documents set now runs A to T plus Regulation 7, with Approved Document B updated in Sept 2026 and T added in Nov 2025. Scotland uses its own Technical Handbooks (April 2026 editions current).

### Cited Findings
- legislation.gov.uk: "All content is available under the Open Government Licence v3.0 except where otherwise stated"; marked "© Crown and database right"; EUR-Lex derived content reused under Commission Decision 2011/833/EU — [legislation.gov.uk help](https://www.legislation.gov.uk/help#licence)
- OGL v3.0 allows copying, publishing, adapting and commercial exploitation, including "in your own product or application"; conditions: attribution (default text "Contains public sector information licensed under the Open Government Licence v3.0"), no implied official status/endorsement; rights end automatically on breach; exempts personal data, logos/crests, third-party rights, other IP such as trade marks — [OGL v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
- GOV.UK Approved Documents collection lists A (Structure, 2013), B (Fire safety, 16 Sept 2026), C, D, E, F (2022), G (Oct 2024), H, J, K, L (Feb 2023), M (Oct 2024), O (2022), P, Q (Nov 2024), R (2022), S (Apr 2023), T (Toilet accommodation, 3 Nov 2025), Regulation 7 (2018); also a merged searchable Approved Documents PDF (1 Oct 2024) and the Manual to the Building Regulations (2020). Page licence: OGL v3.0 except where stated, Crown copyright — [GOV.UK Approved Documents](https://www.gov.uk/government/collections/approved-documents)
- Note: the collection page's "last updated" metadata (May 2024) did not match the newer document dates; check each publication page — [GOV.UK Approved Documents](https://www.gov.uk/government/collections/approved-documents)
- Building Safety Regulator became a standalone executive non-departmental public body on 27 Jan 2026, with HSE support until Dec 2026 — [International Fire & Safety Journal](https://internationalfireandsafetyjournal.com/bsr-gateway-2-update/); [Norton Rose Fulbright](https://connections.nortonrosefulbright.com/post/102m2l3/building-safety-regulator-key-changes-from-january-2026)
- BSR said in March 2026 it had almost cleared its backlog of legacy Gateway 2 applications for higher-risk buildings — [Freeths](https://www.freeths.co.uk/insights-events/legal-articles/2026/gateway-2-in-2026-is-the-regime-future-proof/)
- Staged Gateway 2 applications are now possible for new HRBs (over 7 storeys or 18 m) delivered in phases — [Wedlake Bell](https://wedlakebell.com/insights/building-safety-act/staged-hrb-building-control-approvals-updated-guidance/)
- Consultation on Category A/B works to existing HRBs closed 28 May 2026; July 2026 government response: some rooftop telecoms mast work relieved of certain Gateway 2 requirements from 1 Sept 2026, major cladding remediation still needs full Gateway 2 — [NFRC](https://www.nfrc.co.uk/resource/changes-to-the-building-safety-regime.html); [JD Supra](https://www.jdsupra.com/legalnews/improving-the-building-control-process-8418937/)
- Scotland: April 2026 domestic and non-domestic Technical Handbooks apply to building warrant applications submitted on or after 6 April 2026; edition is set by warrant submission date — [gov.scot building standards collection](https://www.gov.scot/collections/building-standards/); [gov.scot Jan 2025 domestic handbook](https://gov.scot/publications/building-standards-technical-handbook-january-2025-domestic)
- Scottish Government blog (Jan 2026) on future changes to the handbooks — [Building Standards blog](https://blogs.gov.scot/building-standards/2026/01/14/future-changes-to-the-domestic-and-non-domestic-technical-handbooks/)

### Inferences
- Legislation + Approved Documents + Manual to the Building Regulations make a clean OGL core. Chunk by regulation / AD section and keep edition dates as metadata, since transitional rules depend on dates (as in Scotland, warrant date).
- Approved Documents cite British Standards; the AD text is OGL but the cited BS content is not, so the assistant should cite the BS number without reproducing it.
- An AI product should avoid presenting itself as official guidance (OGL non-endorsement clause).

### Gaps
- Content of the 16 Sept 2026 Approved Document B change (what changed, effective date) not checked.
- Wales (own Approved Documents since 2012 devolution of building regs) and Northern Ireland (Building Regulations (NI) and Technical Booklets, DFP) not researched in this pass; licence assumed OGL/Crown but not verified.
- gov.scot licence statement not fetched (normally OGL).

## CDM 2015 and HSE guidance

### Takeaway
HSE web text and printed products are reusable under OGL with attribution, with named exclusions (Law Poster suite, Accident Book, some multimedia, photos/film). So L153 (CDM 2015 guidance), CIS leaflets and INDG leaflets can go into a commercial RAG corpus.

### Cited Findings
- HSE: "You may re-use the Crown material featured on this website free of charge in any format or medium, under the terms of the Open Government Licence"; 'Health and Safety Law: what you need to know' posters excluded; preferred acknowledgement "Contains public sector information published by the Health and Safety Executive and licensed under the Open Government Licence" — [HSE copyright](https://www.hse.gov.uk/help/copyright.htm)
- HSE Books: printed products are Crown copyright unless marked otherwise and reusable under OGL; Law Poster and Accident Book cannot be licensed for third-party reuse — [HSE Books copyright](https://books.hse.gov.uk/copyright)
- Photos, film and similar are outside OGL; fees apply (e.g. £50 + VAT for up to two photographs) — [HSL Crown copyright material](https://hsl.gov.uk/internal/licensing-information/crown-copyright-material)

### Inferences
- Ingest text only; strip images from HSE PDFs to stay inside OGL.
- L153 is at https://www.hse.gov.uk/pubns/books/l153.htm (URL from general knowledge, not fetched this pass).

### Gaps
- Did not verify the current L153 edition or whether HSE has revised CDM guidance after the BSR split.

## Planning Portal, permitted development, legislation.gov.uk

### Takeaway
Permitted development rules themselves (GPDO 2015 and amendments) are on legislation.gov.uk under OGL. Planning Portal's own guidance pages were not checked.

### Cited Findings
- legislation.gov.uk content (including the GPDO) is OGL v3.0 — [legislation.gov.uk help](https://www.legislation.gov.uk/help#licence)

### Inferences
- Planning Portal is operated as a joint venture with a private company (general knowledge), so its interactive guides may be commercial copyright, unlike GOV.UK. Prefer GOV.UK technical guidance on PD rights plus legislation.

### Gaps
- Planning Portal terms of use not fetched. Not verified.

## Warranty standards: NHBC, LABC Warranty, Premier Guarantee

### Takeaway
All three publish their technical manuals free to read or download, but this is not an open licence. NHBC terms explicitly forbid commercial use without a licence. Treat all three as "read, link and summarise, do not ingest" unless licensed.

### Cited Findings
- NHBC Standards 2026 apply to NHBC-registered homes with foundations started on or after 1 Jan 2026; NHBC says only 1.2% of clauses are new positions — [HBD Online](https://hbdonline.co.uk/?p=372896); [LexisNexis](https://www.lexisnexis.co.uk/legal/news/nhbc-publishes-updated-technical-standards-for-new-home-construction-in-2026)
- NHBC terms of use: NHBC owns or licenses the IP and all rights are reserved; downloads of extracts allowed "for your internal purposes and/or personal use"; "You must not use any part of the materials on our website for commercial purposes" without a licence; no framing — [NHBC terms of use](https://www.nhbc.co.uk/terms-of-use)
- Premier Guarantee Technical Manual v17 is effective for homes quoted on or after 1 Jan 2026, free to download in full or by section — [Premier Guarantee technical standards](https://www.premierguarantee.com/en/technical-standards.html)
- LABC Warranty Technical Manual is downloadable (full or by chapter) from its site — [LABC Warranty downloads](https://www.labcwarranty.co.uk/technical-manual-downloads); [LABC Warranty download form](https://info.labcwarranty.co.uk/technical-manual-download)

### Inferences
- For a builder-facing assistant, NHBC content can be pointed to (link to the clause) but not stored, unless NHBC grants a licence.

### Gaps
- LABC Warranty and Premier Guarantee copyright/terms text not found. The latest LABC Warranty manual version number was unclear (download page showed v12 dated 2023–24).
- NHBC "TRM end user licence" PDF not read.

## RIBA Plan of Work, British Standards, JCT, NEC, FMB

### Takeaway
All are commercial copyright. Ingesting the text into a commercial AI product needs a licence. Stage names and short factual descriptions can be paraphrased.

### Cited Findings
- RIBA Plan of Work 2020 Overview: © RIBA 2020, all rights reserved, no reproduction without prior permission — [RIBA Plan of Work 2020 overview PDF](https://www.architecture.com/-/media/GatherContent/Test-resources-page/Additional-Documents/2020RIBAPlanofWorkoverviewpdf)
- RIBA website terms: users may not "reproduce, modify, copy or distribute" site content without written permission — [RIBA terms of use](https://riba.org/about-us/terms-of-use)
- BSI: copyright in all British Standards, in any format, is owned by BSI; commercial use of site materials needs a licence — [BSI IP statement](https://bsigroup.com/about-bsi/legal/intellectual-property-statement)
- BSI licences set how standards content may be used and distributed (e.g. internal documents, software products) and are tailored per customer; no public AI-specific term found — [BSI Knowledge licensing](https://knowledge.bsigroup.com/pages/licensing)
- JCT 2024 Edition is current; released in batches April 2024 to June 2025; JCT 2016 withdrawn from sale 31 March 2025 — [JCT 2024 available contracts](https://corporate.jctltd.co.uk/jct-2024-edition-available-contracts/); [isurv](https://www.isurv.com/info/1190/jct_2024_and_2016_compared)
- NEC: a copyright licence should be taken to amend the wording of standard NEC documents — [NEC copyright policy](https://www.neccontract.com/copyright)

### Inferences
- For contracts, a RAG system could hold the user's own signed contract (customer's licensed copy, for their own use) rather than a central copy; that shifts the licence question to the customer, but still needs legal advice.

### Gaps
- JCT terms of use / AI policy not found. FMB contract template terms not checked.

## Prequalification schemes: SSIP, CHAS, SafeContractor, Constructionline

### Takeaway
SSIP Core Criteria are public and common to all member schemes: H&S policy, organisation, risk assessments and method statements (RAMS), training/competence, accident reporting, plus extra criteria for designers, principal designers and principal contractors. Insurance (notably employers' liability) is commonly requested.

### Cited Findings
- SSIP Core Criteria are the H&S standards all SSIP member schemes assess against, starting with a suitable H&S policy and organisation — [SSIP Core Criteria](https://ssip.org.uk/ssip-core-criteria/)
- SafeContractor lists core SSIP topics, including hazard identification, risk assessments and safe systems of work (method statements) — [SafeContractor SSIP core criteria](https://www.safecontractor.com/contractor-accreditation/ssip/core-ssip-topics-covered); [SafeContractor documents blog](https://www.safecontractor.com/en-gb/insights/blog/what-documents-do-i-need-to-gain-ssip-accreditation/)
- Typical evidence: H&S policy, risk assessments, training records, insurance certificates, accident records; policy reviewed at least yearly — [Croner](https://croner.co.uk/resources/managing-health-safety/how-to-pass-an-ssip-in-2026); [SSIP blog](https://ssip.org.uk/?p=8200)
- CHAS commentary on Common Assessment Standard and SSIP — [CHAS blog](https://www.chas.co.uk/blog/why-uk-contractors-struggle-with-common-assessment-standard-and-ssip-compliance/)

### Inferences
- A good product use case: checklist of documents per scheme, built from paraphrased public criteria, not copied text.

### Gaps
- Exact count of criteria (reported as 15 + 3) comes from secondary sources; confirm on ssip.org.uk. Build UK Common Assessment Standard question set and licence not checked. Scheme site terms not checked.

## CIS and VAT domestic reverse charge (HMRC)

### Takeaway
All HMRC guidance on GOV.UK (CIS 340, reverse charge guidance, VATREVCON manual, VAT Notice 708) is OGL and safe to ingest with attribution.

### Cited Findings
- GOV.UK guidance on VAT domestic reverse charge refers to CIS 340 for contractor/subcontractor status — [GOV.UK reverse charge guidance](https://www.gov.uk/guidance/vat-domestic-reverse-charge-for-building-and-construction-services); [technical guide](https://www.gov.uk/guidance/vat-reverse-charge-technical-guide)
- Reverse charge applies when supplier and customer are UK VAT registered and the service is a construction service — [GOV.UK suppliers guide](https://gov.uk/guidance/how-to-use-the-vat-reverse-charge-if-you-supply-building-and-construction-services); [buyers guide](https://www.gov.uk/guidance/how-to-use-the-vat-reverse-charge-if-you-buy-building-and-construction-services)
- HMRC internal manual VATREVCON and VAT Notice 708 — [VATREVCON manual](https://www.gov.uk/hmrc-internal-manuals/vat-reverse-charge-for-building-and-construction-services-manual); [VAT Notice 708](https://www.gov.uk/guidance/buildings-and-construction-vat-notice-708)
- GOV.UK content licence is OGL v3.0 (stated on GOV.UK pages, e.g.) — [GOV.UK Approved Documents page footer](https://www.gov.uk/government/collections/approved-documents)
- Reverse charge start date was 1 March 2021 (earlier planned 1 Oct 2020, so older material may be wrong) — [Build UK guide](https://builduk.org/reverse-vat-a-practical-guide/?print=pdf)

### Gaps
- CIS 340 page URL not fetched in this pass (expected at gov.uk/government/publications/construction-industry-scheme-cis-340).

## Romanian-language UK construction guidance

### Takeaway
HSE has a small, dated set of Romanian materials (CIS59 welfare facilities, INDG410, a Romanian migrant worker section). They are OGL. No CITB Romanian materials found.

### Cited Findings
- HSE CIS59 in Romanian: "Provision of welfare facilities during construction work" (Romanian PDF listed as 2010; page updated 2021; English updated Oct 2024, so the translation is out of date) — [HSE CIS59 Romanian](https://www.hse.gov.uk/PUBNS/cis59r.htm); [English CIS59](https://hse.gov.uk/pubns/cis59.htm)
- INDG410 "Working in the UK from overseas?" in Romanian (2007; agriculture/food focus) — [HSE INDG410 Romanian](https://www.hse.gov.uk/PUBNS/indg410ro.htm)
- HSE migrant worker pages in Romanian — [HSE Romanian worker pages](https://www.hse.gov.uk/migrantworkers/languages/romanian/worker/)
- HSE/TUC worker guide published in many languages (2004); later list of 21 languages includes Romanian — [FMLink](https://www.fmlink.com/?p=18949)

### Inferences
- For Romanian-speaking builders, a better path is to ingest English OGL sources and translate at answer time, citing the English source; the Romanian HSE set is too old to be primary.

### Gaps
- No CITB Romanian content found (not searched in depth). HSE translated leaflets index (hse.gov.uk/languages) not fetched.

## Legal / IP view on using copyrighted standards for RAG

### Takeaway
No UK court has ruled on RAG. UK commercial text and data mining still needs a licence (the s29A exception is non-commercial research only, and the government said in March 2026 it will not widen it). Storing full copyrighted text in a vector store and returning passages is reproduction risk; OGL sources avoid this. Safe pattern: ingest OGL text fully; for copyrighted standards store only metadata, clause references and own-words summaries, or get a licence.

### Cited Findings
- UK government confirmed in March 2026 it will not introduce a broader opt-out exception for commercial AI training; commercial TDM still needs a licence — [Faegre Drinker, Mar 2026](https://www.faegredrinker.com/zh/insights/publications/2026/3/copyright-and-ai-in-the-uk-implications-for-rights-holders-and-developers); [DLA Piper, Jan 2026](https://www.dlapiper.com/en/insights/blogs/mse-today/2026/tdm-and-training-ai-models)
- s29A CDPA 1988 TDM exception covers only non-commercial research with lawful access — [DLA Piper](https://www.dlapiper.com/en/insights/blogs/mse-today/2026/tdm-and-training-ai-models)
- Getty v Stability AI (High Court, Nov 2025): model weights were not "infringing articles"; ruling separates training from reproducing material in an infringing form — [Hamlins](https://hamlins.com/insight/high-court-delivers-landmark-judgment-on-generative-ai-and-copyright/); [Council of Europe Merlin](https://merlin.obs.coe.int/article/10426)
- Each step of RAG (retrieval, temporary storage, processing) may be an act of reproduction under some EU laws; untested — [IBA](https://www.ibanet.org/Copyrights-silent-frontier)
- Practitioner views differ on whether embeddings are infringing copies — [Veridian Software](https://veridiansoftware.com/knowledge-base/do-retrieval-augmented-generation-rag-models-risk-breaking-copyright) (vendor, low authority)

### Inferences
- Getty helps model training more than RAG: RAG keeps and outputs the actual text, which is closer to reproduction.
- Facts and ideas (e.g. "a stair needs a handrail") are not copyright; expression is. Own-words summaries with clause references are lower risk than stored text, but summarising a whole paid standard clause by clause could still be challenged. Get legal advice before launch.

### Gaps
- No UK case law or IPO guidance specific to RAG found. Not legal advice.
