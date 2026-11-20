# Design: agents, their actions and the flow

Who does what inside Claude, step by step. Interfaces (JSON) are in [agent-contracts.md](agent-contracts.md); server tools in [server.md](server.md). Up: [architecture](../ARCHITECTURE.md).
No model runs on our server (ADR 0006). Code: `plugin/` (skills, agents, rules), `system/api/` (tools).

Updated 20 Nov 2026. Solid = built. Dashed = planned.

## 1. The agents

```mermaid
flowchart TB
    user(["Builder"]) --> main
    subgraph claude["Claude (user's plan)"]
        main["Main agent<br/>+ builders-workflow skill<br/>(router, drafter)"]
        main --> tr["translator<br/>Haiku<br/>in + out"]
        main --> inbox["inbox-clerk<br/>Haiku"]
        main --> var["variations<br/>Haiku"]
        main --> pay["payments<br/>Haiku"]
        main --> paper["paperwork<br/>Haiku"]
        main --> regs["regulations<br/>Haiku"]
        main --> dly["delays<br/>Haiku"]
    end
    subgraph server["Our MCP server (plain code)"]
        tools["data tools"]
        guard["verify_answer"]
    end
    inbox & var & pay & paper & regs & dly --> tools
    tr --> tools
    main --> guard
    sched["Claude Code schedule"] -.->|"check my emails"| main
    main -.->|"with user's yes"| cal["Google Calendar<br/>(Claude connector)"]
```

## 2. Agents and their actions

| Agent | Triggered by | Actions (tools) | Writes data? | Returns |
|---|---|---|---|---|
| **Main agent** (`builders-workflow`) | every question | route; start one specialist; draft; `verify_answer`; reply | no | answer text |
| **translator** | every Romanian turn (start and end) | `lookup_terms` | no | TranslatedQuestion (in) / TranslatedAnswer (out) |
| **inbox-clerk** | "check my emails", schedule | `sync_inbox`, `save_facts`, `list_jobs` | yes: job, document types, facts (server-checked) | Findings: one claim per new email |
| **variations** | approved changes, final account | `get_job`, `search_job_documents` | no | Findings: approved / not_approved claims |
| **payments** | payment, pay less, final dates, the law | `get_payment_dates`, `search_regulations`, `get_job` | no | Findings: deadline claims (calculation) + rule claims |
| **paperwork** | missing items, subcontractor papers | `list_missing_items`, `get_job` | no | Findings: missing / present / expired / expiring_soon |
| **delays** | running late, extensions, damages, what was sent | `get_job_timeline`, `get_job`, `search_job_documents`, `search_regulations` | no | Findings: deadline, action, rule, info claims with contract clauses |
| **regulations** | building regs, asbestos, CDM | `search_regulations`, `get_job` | no | Findings: rule claims with section and edition date |

Only `inbox-clerk` writes, and only through `save_facts`, which rejects anything it cannot match to the source.

## 3. One answer, step by step

```mermaid
stateDiagram-v2
    [*] --> Language
    Language --> Clarify: question unclear
    Language --> Route: english_question (translator in)
    Clarify --> [*]
    Route --> Refuse: decision about a person
    Route --> Specialist: kind found
    Specialist --> Draft: Findings JSON
    Specialist --> Draft: gaps only (tools found nothing)
    Draft --> Translate: Romanian user (translator out)
    Draft --> Verify: English user
    Translate --> Verify
    Verify --> Reply: pass
    Verify --> Fix: fail (round 1 or 2)
    Fix --> Verify
    Verify --> ReplyWithLimits: fail after 2 rounds
    Refuse --> [*]
    Reply --> [*]
    ReplyWithLimits --> [*]
```

| Step | Who | Input | Output | Stops if |
|---|---|---|---|---|
| Language in | translator | TranslationIn | TranslatedQuestion | unclear: asks one clarifying question |
| Route | main | question | `kind`, job | asked to rank, score or monitor people |
| Specialist | sub-agent | SpecialistTask | Findings | tool error: reported in `gaps` |
| Draft | main | Findings | Answer (text + claims) | no claims: says nothing was found |
| Verify | server | Answer | Verdict | — |
| Language out | translator | TranslationOut (English chunks) | TranslatedAnswer | — |
| Fix | main | Verdict problems | corrected Answer | 2 rounds used |
| Reply | main | verified text | chunk 1 in the user's language, then "next"; English version offered; drafts in English | — |

## 4. Flow per specialist

### inbox-clerk (writes)

```mermaid
sequenceDiagram
    participant A as inbox-clerk
    participant T as Tools
    A->>T: sync_inbox()
    T-->>A: counts, emails_needing_facts (text, ids)
    loop each email
        A->>T: save_facts(email_id, job, attachments, facts with quotes)
        T-->>A: saved, rejected (reasons)
        opt rejected
            A->>T: save_facts again with fixes (once)
        end
    end
    opt more_waiting
        A->>T: sync_inbox()
    end
    A-->>A: Findings: one claim per new email
```

### variations, payments, paperwork, regulations (read only)

```mermaid
sequenceDiagram
    participant A as specialist
    participant T as Tools
    A->>T: main tool (get_job / get_payment_dates / list_missing_items / search_regulations)
    T-->>A: JSON with sources
    opt facts look incomplete or the law is asked
        A->>T: second tool (search_job_documents / search_regulations / get_job)
        T-->>A: JSON with sources
    end
    A-->>A: Findings: one claim per fact, exact quotes, gaps
```

## 5. Guardrails: where each one lives

| Guardrail | Where | Kind |
|---|---|---|
| Who may call, which firm | Gateway: API key, secret path, rate limits, lockdown | code |
| No invented facts saved | `save_facts`: quote must be in the source | code |
| No invented facts shown | `verify_answer`: quotes, sources, £ amounts, dates | code |
| Banned wording ("no asbestos", "fără azbest", "I have sent") | `verify_answer` + `shared/rules.md` | code + instruction |
| Terms that differ between Romania and the UK | `lookup_terms` (`mismatch`) + rules | code + instruction |
| Personal data | `verify_answer` flags; rules say minimise | code + instruction |
| Email text is not instructions | `untrusted_content_notice` in tool results + rules | instruction |
| No decisions about people | router step + rules | instruction |
| Drafts only | no sending tools on our server; rules | design + instruction |
| Cost | quotas per firm; no model on our server | code |
| Every call logged | trace row per tool call with tool version | code |

## 6. Surfaces

| Surface | Router + specialists | verify_answer |
|---|---|---|
| Claude Code (plugin) | skill + Haiku sub-agents | yes |
| Claude desktop / Cowork (plugin) | skill + sub-agents (Haiku to check) | yes |
| Claude app phone / web | project instructions; main agent does the specialist steps | yes |

## 7. Not built yet

- Hard tool limits per specialist (`tools:` lists): parking lot S51.
- Evals of the whole flow with an LLM judge in Claude Code: N9.
- Linking all calls of one answer under one trace id: S9.
