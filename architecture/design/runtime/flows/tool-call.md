# Flow: a tool call

One MCP request through security, the tool wrapper and the service layer. Up: [runtime design](../design.md).
Security decision: ADR 0007.

```mermaid
flowchart TB
    req(["HTTPS request<br/>via Caddy"]) --> g1{"1. Gateway.__call__<br/>health, kill switch,<br/>lockdown, IP block"}
    g1 -->|"/healthz"| ok(["200"])
    g1 -->|"off or locked"| r503(["503"])
    g1 -->|"blocked"| r403(["403"])
    g1 --> g2{"2. rate limit per IP<br/>secret path?"}
    g2 -->|"over"| r429(["429"])
    g2 -->|"unknown path"| r404(["404"])
    g2 --> g3{"3. security.check_key()<br/>hash, expiry, revoked"}
    g3 -->|"no"| r401(["401, failure counted"])
    g3 --> rt["4. _Router<br/>firm or regulations server"]
    rt --> wrap{"5. run_tool()<br/>access state"}
    wrap -->|"ended"| ended(["plain 'access ended' message"])
    wrap --> q["6. quotas.consume()<br/>then the service function"]
    q --> tr["7. tracing.write()<br/>version, sources, latency"]
    tr --> res(["8. result + trace_id,<br/>access and untrusted notices"])
```

- **Steps 1 to 3** are in `mcp_server/gateway.py` and `security.py`. Too many failures from one IP block it; too
  many overall start a lockdown (`security.Guard`).
- **The key decides the firm.** `check_key()` returns a `Caller` with the firm and access state: ok, expiring
  (within 14 days), grace, or ended.
- **Steps 5 to 8** are `run_tool()` in `mcp_server/server.py`. An `AppError` becomes a plain error with a code;
  anything else is logged and returned as `internal_error` with the trace id.
