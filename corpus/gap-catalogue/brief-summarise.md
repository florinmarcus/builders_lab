# Brief: summarise gap documents (v1)

You write catalogue entries for documents that our regulations library does NOT hold. The aim is that a later search step can say "that is in BS 9251, which we do not hold; it covers X". You never say what a clause says.

Input: a batch file `{BATCH}` (JSON list of entries with id, title, publisher, url, licence, why, notes) and, for each id, the saved page text in `{RAW}/<id>.md`. Each raw file has `## <url>` sections and a `## not reached` section. Some lines are marked [paraphrase] or say they are the fetch tool's wording: treat those as weaker than quoted or copied text.

Hard rules:
- Use ONLY the raw file. No memory, no web, no guessing. If the raw file does not say it, leave it out.
- Every point names the url of the section it came from.
- Do not copy long passages. Short phrases in your own plain words, at most one short quote per entry.
- If the raw file says a page looked wrong or unreliable, do not use that page; set coverage to "title_only".
- If nothing was reached, write the entry with coverage "none" and an empty summary.

For each id, write one JSON line to `{OUT}`:
{"id": "...", "title": "<as in the batch file>", "coverage": "contents|scope|partial|title_only|none", "parts_seen": "<e.g. 'parts 1, 4 and 7' or ''>", "current_edition": "<edition and status as the page states, or ''>", "status_notes": "<withdrawn, replaced by, under review, new edition coming, as the page states, or ''>", "summary": "<at most 60 words: what the document covers and who it is for>", "topics": ["<3 to 8 short plain search phrases a builder might use>"], "points": [{"text": "<one fact>", "url": "<section url>"}]}

Coverage values:
- contents: the raw file holds a contents list or clause headings.
- scope: it holds a scope or "what it covers" statement but no contents.
- partial: only some parts or sections of a series or document were reached (fill parts_seen).
- title_only: only the title is usable.
- none: nothing reached.

Topics must come from the raw text too; plain words a builder would type, no section numbers.

Write valid JSON, one line per id, every id in the batch. Then reply with one line per id: id, coverage.
