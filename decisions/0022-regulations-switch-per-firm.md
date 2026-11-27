# 0022: Regulations switch per firm, saved and enforced on our server

Date: 27 Nov 2026. Status: accepted (Florin, 27 Nov 2026), not built. Parking lot: N23.

## Context

Florin wants builders to choose whether answers also check the regulations library, like a setting. Talks with a
design-and-build firm (`research/interviews/builder-2.md`) showed the user will mostly be on the Claude app and phone.
Every regulations answer must come from our library, never from memory (server instructions, ADR 0021 point 3).

## Decision

1. **A switch per firm: regulations on or off.**
   - On: answers also search the regulations library where it helps, and cite it.
   - Off: answers use only the firm's data (jobs, emails, documents). A regulations question gets "Regulations are
     switched off; turn them on to check" (in the user's language). Never an answer from memory.
2. **Saved on our server**, with the firm's profile. `get_firm_profile` returns it, so every new chat on any device
   sees it. A tool on the firm server turns it on or off.
3. **Enforced in plain code on the server** (ADR 0006): with the switch off, `verify_answer` flags any regulation
   claim or regulations citation in a draft.
4. Default: on.

## Options considered

- **No switch, regulations rule always on:** safest, but Florin wants the choice; off only removes the lookups, not
  the rule.
- **A hook:** hooks run in Claude Code; not known to run in the Claude app, not on the phone. Would silently do nothing
  for most users.
- **A setting inside the plugin:** the plugin is the same file for every firm; it cannot hold one firm's choice.
- **Claude remembers it from chat:** not reliable across chats and devices.

## Consequences

- New field on the firm record (migration), a change to `get_firm_profile`, a new tool to set it, a new check in
  `verify_answer`, and new versioned tool descriptions (`--lock`).
- The workflow skill reads the switch before planning regulations searches.
- Later, the same place can hold other preferences (language, answer length); a settings card in the chat (connector
  UI) can show them. Not decided here.
