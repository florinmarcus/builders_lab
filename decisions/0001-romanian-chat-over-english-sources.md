# 0001: Romanian chat over English sources

Date: 7 Nov 2026. Status: accepted (to be confirmed by evals).

## Context

Users talk to the assistant only in Romanian. The methodology and rules we can ingest (UK Building Regulations guidance, CDM 2015, NHBC Standards, Planning Portal) are in English. Users in the UK also need the official English terms when they deal with inspectors and suppliers.

## Decision

Three steps per question:

1. **Rewrite the question in English for search.** One model call translates the Romanian question, normalises builder slang (with a glossary) and decides whether a clarifying question is needed. Clarifying questions go to the user in Romanian.
2. **Search the English sources** with the English query.
3. **Generate the answer directly in Romanian** from the English passages. Keep official terms in English in brackets, e.g. "Documentul Aprobat B (Approved Document B)". Cite the English source.

## Options considered

- **A. Full translation layer** (Florin's first idea): translate question to English, search, answer in English, translate the answer to Romanian. Simple to reason about, but one extra model call per question, and meaning and terms can get lost in each translation.
- **B. Translate the query only, answer in Romanian** (chosen). Cheaper, fewer error points, exact terms kept.
- **C. Multilingual embeddings, no translation.** Search Romanian against English directly. Worth testing later; less control over terms.

## Consequences

- We need a Romanian-English builder glossary (`research/domain/glossary.md`).
- We need Romanian test questions in `evals/`, scored on retrieval hits, answer correctness and correct terms.
- Model choice must check Romanian writing quality (`research/models/`).
- Compare A and B on the same eval set before we treat this as final.
