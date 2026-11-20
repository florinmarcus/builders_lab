# 0012: Language and voice: reply in the user's language, English to the tools, speak first

Date: 20 Nov 2026. Status: accepted. Builds on ADR 0001 (Romanian chat over English sources).

## Context

Builders will ask in Romanian or English, often by voice, on site. Our data and the regulations are in English, and UK recipients (clients, councils, suppliers) need English. Answers are often listened to, not read.

## Decision

- **Detect the language** of each question; reply and ask clarifying questions in it. Romanian stays Romanian until the user switches.
- **English to the tools.** For Romanian questions, Claude calls `lookup_terms` (our glossary, plain code) and sends English terms to every other tool. Stored data is never translated.
- **Romanian answers** keep official UK terms in English in brackets, keep quotes in English with a translation, explain terms where the systems differ (`mismatch`), and offer the English version.
- **Outgoing drafts in English** by default (emails, letters, notices, invoices), with a short summary in the user's language; "give me the English final" shows the full text.
- **Speak first.** First chunk two or three short sentences, no tables; then "say next for details, or sources". The whole answer is verified (`verify_answer`) before the first chunk.
- **Glossary source of truth:** `research/domain/glossary.md`; generated `system/api/builders_api/terminology/glossary.json` (test keeps them in step).
- `verify_answer` accepts the short and Romanian AI notices, Romanian dates, and bans Romanian phrases such as "fără azbest".

## Options considered

- **Translate stored data into Romanian:** doubles storage and breaks quote checks against the original.
- **Translate every answer from English (ADR 0001 option A):** extra steps, terms drift.
- **Model-based term lookup on our server:** against ADR 0006; the glossary lookup is plain code.

## Consequences

- Most glossary rows are "unverified": a native-speaker tradesperson must review them (parking lot).
- Word-ending matching for Romanian is simple and will miss some forms.
- Evals need Romanian questions and spoken-style checks (N9).
