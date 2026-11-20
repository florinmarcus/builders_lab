# Sequences: server

Step-by-step flows for [design/server.md](../design/server.md). Updated 20 Nov 2026.

## 1. A tool call (built)

```mermaid
sequenceDiagram
    actor U as Builder
    participant C as Claude app
    participant G as Gateway
    participant M as MCP layer
    participant T as Tool wrapper
    participant S as Service
    participant DB as Postgres

    U->>C: "What's missing on Elm Avenue?"
    C->>G: POST /mcp/<secret> + API key
    G->>DB: check key (hash, expiry, revoked)
    DB-->>G: firm, access state
    G->>M: request (caller set)
    M->>T: list_missing_items(job)
    T->>DB: quota +1 (or refuse)
    T->>S: run for this firm
    S->>DB: items, documents, facts
    DB-->>S: rows
    S-->>T: result + sources
    T->>DB: trace row (version, sources, latency)
    T-->>C: result + AI notice + untrusted-content notice
    C-->>U: answer with citations
```

## 2. New emails: sync and save facts (planned, ADR 0006)

```mermaid
sequenceDiagram
    participant SCH as Claude Code schedule<br/>or user "check my emails"
    participant C as Claude
    participant T as Our tools
    participant GM as Gmail API
    participant DB as Postgres

    SCH->>C: run sync
    C->>T: sync_inbox()
    T->>GM: new messages with label
    GM-->>T: emails + attachments
    T->>T: PDF to text
    T->>DB: upsert emails, attachments
    T-->>C: unfiled emails with text
    C->>C: read, decide job and facts
    C->>T: save_facts(job, facts, quotes)
    T->>T: check job exists, source exists,<br/>quote appears in source
    T->>DB: save facts (or reject with reason)
    T-->>C: saved / rejected
```

## 3. Expired key (built)

```mermaid
sequenceDiagram
    participant C as Claude app
    participant G as Gateway
    participant T as Tool wrapper

    C->>G: request + key
    alt within 14 days of expiry or in grace
        G->>T: caller (expiring / grace)
        T-->>C: result + "access ends on ..., contact Florin"
    else past grace
        G->>T: caller (ended)
        T-->>C: "Your access ended on ... Contact Florin." (no data)
    else revoked or unknown
        G-->>C: 401, failure counted
    end
```

## 4. Upgrade (planned, ADR 0008)

```mermaid
sequenceDiagram
    participant CI as GitHub Actions
    participant SRV as Server (upgrade.sh)
    participant DB as Postgres

    CI->>SRV: run upgrade to version X (OIDC)
    SRV->>DB: backup
    SRV->>SRV: pull image X
    SRV->>DB: migrate
    SRV->>SRV: restart, health check
    alt healthy
        SRV-->>CI: done
    else not healthy
        SRV->>SRV: previous image back
        SRV->>DB: restore backup if migration ran
        SRV-->>CI: rolled back
    end
```
