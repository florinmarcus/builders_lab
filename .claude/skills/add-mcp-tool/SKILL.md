---
name: add-mcp-tool
description: Add or change a tool on the builders MCP server end to end (service, versioned description, registration, tests, plugin, docs, deploy). Use when asked to add a new tool, rename one, or change what a tool returns.
---

# Add or change an MCP tool

Follow every step. Each one exists because skipping it broke something before.

1. **Service function** in `system/api/builders_api/service/<area>.py`. Plain code, no model (ADR 0006). Takes `firm` (uuid) first; raises typed errors from `errors.py` (`ValidationError`, `NotFoundError`, ...), never returns error strings. Return a dict; put sources as `Source`-shaped dicts (`type`, `id`, `label`, `date`) so traces pick them up.
2. **Description file**: `system/api/builders_api/versions/tools/<name>.v1.md` (changing an existing tool: add `.v<N+1>.md`, never edit a locked file). Say when to use it, its inputs and what it returns, in plain words.
3. **Lock it**: from `system/api`, `python -m builders_api.versions --lock`.
4. **Register** in `system/api/builders_api/mcp_server/server.py` inside `build_server()`: `@server.tool(description=desc("<name>"), annotations=READ_ONLY or ToolAnnotations(...))`, body `return run_tool("<name>", lambda f: <service call>)`. Typed inputs: plain types or models from `contracts.py`.
5. **JSON between agents changed?** Edit `system/api/builders_api/contracts.py`, bump `CONTRACT_VERSION`, run `python -m builders_api.contracts --write`, update the examples in `plugin/agents/*.md` and `plugin/skills/builders-workflow/SKILL.md`.
6. **Tests**: a service test in `tests/` (seeded database fixture `seeded`), and add the name to the tool set in `tests/test_mcp_http.py`. Run `TEST_DATABASE_URL=... pytest -q`.
7. **Plugin**: give the tool to the specialist(s) that need it (`plugin/agents/<name>.md`, "Tools you may use"), mention it in `plugin/skills/builders-workflow/SKILL.md` and `plugin/claude-app/PROJECT_INSTRUCTIONS.md` if the flow uses it. `claude plugin validate ./plugin`.
8. **Docs**: the tool table in `system/api/README.md`; the task skill and agent in `architecture/design/runtime/design.md` if they are new; update the tool count in `AGENTS.md` "Where we are".
9. **Parking lot**: any shortcut gets a new unique ID in `requirements/parking-lot.md`.
10. **Commit and push to main** (pull first). The pipeline tests and deploys. Then check `https://<server>/healthz` and, in the Claude app, **reconnect the connector** so it sees the new tool list.

Stop and ask Florin if the tool would write data, send anything outside, or call a model.
