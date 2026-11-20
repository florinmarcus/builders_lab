---
name: builders-workflow
description: Use for EVERY question about the builder's jobs, emails, documents, payments, paperwork or regulations. Runs the fixed answer workflow (router, specialist, draft, verify, reply) from the agent contracts so every answer is grounded and checked.
---

# Builders answer workflow (contracts.v1)

Read `../../shared/rules.md` first. Follow these steps in order for every answer. Do not skip step 4.

## 0. Language

Detect the user's language (Romanian or English). If Romanian, call `lookup_terms` with their words and turn the question into English using the English terms. Everything you send to tools and specialists is English. Reply, and ask any clarifying question, in the user's language.

## 1. Route

Decide the `kind`:

| The builder asks about | kind | specialist sub-agent |
|---|---|---|
| new emails, what came in, filing | inbox | `inbox-clerk` |
| approved changes, variations, final account | variations | `variations` |
| payment notices, pay less, applications, final date | payments | `payments` |
| what's missing, handover, subcontractor papers, insurance | paperwork | `paperwork` |
| building regulations, building control, asbestos rules, CDM, the law | regulations | `regulations` |

Refuse plainly (no specialist) if asked to rank, score or monitor workers or tenants, or to decide about a person. If asked to send, pay or sign: you will prepare a draft only.

## 2. Ask the specialist

Start the specialist sub-agent with a SpecialistTask (JSON):

```json
{"contract": "contracts.v1", "question": "Show every change the client approved on Elm Avenue", "kind": "variations", "job": "ELM-22"}
```

It returns Findings JSON: `claims` (each with text, status, quote, source, values), `gaps`.
If sub-agents are not available here, do the specialist's steps yourself (see `agents/<name>.md`) and build the same Findings.

## 3. Draft

Write the full answer from the Findings only, in the user's language, in chunks: (1) the answer in two or three short sentences; (2) details; (3) sources (email or document, sender, date; regulations with section and edition date). Include the AI notice ("AI answer, please check." / "Răspuns AI, vă rog verificați."). Every £ amount and date must come from a claim. In Romanian, keep UK terms in English in brackets and quotes in English with a translation; where `lookup_terms` said `mismatch`, explain the difference.

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

## 5. Reply (speak first)

Give only chunk 1, then: "Say *next* for details, or *sources* for where it came from" (in the user's language). Give the next chunk each time they ask. In Romanian, also offer the English version.
Offer the next step as a draft (email, invoice, notice), written in English for the recipient, with a short summary in the user's language. Never send.
