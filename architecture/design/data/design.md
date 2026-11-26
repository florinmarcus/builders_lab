# Data design

Where every kind of data lives, and the shape of the two stores: the regulations library and the firm data.
Up: [architecture](../../ARCHITECTURE.md). Updated 26 Nov 2026. Solid = built. Dashed = planned.

Source of truth for columns: the code, not this file.
- Firm tables: `system/api/builders_api/db/migrations/` (add a file, never edit one).
- Regulations tables: `DDL` in `system/rag/load.py`.
- Corpus file formats: `system/rag/README.md` and `corpus/README.md`.

## 1. Where data lives

```mermaid
flowchart LR
    subgraph git["Git (this repo)"]
        cat["corpus catalogue<br/>sources.yaml, versions/, fixes/"]
        gl["glossary<br/>research/domain/glossary.md<br/>→ terminology/glossary.json"]
        ver["prompts, tool texts<br/>versions/*.vN.md + lock"]
        gold["eval questions<br/>evals/golden/"]
        mock["mock firm<br/>system/data/mock/"]
    end

    subgraph aws["AWS London"]
        s3[("S3<br/>raw corpus files")]
        subgraph ec2["EC2 server"]
            firmdb[("firm Postgres<br/>firm tables")]
            corpdb[("corpus-db<br/>Postgres + pgvector<br/>corpus schema")]
        end
        ssm["Parameter Store<br/>secrets, flags"]
        snap["disk snapshots<br/>7 days"]
    end

    local["build machine<br/>corpus/raw, parsed,<br/>chunks, vectors<br/>(not in git)"]

    cat --> local
    s3 <--> local
    local -->|"load.py"| corpdb
    mock -->|"seed SQL"| firmdb
    gl -.->|"read by the server"| ec2
    ver -.->|"read by the server"| ec2
    ec2 -.-> snap
```

| Store | Holds | Who writes | Who reads |
|---|---|---|---|
| Firm Postgres | one firm's jobs, emails, documents, facts; keys, traces, quotas | firm server tools (`sync_inbox`, `save_facts`), seed SQL | firm server only, every query filtered by firm |
| corpus-db | regulations chunks with vectors and keywords | `system/rag/load.py` as the owner login | regulations server as `builders_corpus_reader` (SELECT only) |
| S3 | raw PDF, HTML, XML, by hash | `system/rag/harvest` | parse step on a build machine |
| Git | catalogue, saved model fixes, glossary, versioned texts, eval questions, mock data | us | code and tests |
| Parameter Store | secrets, path secret, `rag_enabled` and other flags | `install.sh`, Florin | server at start-up |

Rules: no real firm data in git (mock only). No corpus text in git: only the catalogue and fixes. Secrets only in
Parameter Store. The regulations server has no connection to the firm database (ADR 0015).

## 2. Regulations library

One document goes from catalogue to searchable chunk. Each step's output is rebuilt from the step before, so only
the catalogue, the fixes and the raw files need keeping. How each step works: [ingest design](../ingest/design.md).

```mermaid
erDiagram
    SOURCE ||--o{ VERSION : "has"
    VERSION ||--|| RAW_FILE : "stored as"
    VERSION ||--o| TREE : "parsed into"
    VERSION ||--o{ FIX : "model fixes"
    TREE ||--o{ CHUNK : "split into"
    CHUNKS_TABLE ||--o{ LEXEMES : "keyword stats"

    SOURCE { text id "adb, br2010, hse-hsg264" text kind "legislation, approved-document, guidance" text mode "ingest, restricted, link_only" text licence }
    VERSION { text version_id text edition_date date valid_from date valid_to "empty = in force" text sha256 text s3_key }
    RAW_FILE { text path "S3, by hash" }
    TREE { json sections "heading path, page, tables, figures" json checks "open decisions" }
    FIX { text fingerprint "content it is about" text result }
    CHUNK { text id text section_id text chunk_type text text text embed_text "breadcrumb + text" json references }
    CHUNKS_TABLE { text id PK text source_id text legal_weight date valid_from date valid_to text applies_to text url vector embedding "1024, Titan V2" tsvector tsv "BM25" tsvector codes_tsv "7.6.3 kept whole" jsonb meta "references, terms, figures" }
    LEXEMES { text lexeme text field int df }
```

- **Files:** SOURCE is `corpus/sources.yaml`. VERSION is one JSON record in `corpus/versions/`. FIX is
  `corpus/fixes/<source>.json`. These three are in git. TREE (`corpus/parsed/`) and CHUNK (`corpus/chunks/`) are
  rebuilt and not in git.
- **Database:** only three tables in schema `corpus`: `chunks`, `lexemes` (word counts for BM25) and `stats` (load
  record). A chunk row holds every filter field, so search needs no joins. References, terms and figure data sit in
  `meta`, not in their own tables.
- **Scope:** only versions in force on or after 1 January 2025 are chunked and loaded (ADR 0016, `in_scope` in
  `system/rag/corpus.py`).
- **Planned:** full section text for `get_section`, and whole documents for `read_document` (ADR 0016).

## 3. Firm data

One database per server, every row tagged with its firm. Mock firm: Marcus Limited.

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
    firms ||--o{ quota_usage : uses
    firms |o--o{ traces : "logged for"
    versions |o--o{ traces : "text version used"

    jobs { uuid id PK text ref "per firm, e.g. ELM-22" date target_date text_arr match_terms "words that file an email" }
    emails { uuid id PK text gmail_message_id timestamptz sent_at text ingest_status timestamptz facts_done_at tsvector search }
    attachments { uuid id PK text document_type date expires_on text text_content tsvector search }
    facts { uuid id PK text fact_type "approval, variation, key_date" text quote "exact words" jsonb value text prompt_version }
    contract_terms { uuid id PK text party "main or subcontract" int final_date_days_after_due int pay_less_days_before_final }
    required_items { text code text_arr satisfied_by }
    api_keys { text key_prefix UK text key_hash "HMAC, never the key" date expires_on timestamptz revoked_at }
    traces { uuid trace_id text kind "tool or model" text name text version_id FK jsonb sources int latency_ms }
```

- **Business data:** `firms`, `staff`, `clients`, `jobs`, `contract_terms`, `emails`, `attachments`, `facts`.
  `job_types` and `required_items` are shared reference lists (what each kind of job needs before handover).
- **Server data:** `api_keys` (ADR 0007), `traces` (one row per tool call), `versions` (which prompt or tool text
  was live), `quota_limits` and `quota_usage`, `gmail_sync_state`, `server_flags` (kill switch),
  `schema_migrations`.
- **Facts carry their proof.** Every fact links to an email or attachment and keeps the exact quote. `save_facts`
  checks the quote is in the source before saving (ADR 0006).
- **Planned:** workflow run records, so tools can refuse steps out of order (ADR 0017, parking lot N21).
