---
name: builders-workflow
description: Use for EVERY question about the builder's jobs, emails, documents, payments, paperwork or regulations. Runs the fixed answer workflow (router, specialist, draft, verify, reply) from the agent contracts so every answer is grounded and checked.
---

# Builders answer workflow (contracts.v3)

Read `../../shared/rules.md` first. Follow these steps in order for every answer. Do not skip step 4.

## 0. Language in (translator)

Start the `translator` sub-agent with `{"contract": "contracts.v3", "direction": "in", "text": "<user's words>"}`.
It returns a TranslatedQuestion: `language`, `english_question`, `terms` (with `mismatch` notes) and maybe a `clarifying_question`.
If there is a clarifying question, ask it (in the user's language) and stop. Otherwise use `english_question` from here on: everything sent to tools and specialists is English.
No sub-agents here? Call `lookup_terms` yourself and write the English question.

## 1. Route

Decide the `kind`:

| The builder asks about | kind | specialist sub-agent |
|---|---|---|
| new emails, what came in, filing | inbox | `inbox-clerk` |
| approved changes, variations, final account | variations | `variations` |
| payment notices, pay less, applications, final date | payments | `payments` |
| what's missing, handover, subcontractor papers, insurance | paperwork | `paperwork` |
| building regulations, building control, asbestos rules, CDM, the law | regulations | `regulations` |
| running late, delays, extensions, damages, "what have I sent", who to tell | delays | `delays` |

Refuse plainly (no specialist) if asked to rank, score or monitor workers or tenants, or to decide about a person. If asked to send, pay or sign: you will prepare a draft only.

## 2. Ask the specialist

Start the specialist sub-agent with a SpecialistTask (JSON):

```json
{"contract": "contracts.v3", "question": "Show every change the client approved on Elm Avenue", "kind": "variations", "job": "ELM-22"}
```

It returns Findings JSON: `claims` (each with text, status, quote, source, values), `gaps`.
If sub-agents are not available here, do the specialist's steps yourself (see `agents/<name>.md`) and build the same Findings.

## 3. Draft (English), then language out

Write the full answer in English from the Findings only. If the user's language is Romanian, then start the `translator` with a TranslationOut (`direction` "out", `language` "ro", the English `chunks`, and `keep_english`: every quote and official term) and use the TranslatedAnswer chunks as the text to verify and show. Chunks: (1) the answer in two or three short sentences; (2) details; (3) sources (email or document, sender, date; regulations with section and edition date). Include the AI notice ("AI answer, please check." / "Răspuns AI, vă rog verificați."). Every £ amount and date must come from a claim. In Romanian, keep UK terms in English in brackets and quotes in English with a translation; where `lookup_terms` said `mismatch`, explain the difference.

## 4. Verify

Call `verify_answer` with:

```json
{"text": "Victoria approved underfloor heating (£2,400 + VAT). AI-generated, check before use.",
 "claims": [{"id": "c1", "quote": "Yes, go ahead with the underfloor heating in the kitchen.", "source": {"type": "document", "id": "<attachment id>"}}]}
```

Schemas: `../../shared/contracts.schema.json` (SpecialistTask, Findings, Answer, Verdict).

Use `{"type": "calculation", "id": "<job ref>"}` for dates from `get_payment_dates`.
If `pass` is false: fix only the flagged parts (remove or correct the claim, add the notice, reword) and verify again. At most two rounds. If it still fails, tell the builder what could not be confirmed.
Warnings (personal data): keep the detail only if the builder needs it.

## 4b. Calendar (with the user's yes)

If the answer has actions or deadlines (send a notice by a date, a quote due, a payment notice, an inspection, a moved site day), offer: "Shall I add this to your calendar?" Only after a yes, create or move the entry in the user's "Marcus Limited" calendar with the Google Calendar connector (title, date, one line of detail with the source). To see what is planned on a job, read that calendar first.

## 5. Reply (speak first)

Give only chunk 1, then: "Say *next* for details, or *sources* for where it came from" (in the user's language). Give the next chunk each time they ask. In Romanian, also offer the English version.
Offer the next step as a draft (email, invoice, notice), written in English for the recipient, with a short summary in the user's language. Never send.
