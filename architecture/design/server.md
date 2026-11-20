# Design: server

MCP server, security, data and deployment. Code: `system/api/`. Flows: [sequences/server.md](../sequences/server.md). Up: [architecture](../ARCHITECTURE.md).

Updated 20 Nov 2026. Solid = built. Dashed = planned.

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
        svc -.-> inbox["inbox<br/>(sync, save facts)"]
        ver["versions<br/>(texts + lock)"] --> mcp
        ver --> tools
    end

    jobs & docs & pay & inbox --> pg[("Postgres")]
    tools --> pg
    regs --> rag["rag.search<br/>(corpus)"]
    regs --> fb["fallback<br/>7 passages"]
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
    p -->|yes| key{"Valid API key?"} -->|no| r401["401 + count failure"]
    key -->|yes| rk{"Per-key limit?"} -->|over| r429b["429"]
    rk -->|ok| a{"Access state"}
    a -->|ended| msg["Plain 'access ended' message"]
    a -->|ok / expiring / grace| tool["Run tool<br/>(+ notice if expiring)"]
```

## Tools

| Tool | Reads | Demo moment |
|---|---|---|
| `list_jobs` | jobs, emails | 1 |
| `get_job` | jobs, emails, attachments, facts, contract terms | 2 |
| `search_job_documents` | emails, attachments | 2 |
| `list_missing_items` | required items, attachments, facts | 3 |
| `search_regulations` | corpus or fallback | 4, 7 |
| `get_payment_dates` | contract terms | 7 |
| `sync_inbox` | Gmail (planned) | 1 |
| `save_facts` (planned) | writes facts | 1 |

## Data (database state)

```mermaid
erDiagram
    firms ||--o{ staff : employs
    firms ||--o{ clients : has
    firms ||--o{ jobs : runs
    clients ||--o{ jobs : orders
    job_types ||--o{ jobs : "type of"
    job_types ||--o{ required_items : needs
    jobs ||--o{ contract_terms : "paid under"
    firms ||--o{ emails : receives
    jobs |o--o{ emails : "filed to"
    emails ||--o{ attachments : carries
    jobs |o--o{ attachments : "filed to"
    attachments |o--o{ contract_terms : "source of"
    emails |o--o{ facts : "source of"
    attachments |o--o{ facts : "source of"
    jobs |o--o{ facts : about
    firms ||--o{ api_keys : holds
    firms ||--o{ quota_limits : "limited by"
    firms ||--o{ quota_usage : uses
    firms ||--o| gmail_sync_state : "synced to"
    firms |o--o{ traces : "logged for"
    versions |o--o{ traces : "version used"

    firms { uuid id PK
        text slug UK
        text name }
    jobs { uuid id PK
        text ref UK "per firm"
        text job_type_code FK
        date target_date
        text_arr match_terms }
    emails { uuid id PK
        text gmail_message_id UK "per firm"
        timestamptz sent_at
        uuid job_id FK
        text ingest_status
        tsvector search }
    attachments { uuid id PK
        text document_type
        date document_date
        date expires_on
        tsvector search }
    facts { uuid id PK
        text fact_type
        text quote "exact words"
        jsonb value
        text prompt_version }
    contract_terms { uuid id PK
        text party "main or subcontract"
        int due_day_of_month
        int final_date_days_after_due
        int pay_less_days_before_final }
    required_items { text code
        text_arr satisfied_by }
    api_keys { uuid id PK
        text key_prefix UK
        text key_hash "HMAC, never the key"
        date expires_on
        timestamptz revoked_at }
    traces { bigint id PK
        uuid trace_id
        text kind "tool or model"
        text version_id FK
        numeric cost_usd
        jsonb sources }
    versions { text id PK
        text kind
        text sha256 }
    quota_usage { text metric
        date day
        numeric used }
```

Also: `schema_migrations` (applied files and hashes), `server_flags` (kill switch).

## Deployment (ADR 0008; code in `deploy/`, not yet run in AWS)

```mermaid
flowchart TB
    internet(["Internet"]) -->|"80, 443 only"| caddy
    subgraph aws["AWS eu-west-2, own VPC"]
        subgraph ec2["EC2 t4g.small, encrypted disk, no SSH"]
            caddy["Caddy<br/>HTTPS"] --> app["MCP server<br/>non-root, read-only"]
            app --> pg[("Postgres<br/>app user: no DDL")]
        end
        ssm["Parameter Store<br/>secrets"] --> ec2
        dlm["Daily snapshots, 7 kept"] --> ec2
        alarm["Alarm: auto-recover + email"] --> ec2
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
