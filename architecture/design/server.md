# Design: server

MCP server, security, data and deployment. Code: `system/api/`. Flows: [sequences/server.md](../sequences/server.md). Up: [architecture](../ARCHITECTURE.md).

Updated 24 Nov 2026. Solid = built. Dashed = planned.

## Components

```mermaid
flowchart LR
    client["Claude app /<br/>Claude Code"] --> gw

    subgraph proc["One Python process"]
        gw["Gateway<br/>security checks"] --> mcp["MCP layer<br/>(MCPServer, HTTP)"]
        mcp --> tools["Tool wrapper<br/>caller, access,<br/>quota, trace, errors"]
        tools --> svc["Service layer"]
        svc --> jobs["jobs"]
        svc --> docs["documents<br/>(full-text)"]
        svc --> pay["payments<br/>(date sums)"]
        svc --> regs["regulations"]
        svc --> inbox["inbox + facts<br/>(sync, save facts)"]
        ver["versions<br/>(texts + lock)"] --> mcp
        ver --> tools
    end

    jobs & docs & pay & inbox --> pg[("Postgres")]
    tools --> pg
    regs --> rag["rag.search<br/>(corpus)"]
    rag --> cpg[("corpus-db<br/>Postgres + pgvector<br/>read-only login")]
    rag --> bed["Bedrock: Titan (London),<br/>Rerank (Frankfurt)"]
    regs --> fb["fallback<br/>7 passages"]
    inbox --> eml["demo mail folder"]
    inbox -.-> gmail["Gmail API"]
```

## Security layers (ADR 0007)

```mermaid
flowchart TB
    req["Request"] --> h{"/healthz?"} -->|yes| ok200["200"]
    h -->|no| k{"Kill switch on?"} -->|yes| r503a["503"]
    k -->|no| l{"Lockdown?"} -->|yes| r503b["503"]
    l -->|no| b{"IP blocked?"} -->|yes| r403["403"]
    b -->|no| ri{"Per-IP limit?"} -->|over| r429a["429"]
    ri -->|ok| p{"Secret path?"} -->|no| r404["404"]
    p -->|"firm or /regulations"| key{"Valid API key?"} -->|no| r401["401 + count failure"]
    key -->|yes| rk{"Per-key limit?"} -->|over| r429b["429"]
    rk -->|ok| a{"Access state"}
    a -->|ended| msg["Plain 'access ended' message"]
    a -->|ok / expiring / grace| tool["Run tool<br/>(+ notice if expiring)"]
```

## Tools

Two servers in one process (ADR 0015): **firm** at `/mcp/<secret>`, **regulations** at `/mcp/<secret>/regulations`. Same keys, same Gateway.

| Tool | Server | Reads | Demo moment |
|---|---|---|---|
| `list_jobs` | firm | jobs, emails | 1 |
| `get_job` | firm | jobs, emails, attachments, facts, contract terms | 2 |
| `search_job_documents` | firm | emails, attachments | 2 |
| `list_missing_items` | firm | required items, attachments, facts | 3 |
| `search_regulations` | regulations | corpus or fallback | 4, 7 |
| `get_payment_dates` | firm | contract terms | 7 |
| `sync_inbox` | firm | mail source (demo folder; Gmail planned), stores and files emails | 1 |
| `save_facts` | firm | writes job, document types and facts after server checks | 1 |
| `verify_answer` | firm | read-only checks on a draft answer (agent contracts) | all |
| `lookup_terms` | both | Romanian <-> English glossary lookup (ADR 0012) | all (Romanian) |
| `about_regulations_library` | regulations | corpus stats and documents (live) + `regulations_fallback/library.json` (built from `corpus/sources.yaml` by `python -m system.rag.library`) | "what does the library cover?", empty searches (S100) |
| `get_firm_profile` | firm | live firm context: people, jobs, contacts, due in 14 days | start of every conversation |
| `get_job_timeline` | firm | emails received and sent, documents, dated facts, upcoming | delays, "what have I sent" |

## Data

Tables and stores: [data design](data/design.md).

## Deployment (ADR 0009; code in `deploy/`, live since 20 Nov 2026)

```mermaid
flowchart TB
    internet(["Internet"]) -->|"80, 443 only"| caddy
    subgraph aws["AWS eu-west-2, own VPC"]
        subgraph ec2["EC2 t4g.medium, encrypted disk, no SSH"]
            caddy["Caddy<br/>HTTPS"] --> app["MCP server<br/>non-root, read-only"]
            app --> pg[("Postgres<br/>app user: no DDL")]
        end
        ssm["Parameter Store<br/>secrets"] --> ec2
        dlm["Daily snapshots, 7 kept"] --> ec2
        alarm["Alarm: server down → email"] --> ec2
        budget["Budget alarm"]
    end
    admin(["Florin"]) -->|"Session Manager"| ec2
    gha["GitHub Actions"] -->|"OIDC role,<br/>Run Command"| ec2
```

## Upgrade

```mermaid
flowchart LR
    v["version"] --> b["build image<br/>(tag = commit)"] --> bk["backup"] --> m["migrate"] --> r["restart"] --> h{"healthy?"}
    h -->|yes| done["record version"]
    h -->|no| rb["restore DB if migrated,<br/>previous image back"]
```

## Rules this design keeps

- No chat model on the server (ADR 0006).
- Every tool call: one trace row with tool version and sources.
- Texts versioned, never edited in place.
- Retries only for retryable errors. Users see plain errors, never stack traces.
- Every shortcut in the [parking lot](../../requirements/parking-lot.md).
