---
name: builders-translate
description: Use only inside Marcus Limited (the building firm) answers when the builder writes or speaks Romanian. Part "in" turns the question into UK English with the official terms (lookup_terms); part "out" turns the checked English answer into plain spoken Romanian.
---

# Translate between Romanian and UK English

Read `../../shared/rules.md` first. Do this yourself in the conversation; no sub-agent.

## Part "in" (the builder's words)

1. Decide the language: Romanian or English. English: nothing to do.
2. Call `lookup_terms` with the builder's words.
3. Write the question in plain UK English, using the English terms from `lookup_terms` (builder slang turned into the proper term, e.g. "gips-carton" -> plasterboard). Use this English question in every other tool call.
4. Where a term has `mismatch: true`, keep its note: the answer must explain the difference.
5. Too unclear to look up (no job, no subject)? Ask one short clarifying question in Romanian and stop.

## Part "out" (the checked English answer)

1. Translate each chunk into plain, spoken Romanian, short sentences.
2. Keep quotes and official terms in English exactly as written ("Approved Document A", "pay less notice"), with the Romanian after them in brackets.
3. Keep every £ amount exactly as written (£2,400, never 2.400 £), so `verify_answer` can check it. Dates may use Romanian month names (30 noiembrie 2026).
4. Never add facts, never drop a warning, never add disclaimer lines.
5. Offer the English version at the end.

Example: „Victoria a aprobat încălzirea în pardoseală (underfloor heating), £2,400 + TVA, pe 3 noiembrie. Citat: „Yes, go ahead with the underfloor heating in the kitchen.” (Da, mergeți înainte cu încălzirea în pardoseală în bucătărie.)"
