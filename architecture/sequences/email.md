# Sequences: how email reaches the assistant

What happens when Florin says "check my emails" ("Verifică mail-urile"). Up: [server flows](server.md), [architecture](../ARCHITECTURE.md). Updated 20 Nov 2026.

## The parts

```mermaid
flowchart LR
    mailcom(["Florin's mail.com<br/>(plays council, client, staff)"]) -->|"sends to<br/>florin.marcus+council@gmail.com"| gmail[("Florin's Gmail")]
    sim["Simulator<br/>(on our server)"] -->|"every 10 s: rewrites as the person,<br/>adds label marcus-limited,<br/>bins the original"| gmail
    loader["gmail_demo.py load<br/>(laptop, once)"] -->|"21 past emails,<br/>label marcus-limited"| gmail
    feed["Demo mail folder<br/>(on our server)"] --> server
    gmail -->|"Gmail API: label<br/>marcus-limited ONLY"| server["Our MCP server<br/>sync_inbox"]
    server --> db[("Postgres:<br/>emails, documents, facts")]
    claude["Claude app<br/>(phone)"] -->|"sync_inbox, save_facts"| server
    claude -.->|"Claude's own Gmail connector:<br/>whole inbox, drafts"| gmail
```

## "Check my emails", step by step

```mermaid
sequenceDiagram
    actor F as Florin (phone)
    participant C as Claude app
    participant S as Our server (sync_inbox)
    participant G as Gmail (label marcus-limited)
    participant DB as Postgres

    F->>C: "Verifică mail-urile, te rog"
    C->>S: sync_inbox()
    S->>G: list emails with label marcus-limited
    G-->>S: emails + attachments
    S->>S: skip ones already stored (same Message-ID)
    S->>S: PDF to text, file by job (words, sender history)
    S->>DB: store new emails and documents
    S-->>C: counts + new emails needing facts (text, ids)
    loop each new email
        C->>S: save_facts(job, document types, facts with exact quotes)
        S->>S: check quotes are really in the email
        S->>DB: save facts
    end
    C-->>F: "2 new: Sam Price (council) asks you to confirm 27 Nov, Mike says the kitchen cannot start"
```

## A live email from the "council"

```mermaid
sequenceDiagram
    actor F as Florin (mail.com)
    participant G as Gmail
    participant SIM as Simulator (server)
    participant S as Our server
    F->>G: email to florin.marcus+contracts@gmail.com
    Note over G: arrives from mail.com, no label yet:<br/>our server does not see it
    SIM->>G: every 10 s: new email from an allowed sender?
    SIM->>G: import copy "from Sam Price, Contract Manager", label marcus-limited
    SIM->>G: move the mail.com original to Bin
    Note over G,S: from now on sync_inbox picks it up
```

## Good to know

- Our server reads **only** the `marcus-limited` label, never the rest of the inbox (ADR 0005).
- Ask "check my emails" **after** the email shows under the label (about 10 to 20 seconds after sending).
- Claude's own Gmail connector can also read the inbox and write drafts; our tools do the filing, facts and checks.
- The demo mail folder on the server is a second source used for resets; Gmail and the folder never double-count (same Message-ID).
