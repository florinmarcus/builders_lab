# 0007: MCP server security: API keys now, OAuth next, hardening from day one

Date: 20 Nov 2026. Status: accepted.
Changed by: 0015 (one key for both servers).

## Context

The MCP server will be on the public internet. Bots scan for MCP servers. Users are builders, not technical, so security must not ask them to manage keys. The Claude app accepts a fixed header credential, OAuth, or no login for a custom connector (`research/hosting-costs/connector-auth-options.md`).

## Decision

Two authentication layers in the end:

1. **API key per firm** (now). Sent in a request header. Stored as a hash, never in plain text. Has an expiry date ("paid until"), a revoked flag and a label. The key tells the server which firm is calling; every query is filtered by that firm.
2. **OAuth per person** (next, with Cognito). The person must belong to the firm of the key. To check: whether the Claude app can send both on one connector. If not, OAuth carries the firm in the app, and API keys serve Claude Code, scripts and the harness.

For non-technical users:

- Renewal moves the expiry date; the key does not change.
- From 14 days before expiry, every tool answer carries a plain warning to contact Florin.
- After expiry, a 7-day grace period with the warning, then every tool returns a plain "your access ended" message instead of data.
- New key only on leak, staff leaving, or a yearly planned rotation.

Hardening built into the server:

- Requests without a valid key are refused before the MCP layer. Unknown paths return 404. The MCP path includes a long random segment.
- An IP is blocked for an hour after 10 failed key checks.
- Rate limits per key, per IP and overall. Small request size limit.
- Automatic lockdown: if total traffic or failed key checks pass a threshold, refuse everything for 15 minutes and alert Florin. Manual kill switch.
- Tools read only (later: `save_facts` writes facts only). No shell, no file access, nothing that sends data out.
- Email and document text in tool results is marked as untrusted content; the server instructions tell Claude to treat it as data, never as instructions (prompt injection).
- With deployment: only HTTPS open, database not reachable from outside, automatic security updates, admin access through AWS Systems Manager (no SSH passwords), database user without rights to drop tables, alerts and an AWS budget alarm.

## Options considered

- **No login, mock data only** (the original demo plan): simplest, but a public MCP server would be found and abused.
- **OAuth only:** short-lived tokens rotate by themselves, but more to build and test before Saturday.
- **Cognito machine-to-machine tokens for firms:** about $0.00225 per token request plus a charge per client; API keys in our own database cost nothing extra.

## Consequences

- Keys are long-lived until OAuth exists. Parked as S16 in `requirements/parking-lot.md`.
- Blocking, rate limits and lockdown live in memory on one server (S7, S17).
- Florin creates, extends and revokes keys with a command on the server.
