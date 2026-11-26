# 0020: Docs structure: one overview, four designs, one source of truth

Date: 26 Nov 2026. Status: proposed (Florin, 26 Nov 2026).

## Context

The docs grew with the work. A review on 26 Nov 2026 found:

- **Rules repeated in many places.** The asbestos rule shows up 13 times across the server text, plugin rules, skills,
  agents and the Claude app instructions. Copies drift apart.
- **Stale status in files loaded in every session.** AGENTS.md said 23 Nov and listed done work as "next".
- **One design file too big to use.** `regulations-corpus.md` has 610 lines and 25 diagrams.
- **ADRs used two ways.** Some take changes as dated notes inside the old ADR (0008, 0009, 0010, 0013). Others are
  replaced by a new ADR. ADR 0013 now reads as a change log, with live figures such as chunk counts.
- **An accepted ADR is missing.** ADR 0017 sits only on an unmerged branch.

The docs serve two readers: Florin and the models. Both do best with short files, clear names, one index and links,
rather than one long file.

## Decision

1. **Layout.** Code lives in `system/`, `plugin/`, `deploy/`. Technical docs live in `architecture/`:

   ```
   architecture/
     ARCHITECTURE.md        high level, the agents, a map of the designs
     design/
       runtime/  design.md  + flows/   server runtime and plugin runtime
       ingest/   design.md  + flows/   harvest, parse, check, chunk, embed, load
       eval/     design.md  + flows/   golden set, runs, judges, reports
       data/     design.md             two entity diagrams: regulations, and firm plus server
   ```

2. **Flows are children of a design.** One flow per file, 5 to 8 steps. A flowchart by default; a sequence diagram
   only when the order of calls between three or more parts matters. Each step names the real module and function,
   so a reader can jump to the code.
3. **Few diagrams.** As few as each file needs. About 10 is a warning sign, not a hard limit.
4. **One source of truth.** Each fact or rule lives in one place. Everything else links to it.
   - Answer rules every answer needs: the server instructions (`versions/server/`). The plugin rules keep only what the
     server lacks.
   - Answer layout: `plugin/skills/builders-workflow/references/answer-format.md`.
   - Live figures and status: a status file, not AGENTS.md or ADRs.
   - Lists (tools, tables, folders): the code or the one doc that owns them. Others link.
5. **AGENTS.md stays short and stable:** purpose, rules, commands, the "read first" table, the branch and deploy rule
   once. No status, no copied lists.
6. **ADRs record decisions, not state.** An accepted ADR is not rewritten. A change is a new ADR. The old one gets
   one line in its header: "Changed by NNNN". `decisions/README.md` lists every ADR with its status. Existing dated
   notes stay as history.

## Options considered

- **One long architecture file.** Easy to find, but heavy to load and hard to read. Rejected.
- **A data design per pipeline.** Ingest, runtime and evals use the same tables, so the copies would drift.
  Rejected for one data design.
- **A separate `sequences/` folder.** Splits a flow from its design. Rejected: flows sit under their design.

## Consequences

- The current design files move and split into the new folders. Old paths are removed, and links are updated in the
  same commit.
- Rules move out of skills, agents and app instructions to the one place they belong.
- A small test could check that every code path named in `architecture/` still exists (parking lot).
- More files to keep current. The one-source rule keeps that cost down.
