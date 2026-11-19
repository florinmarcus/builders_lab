-- 0001: first schema for the demo (19 Nov 2026).
-- Never edit an applied migration. Add a new numbered file instead.

create extension if not exists pgcrypto;  -- gen_random_uuid()

-- ---------------------------------------------------------------- firm data

create table firms (
    id          uuid primary key default gen_random_uuid(),
    slug        text not null unique,
    name        text not null,
    created_at  timestamptz not null default now()
);

create table staff (
    id       uuid primary key default gen_random_uuid(),
    firm_id  uuid not null references firms(id) on delete cascade,
    name     text not null,
    role     text not null,
    email    text
);

create table clients (
    id       uuid primary key default gen_random_uuid(),
    firm_id  uuid not null references firms(id) on delete cascade,
    name     text not null,
    kind     text not null check (kind in ('private', 'commercial', 'council')),
    email    text,
    phone    text
);

-- Job types and their required items are shared reference data (mock list, not a legal rule).
create table job_types (
    code  text primary key,
    name  text not null
);

create table required_items (
    id              uuid primary key default gen_random_uuid(),
    job_type_code   text not null references job_types(code) on delete cascade,
    code            text not null,
    label           text not null,
    -- document types (attachments.document_type) or fact types (facts.fact_type) that satisfy this item
    satisfied_by    text[] not null,
    sort_order      int not null default 0,
    unique (job_type_code, code)
);

create table jobs (
    id             uuid primary key default gen_random_uuid(),
    firm_id        uuid not null references firms(id) on delete cascade,
    client_id      uuid references clients(id) on delete set null,
    job_type_code  text not null references job_types(code),
    ref            text not null,                 -- short name, e.g. ELM-22
    title          text not null,
    address        text not null,
    status         text not null default 'active' check (status in ('active', 'complete', 'on_hold')),
    start_date     date,
    target_date    date,
    match_terms    text[] not null default '{}',  -- words that link an email to this job
    unique (firm_id, ref)
);

-- Payment terms per contract on a job (main contract or a subcontract). Our code does the date sums.
create table contract_terms (
    id                             uuid primary key default gen_random_uuid(),
    firm_id                        uuid not null references firms(id) on delete cascade,
    job_id                         uuid not null references jobs(id) on delete cascade,
    party                          text not null check (party in ('main', 'subcontract')),
    counterparty                   text not null,
    contract_form                  text,           -- e.g. "JCT Intermediate Building Contract 2016"
    valuation_day_of_month         int check (valuation_day_of_month between 1 and 31),
    due_days_after_valuation       int,
    due_day_of_month               int check (due_day_of_month between 1 and 31),
    final_date_days_after_due      int not null,
    payment_notice_days_after_due  int not null,
    pay_less_days_before_final     int not null,
    source_attachment_id           uuid,           -- set after attachments exist (fk below)
    check (valuation_day_of_month is not null or due_day_of_month is not null)
);

-- ---------------------------------------------------------------- email and documents

create table emails (
    id                 uuid primary key default gen_random_uuid(),
    firm_id            uuid not null references firms(id) on delete cascade,
    gmail_message_id   text not null,
    gmail_thread_id    text,
    from_name          text,
    from_address       text,
    to_addresses       text[] not null default '{}',
    subject            text not null default '',
    sent_at            timestamptz not null,
    body_text          text not null default '',
    job_id             uuid references jobs(id) on delete set null,
    filing_reason      text,                      -- why it was linked to this job (or not)
    ingest_status      text not null default 'pending' check (ingest_status in ('pending', 'done', 'failed')),
    ingest_error       text,
    ingest_attempts    int not null default 0,
    ingested_at        timestamptz,
    search             tsvector generated always as (
                           setweight(to_tsvector('english', coalesce(subject, '')), 'A') ||
                           setweight(to_tsvector('english', coalesce(from_name, '')), 'B') ||
                           setweight(to_tsvector('english', coalesce(body_text, '')), 'C')
                       ) stored,
    unique (firm_id, gmail_message_id)
);
create index emails_job_idx    on emails (job_id);
create index emails_sent_idx   on emails (firm_id, sent_at desc);
create index emails_search_idx on emails using gin (search);

