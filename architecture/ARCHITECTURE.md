# Architecture

Builders Lab: an AI assistant that works where a builder's work already is. High level only. Details: [designs](#map).

Updated 20 Nov 2026. Solid lines = built. Dashed lines = planned.

## 1. Who talks to what

```mermaid
flowchart LR
    builder(["Builder<br/>(phone or web)"])
    dev(["Florin and testers"])

    subgraph claude["Claude (the agents live here, ADR 0006)"]
        app["Claude app"]
        code["Claude Code<br/>harness, subagents,<br/>scheduled sync"]
    end

    subgraph ours["Our system (AWS, London)"]
        mcp["MCP server<br/>tools + security"]
        db[("Postgres<br/>firm data")]
        rag["Regulations search<br/>(corpus session)"]
    end

    gmail["Gmail"]
    xero["Xero"]

    builder --> app
    dev --> code
    app -->|"Gmail connector"| gmail
    app -->|"Xero connector"| xero
    app -->|"our connector<br/>API key"| mcp
    code -->|"same connector"| mcp
    mcp --> db
    mcp --> rag
    mcp -.->|"Gmail API (sync)"| gmail
```

## 2. Where things run

```mermaid
flowchart TB
    subgraph gh["GitHub"]
        repo["Repo: code, docs, deploy scripts"]
        ci["Actions pipeline"]
    end

    subgraph aws["AWS eu-west-2 (live since 20 Nov 2026; ADR 0009)"]
        subgraph ec2["EC2 server (Docker)"]
            caddy["Caddy<br/>HTTPS"] --> app["MCP server"] --> pg[("Postgres")]
        end
        ssm["Parameter Store<br/>secrets"]
        backup["Backups"]
        bedrock["Bedrock<br/>embedder, re-ranker<br/>(corpus only)"]
        s3["S3<br/>corpus files"]
    end

    repo --> ci
    ci -.->|"OIDC, no stored keys"| ec2
    app -.-> ssm
    pg -.-> backup
    app -.-> bedrock
    app -.-> s3
```

## 3. Where the intelligence is

```mermaid
flowchart LR
    q["Question or<br/>new emails"] --> claude["Claude<br/>(user's plan)"]
    claude -->|"reads, extracts,<br/>writes drafts"| tools["Our tools"]
    tools -->|"facts, search,<br/>date sums"| claude
    tools --> code["Plain code:<br/>no chat model<br/>on our server"]
```

## Map

| Level | Document |
|---|---|
| Design | [Server: MCP, security, data, deployment](design/server.md) |
| Design | [Regulations corpus and search](design/regulations-corpus.md) (corpus session) |
| Sequences | [Server flows](sequences/server.md) |
| Decisions | [ADRs](../decisions/) |
| Gaps | [Parking lot](../requirements/parking-lot.md) |
