# AI regulation: EU AI Act and UK rules

Checked 18 Nov 2026. Not legal advice. Full report: `reports/EU AI Act and UK rules.md`. Source notes: `research_notes/EU AI Act and UK rules/`. "Interpretation" means our reading. "Unverified" means one secondary source or not re-read.

## Status: EU vs UK (as of 18 Nov 2026)

| Item | EU AI Act | UK |
|---|---|---|
| Is there an AI law? | Yes. Regulation (EU) 2024/1689, amended by the Digital Omnibus (Reg. 2026/1744, in force 27 Jul 2026) | No. Existing laws and regulators. No AI bill in Parliament (May 2026) |
| Banned AI practices | Since 2 Feb 2025. One new ban from 2 Dec 2026 | None specific |
| Staff AI literacy | Since 2 Feb 2025. Softened in Jul 2026 to "support" literacy | No duty |
| Rules for model makers (GPAI, e.g. Claude) | Since 2 Aug 2025 | None |
| Tell users it is AI; mark AI text | Since 2 Aug 2026 (Art 50). Grace to 2 Dec 2026 only for systems on the market before 2 Aug 2026 | No duty |
| High-risk rules | Delayed: 2 Dec 2027 (Annex III uses), 2 Aug 2028 (Annex I products) | None |
| Automated decisions about people | High-risk only if in Annex III | UK GDPR Arts 22A–22D, since 5 Feb 2026 |
| AI code of practice | Transparency code final 10 Jun 2026; high-risk guidelines draft, final due end 2026 | Statutory ICO AI code required since 12 May 2026, expected 2027 (unverified) |
| Health and safety | Not in the AI Act | HSE AI statement 12 Jun 2026: existing law applies; guidance due 2026/27 |
| Software product liability | New PLD: software is a product, transposition due 9 Dec 2026 (Romania not done as of Aug 2026) | Law Commission consultation to 14 Jan 2027. Proposal only |
| Regulator | ANCOM in Romania (named 12 Mar 2026; law pending, unverified) | ICO / Information Commission, HSE |
| Fines | Art 50: up to EUR 15m or 3%, lower of the two for SMEs | UK GDPR up to £17.5m or 4% (unverified) |

## What applies to us now (pilot, England)

- EU AI Act: very likely not, if users and outputs stay in the UK (interpretation). Edge case: AI text sent to someone in the EU.
- UK GDPR is the main law. Council = controller. Contractor = processor (usually). builders_lab = sub-processor. AWS = our sub-processor.
- The contractor may need the council's written consent before council data reaches us (interpretation, Art 28). This is the biggest risk.
- A DPIA is expected (AI is new technology; repairs emails can hold health data).
- About 30% of councils ask suppliers to declare AI use (LGA). Have a one-page AI-use statement ready.
- Asbestos (CAR 2012 reg 5) and CDM duties stay with the contractor. The tool can find what the survey says. It cannot be the assessment.
- We cannot exclude liability for death or injury from negligence (UCTA 1977 s2). We can cap other losses if reasonable.
- Golden thread (Building Safety Act) mostly does not apply: most council low-rise flats are under 18 m / 7 storeys.

## What applies if we serve firms in Romania

- We become a non-EU **provider** placing an AI system on the EU market. Firms are **deployers**. Anthropic is the model provider.
- Likely limited risk, not high-risk (interpretation).
- Art 50(1): tell users they are talking to an AI, at first use.
- Art 50(2): machine-readable marking of generated text. Exemptions may fit: plain translation, or closed B2B use with isolation and role-based access (from summaries only; read the guidelines).
- Art 4: support AI literacy of our staff; firms do the same for theirs.
- No EU representative needed (only for high-risk).
- EU product liability: software becomes a product once Romania transposes the PLD.
- Romanian asbestos rule (HG 1875/2005): risk assessment per task; stop work on unexpected asbestos.

## Design rules

1. AI notice at first use, in Romanian and English.
2. "AI-generated" footer plus a machine-readable marker on every summary, draft and export.
3. Cite document, page, date in every answer. For asbestos: survey type and rooms covered. Show the English source next to the Romanian answer.
4. Never say "no asbestos". If not covered or unclear: "Treat as containing asbestos until checked (reg 5)". Suspect material: "Stop work and get it checked".
5. Flag management-only surveys for refurbishment work, and old surveys.
6. No finished or signed RAMS or surveys. Drafts say "needs competent person review".
7. No decisions about tenants or workers: no ranking, scoring, monitoring.
8. Never drop tenant vulnerability or access notes from a summary.
9. AWS London, EU inference profile, no training on customer data, per-firm isolation.
10. Log questions, answers, sources, model version, user, time. Delete per property and at contract end.
11. One-page "use this tool safely" guide, Romanian and English.
12. Evals with negative tests: room not covered, old survey, conflicting documents.

## Open items

- Read the primary EU Art 50 guidelines and Code (B2B carve-out, translation exemption).
- Get 2–3 real council repairs DPAs or tender packs and quote their AI and sub-processor clauses.
- Check Romania: AI Act implementing law, PLD transposition, HG 1875/2005 amendment.
- Confirm on primary sources: ICO-to-Information Commission date (30 Sep 2026), King's Speech 13 May 2026, UK GDPR fine levels.
- Read CDM 2015 duties (SI 2015/51) and check for HSE's 2026/27 AI guidance.
- Ask a solicitor: negligent misstatement by an information tool; our liability terms.
- Ask an insurer about PI and product cover for an AI tool.
- Recheck high-risk classification when the final Commission guidelines come out (end 2026).