create table attachments (
    id                    uuid primary key default gen_random_uuid(),
    firm_id               uuid not null references firms(id) on delete cascade,
    email_id              uuid not null references emails(id) on delete cascade,
    filename              text not null,
    mime_type             text not null,
    size_bytes            int,
    sha256                text not null,
    page_count            int,
    text_content          text not null default '',
    job_id                uuid references jobs(id) on delete set null,
    document_type         text,                    -- e.g. quote, works_order, asbestos_survey, insurance_certificate, chat_export
    document_date         date,
    expires_on            date,                    -- insurance, certificates
    search                tsvector generated always as (
                              setweight(to_tsvector('english', coalesce(filename, '')), 'A') ||
                              setweight(to_tsvector('english', coalesce(text_content, '')), 'C')
                          ) stored,
    unique (email_id, sha256)
);
create index attachments_job_idx    on attachments (job_id);
create index attachments_search_idx on attachments using gin (search);
create index attachments_expiry_idx on attachments (firm_id, expires_on) where expires_on is not null;

alter table contract_terms
    add constraint contract_terms_source_fk
    foreign key (source_attachment_id) references attachments(id) on delete set null;

-- Facts extracted by the model. Each one points back to its source for citations.
create table facts (
    id              uuid primary key default gen_random_uuid(),
    firm_id         uuid not null references firms(id) on delete cascade,
    job_id          uuid references jobs(id) on delete set null,
    email_id        uuid references emails(id) on delete cascade,
    attachment_id   uuid references attachments(id) on delete cascade,
    fact_type       text not null,                 -- e.g. approval, variation, key_date, amount, asbestos_item, certificate_pending
    summary         text not null,
    quote           text,                          -- exact words from the source
    value           jsonb not null default '{}',   -- structured detail (amount, room, material, result ...)
    fact_date       date,
    source_page     int,
    prompt_version  text not null,
    trace_id        uuid,
    created_at      timestamptz not null default now(),
    check (email_id is not null or attachment_id is not null)
);
create index facts_job_idx  on facts (job_id, fact_type);
create index facts_email_idx on facts (email_id);
create index facts_attachment_idx on facts (attachment_id);

-- ---------------------------------------------------------------- versions, traces, quotas

-- Every prompt, server instruction and tool description has a version id. Text lives in the repo;
-- the hash here catches in-place edits (same id, different text).
create table versions (
    id          text primary key,                  -- e.g. extract_email.v1
    kind        text not null check (kind in ('prompt', 'server_instructions', 'tool_description')),
    name        text not null,
    sha256      text not null,
    created_at  timestamptz not null default now()
);

-- One row per model call and per tool call.
create table traces (
    id              bigint generated always as identity primary key,
    trace_id        uuid not null,
    span_id         uuid not null default gen_random_uuid(),
    parent_span_id  uuid,
    firm_id         uuid references firms(id) on delete set null,
    kind            text not null check (kind in ('model', 'tool')),
    name            text not null,                 -- tool name or model purpose
    model_id        text,
    version_id      text references versions(id),
    input_tokens    int,
    output_tokens   int,
    cost_usd        numeric(12, 6),
    latency_ms      int,
    status          text not null check (status in ('ok', 'error')),
    error_type      text,
    sources         jsonb not null default '[]',   -- ids and labels of emails, documents, regulation passages returned
    started_at      timestamptz not null default now()
);
create index traces_trace_idx on traces (trace_id);
create index traces_firm_idx  on traces (firm_id, started_at desc);

create table quota_limits (
    firm_id      uuid not null references firms(id) on delete cascade,
    metric       text not null check (metric in ('documents_ingested', 'tool_calls', 'bedrock_usd')),
    daily_limit  numeric(12, 4) not null check (daily_limit >= 0),
    primary key (firm_id, metric)
);

create table quota_usage (
    firm_id  uuid not null references firms(id) on delete cascade,
    metric   text not null check (metric in ('documents_ingested', 'tool_calls', 'bedrock_usd')),
    day      date not null,
    used     numeric(12, 4) not null default 0,
    primary key (firm_id, metric, day)
);

-- Gmail sync position per firm, so sync_inbox only fetches what is new.
create table gmail_sync_state (
    firm_id          uuid primary key references firms(id) on delete cascade,
    last_history_id  text,
    last_synced_at   timestamptz
);
