-- 0002: API keys per firm and server flags (kill switch). ADR 0007. 20 Nov 2026.

create table api_keys (
    id            uuid primary key default gen_random_uuid(),
    firm_id       uuid not null references firms(id) on delete cascade,
    label         text not null,                 -- who or what uses it, e.g. "Dan, Claude app"
    key_prefix    text not null unique,          -- first characters, for lookup and display
    key_hash      text not null,                 -- HMAC-SHA256 of the full key; the key itself is never stored
    expires_on    date not null,                 -- "paid until"
    grace_days    int not null default 7 check (grace_days between 0 and 60),
    revoked_at    timestamptz,
    created_at    timestamptz not null default now(),
    last_used_at  timestamptz
);
create index api_keys_firm_idx on api_keys (firm_id);

create table server_flags (
    name        text primary key,
    value       text not null,
    updated_at  timestamptz not null default now()
);
