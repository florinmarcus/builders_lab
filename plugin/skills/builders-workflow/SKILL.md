---
name: builders-workflow
description: Use for questions about Marcus Limited's (the building firm's) jobs, job emails, documents, payments, paperwork, delays or building regulations, in Romanian or English, when the BuildersMCP connector is available. Loads the firm's live context, routes to a specialist, verifies with plain-code checks and replies in short spoken chunks.
---

# Builders answer workflow (contracts.v4)

Rules: `../../shared/rules.md` (read once per conversation). Steps in order; never skip step 5.

1. **Firm context (once per conversation).** Call `get_firm_profile`. It tells you our people and addresses, the jobs (refs, clients, contacts with emails, contracts) and what is due in the next 14 days. Use job refs from it in every other call.
2. **Language in.** Romanian or English? For Romanian, start the `translator` agent with `{"contract": "contracts.v4", "direction": "in", "text": "<user's words>"}` and use its `english_question`. If it returns a `clarifying_question`, ask it and stop. (No sub-agents: call `lookup_terms` yourself.)
3. **Route** with `references/routing.md`: pick the kind and the specialist. Refuse decisions about workers or tenants.
4. **Specialist.** Start it with a SpecialistTask:

   ```json
   {"contract": "contracts.v4", "question": "Show every change the client approved on Elm Avenue", "kind": "variations", "job": "ELM-22"}
   ```

   It returns Findings (claims with exact quotes and sources, plus gaps).
   **How to start it, in this order:**
   - The plugin's agent (`builders:<name>`) if it is available (Cowork, Claude Code).
   - Otherwise, if you can start a general sub-agent: start one **on Haiku**, with a prompt made of the full text of `../../agents/<name>.md` (after its front matter) followed by the SpecialistTask JSON. It has the same tools as you; it must use only the tools that file lists.
   - Otherwise (no sub-agents at all): follow `../../agents/<name>.md` yourself.
   The same applies to the `translator` in steps 2 and 5.
5. **Draft and verify.** Write the answer in English from the Findings only, in chunks (see `references/answer-format.md`). Romanian user: `translator` with direction "out". Then call `verify_answer` with the final text and the claims:

   ```json
   {"text": "Victoria approved underfloor heating (£2,400 + VAT).",
    "claims": [{"id": "c1", "quote": "Yes, go ahead with the underfloor heating in the kitchen.", "source": {"type": "document", "id": "<attachment id>"}}]}
   ```

   Fix what it flags; at most two rounds. Payment dates: source `{"type": "calculation", "id": "<job ref>"}`.
6. **Calendar (with a yes).** Deadlines or actions? Offer to add them to the "Marcus Limited" calendar; create or move entries only after the user agrees.
7. **Reply, speak first.** Chunk 1 only, then "Say next for details, or sources for where it came from" in the user's language; offer the English version to Romanian users. Drafts for others: in English, addressed to the right person (email from the sources or the profile). Never send.

Schemas: `../../shared/contracts.schema.json`.
