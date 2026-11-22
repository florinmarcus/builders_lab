# X: can free government MCP servers replace our own index? (22 Nov 2026)

**Question (Florin, 22 Nov):** do we need the government documents in our own index at all, when free MCP servers
from government and open source already search legislation and GOV.UK?

**Answer: yes, keep them.** No external server covers what the builders ask about most, and where one does
(legislation), it is no better than our own search and brings noise we filter out. One server, Lex, is worth
keeping as an optional second source for laws.

## What was run

- Script: `evals/external_mcp.py`. Tests: `tests/test_external_mcp.py` (9 offline, 6 live checks behind
  `BUILDERS_LIVE_MCP=1`; all pass on 22 Nov).
- Questions: the 299 golden dev questions. Holdout never sent. Each system gets only the questions whose expected
  sections it could hold: 185 with a law, 180 with a GOV.UK page.
- Servers, called live on 22 Nov:
  - **Lex** (i.AI, government, experimental): section search over Acts and SIs.
  - **uk-legal-mcp** (community): law search on legislation.gov.uk.
  - **govuk-mcp** (community): the official GOV.UK Search API.
- Two kinds of query:
  - **raw**: the builder's question as written.
  - **keyword**: one search query per question, written by Sonnet from the question only (no labels), the same for
    every system (`evals/external/keyword-queries.jsonl`). This is close to what our agents send.
- Our search: the full corpus in local Postgres (`corpus_next`). L1 = the live setup (hybrid + rerank) on raw
  questions. X1 = the same on the keyword queries (`evals/results/X1-keyword-hybrid-dev.jsonl`).
- **Like for like:** a law server returns 5 laws; our top 5 mixes laws and guidance. So for laws we keep only our
  legislation results, and for pages only our GOV.UK results ("same type" below).
- Numbers: `evals/external/summary.json`; raw replies: `evals/external/runs/`.

## Results (top 5)

| System | Right law | Right provision | Right GOV.UK page |
|---|---|---|---|
| Lex, keyword | 0.64 | 0.46 | none (laws only) |
| Lex, raw question | 0.35 | 0.26 | none |
| uk-legal, keyword | 0.15 | 0.00 (law level only) | none |
| uk-legal, raw question | 0.00 (long queries return nothing) | 0.00 | none |
| GOV.UK search, keyword | none | none | 0.41 |
| GOV.UK search, raw question | none | none | 0.03 |
| **Ours X1, keyword, same type** | **0.64** | **0.54** | **0.94** |
| Ours L1, raw question, same type | 0.50 | 0.40 | 0.89 |

Paired tests (McNemar, same questions):
- Laws: ours X1 and Lex tie, 118 of 185 each. Each finds 32 the other misses. Together they find 150 (0.81).
- Provisions: ours 100, Lex 85 (p = 0.07, not significant).
- GOV.UK pages: ours 169 of 180, GOV.UK search 74 (p < 0.001). And GOV.UK search returns titles and links only. The
  agent would still have to fetch and read the whole page.

Noise in Lex's top 5, on average:
- **1.5 results not for England**: mostly Northern Ireland copies of the same rules, for example the Control of
  Asbestos Regulations (Northern Ireland) 2012 next to the England ones.
- **3.7 results from laws outside our corpus**: these include revoked laws and orders that are not relevant.
- Our index has none of either: it holds only the in-force English versions we chose.

Speed and errors: all three servers answered every call (0 errors in 1,100 calls). Median replies took 0.3 to
0.6 s, and the slowest 5% took up to 1 s. Lex is rate-limited per IP (60 a minute) and labelled
"research and non-production use".

## What the external servers cannot do at all

What our dev questions need:

| Expected sources | Questions |
|---|---|
| A law plus a GOV.UK document (mostly Approved Documents) | 97 |
| A GOV.UK document only | 83 |
| A law plus HSE guidance | 61 |
| HSE guidance only | 31 |
| A law only | 27 |

- **Lex alone could fully serve at most 27 of 299 questions (9%).**
- **HSE guidance (92 questions) is on no server.** That covers the asbestos ACOP L143, HSG264, HSG150, the asbestos
  essentials sheets and CDM guidance.
- **Approved Documents and other GOV.UK PDFs:** GOV.UK search can at best point to the publication page. It cannot
  return the paragraph, table or diagram, and it has no dated versions.

## Recommendation

1. **Keep the government documents in our index.** We need them for the guidance, for passages rather than links,
   for England-only in-force versions, and for model-checked tables and figures.
2. **Lex as an optional second source for laws, later.** Together with our index it finds more laws (0.81 against
   0.64). It is experimental, though, and rate-limited per IP, and its results need an England and in-force filter.
   It is not for the demo. Revisit once retrieval is strong.
3. **Do not use uk-legal-mcp or GOV.UK search for retrieval.** They do worse than our index on every measure.
4. **A side finding for step 2:** keyword queries lift our own law hits from 0.50 to 0.64. This agrees with E3-E5:
   the agent's search query matters as much as the index.

## Limits

- Pages are scored at document level: any chunk of the right GOV.UK document counts. This favours our index a
  little, since GOV.UK search can only return documents.
- The Lex numbers count laws outside our corpus as misses, even when they might answer the question. I checked all
  688 such results in Lex's keyword top 5:
  - About 300 were Northern Ireland, Welsh or Scottish laws.
  - Most of the rest were old, revoked UK rules, for example the Asbestos (Licensing) Regulations 1983 and the
    Building Regulations 1965, or amending instruments.
- One run, on one day. The servers may change. The live tests check that they are still up and still find a
  known law and page.
