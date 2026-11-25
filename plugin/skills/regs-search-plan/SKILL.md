---
name: regs-search-plan
description: Use only inside Marcus Limited (the building firm) answers, just before calling search_regulations (BuildersRegulations connector). Turns the builder's question into one to three short English searches, runs them together and merges the passages.
---

# Plan the regulations search

Read `../../shared/rules.md` first. This replaces sending the builder's words to `search_regulations` as they are.

1. **English terms.** Romanian question: use the English terms from `lookup_terms` (call it now if not done yet). Builder slang becomes the proper term ("gips-carton" -> plasterboard).
2. **Split by topic.** One search per separate thing the builder needs to know, at most three.
   - "Do I need building control to take out this wall, and who is the principal designer?" -> two searches.
   - "What if I miss a pay less notice?" -> one search. Do not split a single question.
   - A job question that needs no rule (dates, emails, papers) needs no search.
3. **Write each search** as a short plain sentence or phrase, 4 to 12 words, in English:
   - keep the builder's key words;
   - add the official term from `lookup_terms` where there is one;
   - name the subject (structure, fire, asbestos, payment, CDM) if the question makes it clear;
   - never add a regulation number, section or document you did not get from a tool.
4. **Run them together.** Call `search_regulations` once per search, all in the same turn. Add `as_of_date` (YYYY-MM-DD) when the question is about a job (its date from the firm server) or a past date.
5. **Merge.** The same section from two searches counts once. Answer each part only from its own passages. A part with no useful passages: "Our regulations library does not cover that yet", and who to ask (building control, a structural engineer, the HSE). Never search the web.
6. **Show the plan.** Before the searches, one short line in the user's language naming them, for example "Searching: removing a load-bearing wall; principal designer duties."
