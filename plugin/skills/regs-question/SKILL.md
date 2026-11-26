---
name: regs-question
description: Use for Marcus Limited (the building firm) building questions about building regulations, building control, structure, fire, asbestos rules, CDM or payment law in England, answered only from the BuildersRegulations connector (regulations library) (no web search).
---

# Building regulations question

Read `../../shared/rules.md` first.

1. Plan and run the search with the `regs-search-plan` skill: one to three short English searches, run together. Add `as_of_date` if they ask about a past date.
2. Answer only from the passages returned. Quote the key words. Cite document, section, edition date and link for each point. Lay it out as in `../builders-workflow/references/answer-format.md`: heading, answer, what to do, numbered sources with each document name linked to the passage's `url`, closing line.
3. If the passages do not answer it (or none come back), say "Our regulations library does not cover that yet" and who can help: a building control body, a structural engineer, or the HSE. **Do not search the web.** If it may be a known gap (a British Standard such as BS 7671, a JCT contract, Wales or Scotland, an older edition), call `about_regulations_library` with part "gaps" and say plainly why it is missing. Never answer it from memory, even when you think you know.
6. Asked what the library covers, which version it is, or what it lacks? Call `about_regulations_library` (part "summary"; "contents" or "gaps" for the full lists) and answer from it only.
4. Never say work is safe or compliant. Say what the rules say and what the builder must check.
5. If the question touches a live job (for example a wall on the Elm Avenue job), also check the job's facts with `get_job` and mention anything relevant, such as "engineer not yet booked".
