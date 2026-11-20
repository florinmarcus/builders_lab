# Research backlog

Ordered by priority. Top first.

1. **Council refurbishment use case** (main direction, see `directions.md`). Desk research done 7 Nov 2026 (`reports/Council refurbishment and asbestos.md`). Still open:
   - Follow-up questions for Builder 1 (`interviews/builder-1.md`), including 2–3 anonymised email threads.
   - Whether councils allow contractors to put council data into an AI tool (legal review).
   - Done 19 Nov 2026: asbestos SI 2026/1153 (made 2 Nov 2026; new reg 20 from 25 Nov 2027) and Awaab's Law Phase 2 (30 Nov 2026, SI 2026/1195). See `domain/corpus-inventory/`.
2. **Hosting and model costs:** done 18 Nov 2026 (`hosting-costs/claude-app-vs-bedrock.md`). Still open: AWS credits for Claude, real tokens per PDF page.
3. **WhatsApp as an input channel:** WhatsApp Business Platform (Cloud API) limits: only a business number, no reading of personal chats or groups (to verify); options: forward messages and files to a business number, or upload exported chats. Costs and Meta rules.
4. **Voice with connectors:** can Claude (and ChatGPT) voice mode on the phone use custom MCP connectors? UK GBP prices for Claude Pro and Team.
5. **What do Romanian builders use today?** More interviews (`interviews/interview-guide.md`), Romanian Builders Network event 21 Nov 2026.
6. **Interfaces and access**: ChatGPT Apps SDK, Claude MCP apps (which plans users need, costs); Gmail and Microsoft 365 rules for reading mail and calendar (Google restricted/sensitive scopes, verification).
7. **Finish the walk-through** (`market/walkthrough.md`): big platforms, ChatGPT and Claude on their own, Romanian tools.
8. **Test regulation assistants in Romanian**: StructureGPT and BuildingRegs.app free plans, 3–4 builder questions.
9. **Candidate feature: upload a RAMS, explain it in Romanian.** No integration or passwords.
10. **Ask RAMSReady and DocGen about APIs or partnerships** (later, only if a pilot works). No logging in to their apps on users' behalf (agreed 7 Nov 2026).
11. **Licences for copyrighted sources** (not urgent): BSI/IET (BS 7671), NHBC, JCT. Their terms forbid storing even contents pages (`domain/corpus-inventory/d-tax-and-paid-toc.md`). BSI sells software licences: copyright@bsigroup.com. Prototype rule: ADR 0008.
12. **Phone files (iPhone) as an input** (side question, noted 20 Nov 2026, not urgent): can a builder give Claude access to photos and files on their phone through a connector? Guess, to check: our connector runs on our server, so it cannot read the phone directly; options are attaching files in the Claude app chat, or an upload page or share-sheet route into our store.
