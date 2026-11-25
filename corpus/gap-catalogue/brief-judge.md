# Brief: judge gap catalogue entries (v1)

You check catalogue entries for documents our library does not hold. Each entry was written only from a saved raw file. Your job: find anything in the entry that the raw file does not support.

Input: entries in `{IN}` (one JSON line each) and raw files in `{RAW}/<id>.md`.

For each entry, check:
1. supported: every point, the summary, the edition, the status notes and the topics are backed by the raw file. A topic is fine if it is a plain rewording of something the raw file says the document covers.
2. url: each point's url is a `## <url>` section in the raw file, and the fact is in that section.
3. coverage: the coverage value matches the raw file (contents / scope / partial / title_only / none).
4. copying: no passage longer than about 25 words copied word for word.
5. clauses: the entry does not state what a clause or requirement says (only what the document covers).

Use only the raw file. No outside knowledge, even if you think the raw file is wrong.

Reply with one JSON line per entry to `{OUT}`, nothing else:
{"id": "...", "verdict": "good|fix|bad", "unsupported": ["<each claim not in the raw file>"], "url_ok": true, "coverage_ok": true, "copying_ok": true, "clauses_ok": true, "reason": "<one plain sentence>"}

- good: all checks pass.
- fix: one small problem (a wrong url, a topic stretched a little, coverage one step off).
- bad: any invented fact, edition or status, or a clause stated.

Then reply with the counts of good, fix and bad.
