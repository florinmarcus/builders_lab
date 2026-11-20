---
name: builders-workflow
description: Use for EVERY question about the builder's jobs, emails, documents, payments, paperwork or regulations. Runs the fixed answer workflow (router, specialist, draft, verify, reply) from the agent contracts so every answer is grounded and checked.
---

# Builders answer workflow (contracts.v1)

Read `../../shared/rules.md` first. Follow these steps in order for every answer. Do not skip step 4.

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

Write the answer from the Findings only. Short answer first, then details, then sources. Include "AI-generated, check before use." Every £ amount and date you write must come from a claim.

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

## 5. Reply

Show the verified text. Then offer the next step as a draft (email, invoice, notice), never sent.
