# Corpus coverage

Made by `python -m system.rag.coverage` (corpus/OVERNIGHT-PLAN.md, S1). In scope: sources with mode `ingest` that are fetched. Restricted and link-only sources are out of scope tonight.

- Sources in scope: 193.
- By status: to parse 175, chunked 12, raw missing 6.
- By parser (assigned, else the one that fits): parse_html 65, parse_pdf 53, parse_legislation 52, parse_adoc 23.

| id | priority | kind | parts | raw | file types | parser assigned | fits | trees | open checks | chunk files | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ad7 | 1 | approved-document | 2 | 2/2 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| ada | 1 | approved-document | 2 | 2/2 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adb | 1 | approved-document | 8 | 8/8 | pdf | parse_adoc | parse_adoc | 1 | 0 | 1 | chunked |
| adc | 1 | approved-document | 2 | 2/2 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adf | 1 | approved-document | 2 | 2/2 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adg | 1 | approved-document | 4 | 4/4 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adj | 1 | approved-document | 1 | 1/1 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adl | 1 | approved-document | 3 | 3/3 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adp | 1 | approved-document | 1 | 1/1 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| awaab-guidance-phase1 | 1 | guidance | 1 | 1/1 | html | parse_html | parse_html | 1 | 0 | 1 | chunked |
| awaab-guidance-phase2 | 1 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| awaab-triage-phase2 | 1 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| br-approval | 1 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| bsr-dutyholder | 1 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| cps-schemes | 1 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| damp-mould-health | 1 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| ess-guidance | 1 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| fser-fire-doors | 1 | guidance | 2 | 2/2 | html | parse_html | parse_html | 2 | 0 | 2 | chunked |
| govuk-cis-contractor | 1 | tax-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| govuk-cis-subcontractor | 1 | tax-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hmrc-cis-340 | 1 | tax-guidance | 1 | 1/1 | html | parse_html | parse_html | 1 | 0 | 1 | chunked |
| hmrc-cis-fraud-2026 | 1 | tax-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hmrc-cis-simplify-2026 | 1 | tax-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hmrc-vatrevcon | 1 | tax-guidance | 48 | 48/48 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-asbestos-duty | 1 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-asbestos-essentials | 1 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-asbestos-licensing | 1 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-asbestos-locations | 1 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-asbestos-training | 1 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-asbestos-workers | 1 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-nnlw | 1 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| vat-drc-guide | 1 | tax-guidance | 1 | 1/1 | html | parse_html | parse_html | 1 | 0 | 1 | chunked |
| vat-notice-708 | 1 | tax-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| awaab-amd-2026 | 1 | legislation | 1 | 1/1 | xml | parse_legislation | parse_legislation | 0 | 0 | 0 | to parse |
| awaab-regs-2025 | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| br-amd-2023-dutyholders | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| br2010 | 1 | legislation | 1 | 1/1 | xml | parse_legislation | parse_legislation | 4 | 0 | 4 | chunked |
| car-amd-2026 | 1 | legislation | 1 | 1/1 | xml | parse_legislation | parse_legislation | 0 | 0 | 0 | to parse |
| car2012 | 1 | legislation | 1 | 1/1 | xml | parse_legislation | parse_legislation | 1 | 0 | 1 | chunked |
| cdm2015 | 1 | legislation | 1 | 1/1 | xml | parse_legislation | parse_legislation | 1 | 0 | 1 | chunked |
| cis-amd-2026 | 1 | legislation | 1 | 1/1 | xml | parse_legislation | parse_legislation | 0 | 0 | 0 | to parse |
| cis-regs-2005 | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| ess2020 | 1 | legislation | 1 | 0/1 | xml |  | parse_legislation | 0 | 0 | 0 | raw missing |
| fa2004-cis | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| fso2005 | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| gsiur1998 | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| hgcra1996-p2 | 1 | legislation | 1 | 1/1 | xml | parse_legislation | parse_legislation | 1 | 0 | 1 | chunked |
| hhsrs-amd-2026 | 1 | legislation | 1 | 1/1 | xml | parse_legislation | parse_legislation | 0 | 0 | 0 | to parse |
| hhsrs-regs-2005 | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| housing-act-2004-p1 | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| scheme-cc-1998 | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| scoar2015 | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| vat-s55a-order-2019 | 1 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| awaab-consolidated | 1 | guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| decent-home-2006 | 1 | guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-asbestos-a0 | 1 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-asbestos-em1 | 1 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-cis80 | 1 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-hsg227 | 1 | hse-guidance | 1 | 1/1 | pdf | parse_pdf | parse_pdf | 1 | 0 | 1 | chunked |
| hse-hsg248 | 1 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-hsg264 | 1 | hse-guidance | 1 | 1/1 | pdf | parse_pdf | parse_pdf | 1 | 0 | 1 | chunked |
| hse-l143 | 1 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-l153 | 1 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-l56 | 1 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| adb-amendments | 2 | approved-document | 8 | 8/8 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| ade | 2 | approved-document | 2 | 2/2 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adf-2026 | 2 | approved-document | 1 | 1/1 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adh | 2 | approved-document | 1 | 1/1 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adk | 2 | approved-document | 1 | 1/1 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adl-2026 | 2 | approved-document | 2 | 2/2 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adm | 2 | approved-document | 6 | 6/6 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adb-faq | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| below-threshold-guidance | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| bsr-hrb-approval | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| circ-01-2024 | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| circ-01-2026 | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| decent-homes-new | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hhsrs-landlords | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hrb-existing | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-cdm-domestic-clients | 2 | hse-guidance | 1 | 1/1 | html | parse_html | parse_html | 1 | 0 | 1 | chunked |
| hse-cdm-pages | 2 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-cis-index | 2 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-cis36 | 2 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-cis69 | 2 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-eh40 | 2 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-gas-landlords | 2 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-hsg210 | 2 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-indg463 | 2 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-ms34 | 2 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-romanian | 2 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| party-wall-booklet | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| ppn-023-2026 | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| procurement-supplier-guide | 2 | guidance | 5 | 5/5 | html |  | parse_html | 0 | 0 | 0 | to parse |
| reserving-below-threshold | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| scoar-guidance | 2 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| ba1984 | 2 | legislation | 1 | 0/1 | xml |  | parse_legislation | 0 | 0 | 0 | raw missing |
| br-amd-2026-fhs | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| bsa2022 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| coshh2002 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| eawr1989 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| ess-amd-2026 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| ess-social-2025 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| fser2022 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| gpdo-2015 | 2 | legislation | 1 | 0/1 | xml |  | parse_legislation | 0 | 0 | 0 | raw missing |
| hfhh-act-2018 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| hrb-descriptions-2023 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| hrb-procedures-2023 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| hswa1974 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| lta1985-s11 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| mhswr1999 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| party-wall-act-1996 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| procurement-act-2023 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| riddor2013 | 2 | legislation | 1 | 0/1 | xml |  | parse_legislation | 0 | 0 | 0 | raw missing |
| scoar-amd-2022 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| wah2005 | 2 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| awaab-tenants | 2 | guidance | 7 | 7/7 | html, pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| bc-changes-2023 | 2 | guidance | 4 | 4/4 | html, pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| br-circulars | 2 | guidance | 153 | 153/153 | html, pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| circ-adb-2024 | 2 | guidance | 4 | 4/4 | html, pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| fser-page | 2 | guidance | 10 | 10/10 | html, pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| fso-guidance-collection | 2 | guidance | 62 | 62/62 | html, pdf, vnd.oasis.opendocument.spreadsheet, vnd.oasis.opendocument.text |  | parse_pdf | 0 | 0 | 0 | to parse |
| fso-s156 | 2 | guidance | 2 | 2/2 | html, pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hhsrs-operating | 2 | guidance | 3 | 3/3 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-cis54 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-cis62 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-cis63 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-cis65 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-cis78 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-cis79 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-hsg141 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-hsg247 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-hsg33 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-hsg85 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-hsr25 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-indg136 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-indg285 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-indg344 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-indg344-ro | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-indg401 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-indg411 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-indg453 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-l5 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-ro-indg410 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-ro-indg450 | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-ro-watch-your-step | 2 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| pd-householder-guide | 2 | guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| rsh-safety-quality | 2 | guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| adb-historical | 3 | approved-document | 17 | 17/17 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| add | 3 | approved-document | 1 | 1/1 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| ado | 3 | approved-document | 1 | 1/1 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adq | 3 | approved-document | 1 | 1/1 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adr | 3 | approved-document | 2 | 2/2 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| ads | 3 | approved-document | 1 | 1/1 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| adt | 3 | approved-document | 1 | 1/1 | pdf |  | parse_adoc | 0 | 0 | 0 | to parse |
| bsa-secondary | 3 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| fire-flats-residents | 3 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hfhh-guides | 3 | guidance | 3 | 3/3 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hmrc-cis-consult-2026 | 3 | tax-guidance | 2 | 2/2 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-asbestos-information | 3 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-asbestos-pubns-index | 3 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-gas-domestic | 3 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-hsg47 | 3 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-indg231 | 3 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-indg236 | 3 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-l74 | 3 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-ro-cis59 | 3 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-ro-migrant-workers | 3 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| hse-wood-dust | 3 | hse-guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| party-wall-guidance | 3 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| payments-compliance-notices | 3 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| sme-hub | 3 | guidance | 1 | 1/1 | html |  | parse_html | 0 | 0 | 0 | to parse |
| bamd2018 | 3 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| br-charges-2026 | 3 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| fsa2021 | 3 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| hrb-management-2023 | 3 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| lg-exclusion-order-2026 | 3 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| noise2005 | 3 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| procurement-regs-2024 | 3 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| procurement-thresholds-2025 | 3 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| rbca-2024 | 3 | legislation | 1 | 0/1 | xml |  | parse_legislation | 0 | 0 | 0 | raw missing |
| rra2025 | 3 | legislation | 1 | 0/1 | xml |  | parse_legislation | 0 | 0 | 0 | raw missing |
| shra2023 | 3 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| vibration2005 | 3 | legislation | 1 | 1/1 | xml |  | parse_legislation | 0 | 0 | 0 | to parse |
| awaab-collection | 3 | guidance | 28 | 28/28 | html, pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hhsrs-enforcement | 3 | guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-hsg150 | 3 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-l108 | 3 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-l140 | 3 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| hse-ro-cis26 | 3 | hse-guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| manual-br | 3 | guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| rsh-code-of-practice | 3 | guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| rsh-competence-conduct | 3 | guidance | 1 | 1/1 | pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
| supplier-information | 3 | guidance | 49 | 49/49 | html, pdf |  | parse_pdf | 0 | 0 | 0 | to parse |
