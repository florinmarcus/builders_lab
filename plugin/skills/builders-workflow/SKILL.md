---
name: builders-workflow
description: Use for questions about Marcus Limited's (the building firm's) jobs, job emails, documents, payments, paperwork, delays or building regulations, in Romanian or English, when the BuildersMCP connector is available. Loads the firm's live context, routes to the right task skill, verifies with plain-code checks and replies in short spoken chunks.
---

# Builders answer workflow (contracts.v4)

Rules: `../../shared/rules.md` (read once per conversation). Steps in order; never skip step 6.
Do the work yourself, in this conversation, so the builder sees each step (ADR 0019). No sub-agents unless step 4 says so.

1. **Firm context (once per conversation).** Call `get_firm_profile`. It tells you our people and addresses, the jobs (refs, clients, contacts with emails, contracts) and what is due in the next 14 days. Use job refs from it in every other call.
2. **Language in.** Romanian? Follow the `builders-translate` skill, part "in": `lookup_terms`, then the question in English. If it is too unclear, ask the one clarifying question and stop.
3. **Route and say so.** Pick the kind and its task skill with `references/routing.md`. Refuse decisions about workers or tenants. Then write one short line in the user's language saying what you are checking, with no facts in it: "Checking the Riverside emails and contract." / "Mă uit în emailurile și contractul de la Riverside."
4. **Do the task skill's steps yourself**, calling the tools directly. Before any `search_regulations` call, follow the `regs-search-plan` skill. Collect claims as you go: one per fact, the exact quote and its source id from the tool results.
   **Sub-agent only for big jobs:** more than 5 emails to file, or one question across three or more jobs. Then start the plugin's agent (`builders:<name>`), or a general sub-agent on Haiku given the text of `../../agents/<name>.md`, with a SpecialistTask, and draft from its Findings:

   ```json
   {"contract": "contracts.v4", "question": "File the 12 new emails and record their facts", "kind": "inbox", "job": null}
   ```

5. **Draft.** Write the full answer in English from the claims only, in chunks (see `references/answer-format.md`). Romanian user: follow `builders-translate` part "out".
6. **Verify.** Call `verify_answer` with the final text (in the user's language) and the claims:

   ```json
   {"text": "Victoria approved underfloor heating (£2,400 + VAT).",
    "claims": [{"id": "c1", "quote": "Yes, go ahead with the underfloor heating in the kitchen.", "source": {"type": "document", "id": "<attachment id>"}}]}
   ```

   Fix what it flags; at most two rounds. Payment dates: source `{"type": "calculation", "id": "<job ref>"}`.
7. **Calendar (with a yes).** Deadlines or actions? Offer to add them to the "Marcus Limited" calendar; create or move entries only after the user agrees.
8. **Reply, speak first.** Chunk 1 only, then "Say next for details, or sources for where it came from" in the user's language; offer the English version to Romanian users. Drafts for others: in English, addressed to the right person (email from the sources or the profile). Never send.

Schemas: `../../shared/contracts.schema.json`.
