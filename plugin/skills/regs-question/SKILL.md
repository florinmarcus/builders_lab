---
name: regs-question
description: Use for questions about building regulations, building control, structure, fire, asbestos rules, CDM or payment law in England. For example "do I need building control to remove this wall?".
---

# Building regulations question

Read `../../shared/rules.md` first.

1. Call `search_regulations` with the builder's question in plain words. Add `as_of_date` if they ask about a past date.
2. Answer only from the passages returned. Quote the key words. Cite document, section, edition date and link for each point.
3. If the passages do not answer it, say so and say who can: a building control body, a structural engineer, or the HSE.
4. Never say work is safe or compliant. Say what the rules say and what the builder must check.
5. If the question touches a live job (for example a wall on the Elm Avenue job), also check the job's facts with `get_job` and mention anything relevant, such as "engineer not yet booked".
