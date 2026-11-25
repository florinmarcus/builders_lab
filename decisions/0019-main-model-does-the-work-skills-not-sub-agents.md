# 0019: The main model does the work; skills, not sub-agents

Date: 25 Nov 2026. Status: accepted (Florin, 25 Nov 2026). Changes how ADR 0011 (plugin) runs an answer.

## Context

Florin tried the installed plugin. The first answer took a couple of minutes and came all at once, with nothing
on screen before it. The search itself is fast (about 1.3 s). The time went into sub-agents:

- every question started a specialist sub-agent on Haiku, and a Romanian question also started the translator
  twice (in and out), one after another;
- each sub-agent starts cold, reads its instructions and shows nothing until it ends;
- `verify_answer` is plain code on our server and takes well under a second, so it is not the cause.

The regulations specialist also sent the builder's question to `search_regulations` as it was, with no step that
turns it into searches.

We did not time the flow: Florin has no API key for a test run here (S156).

## Decision

1. **The main model does the work.** `builders-workflow` routes to a task skill (`references/routing.md`) and
   follows its steps itself, calling the tools directly. The builder sees each tool call as it happens.
2. **One status line first.** Before the tools, one short line in the builder's language says what is being
   checked, with no facts in it. The answer itself is still checked by `verify_answer` before it is shown.
3. **Translator as a skill.** `builders-translate` (part in: `lookup_terms`, then the question in English; part
   out: plain spoken Romanian, quotes and £ amounts kept exactly).
4. **Search planning as a skill.** `regs-search-plan` runs before every `search_regulations` call: one to three short
   English searches, one per separate topic, official terms from `lookup_terms`, no section numbers from memory,
   all run in the same turn, passages merged.
5. **Sub-agents only for big jobs:** more than 5 emails to file, or one question across three or more jobs. The
   agent files and contracts.v4 stay for that.

## Options considered

- **Keep sub-agents, show progress.** In Florin's test the app showed nothing of the sub-agents' work until they ended, and the cold starts stay.
- **Faster sub-agents** (smaller prompts). Still a cold start per hop and nothing on screen.
- **Search planning on our server.** Would need a model on the server (ADR 0006). Planning stays in Claude; the
  server-side "too broad" reply and lanes (ADR 0016) still come later.

## Consequences

- Fewer hops: an English question has none, a Romanian one has none instead of three.
- The main model (often Opus or Sonnet) does the specialist work, so each step costs more on the user's plan than
  on Haiku. Accepted: speed and seeing the steps matter more for the demo.
- Specialist tool limits (S51) never applied to skills anyway; the rules file and `verify_answer` still apply.
- Not measured yet: time per answer before and after, and whether split searches find more rules than one search
  (S156). Rule coverage on the dev set (`evals/paired.py`) can test the split offline with planned queries.
