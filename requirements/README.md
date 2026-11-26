# Requirements

Built from `research/`. Status: `status.md`. Start with:

- `users.md`: who uses it (personas).
- `use-cases.md`: what they do with it, linked to pain points.
- `scope.md`: in and out of scope for the first version.
- `non-functional.md`: cost limits, languages, privacy, devices.

## Open questions (moved from AGENTS.md, 26 Nov 2026)

- Romanian answers: when, and for which users (ADR 0001)?

## Answered questions (moved from AGENTS.md, 20 Nov 2026)

| Question | Answer | Where |
|---|---|---|
| Which businesses? | UK builders of every size, mostly private clients and main contractors, some council work | `prototype.md` |
| Where? | UK first (England). Romania later: see `research/domain/ai-regulation.md` | `prototype.md` |
| Which language? | English for the UK prototype; Romanian chat over English sources is the direction | `decisions/0001-romanian-chat-over-english-sources.md` |
| Who pays? | The builder buys their own Claude Team plan and adds our connector | `research/directions.md`, `decisions/0004`, `decisions/0014` |
| How much will a firm pay us? | Pilot £100 for 3 months; then £250 setup and £49 a month (a guess to test) | `business-plan.md`, `decisions/0014` |
