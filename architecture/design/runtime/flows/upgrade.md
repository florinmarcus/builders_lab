# Flow: upgrade the server

A push to `main` reaching the live server, with automatic rollback. Up: [runtime design](../design.md).
Decision: ADR 0009. Commands and keys: `deploy/README.md`.

```mermaid
flowchart LR
    push(["push to main"]) --> ci["1. CI<br/>.github/workflows/ci-deploy.yml<br/>tests, version lock"]
    ci --> run["2. Run Command<br/>OIDC role"]
    run --> up["3. upgrade.sh<br/>settings from Parameter Store"]
    up --> b["4. build image<br/>tag = commit"]
    b --> bk["5. backup.sh"]
    bk --> m["6. migrate"]
    m --> r["7. restart, health check"]
    r -->|"healthy"| done(["version recorded"])
    r -->|"not healthy"| rb(["rollback.sh: previous image,<br/>restore DB if migrated"])
```

- All scripts are in `deploy/scripts/`. The app user cannot change the schema.
- Settings are read from Parameter Store on every upgrade, so new flags such as `rag_enabled` take effect.
