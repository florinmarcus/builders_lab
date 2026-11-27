# Builder 2: where each document lives (first draft, 27 Nov 2026)

![Where documents live](builder-2-documents.png)

Draft to check with the owner. Green: he told us (`builder-2.md`). "?": our guess. Dashed line: no connector, or not checked. Connector facts from `research/integrations/connector-map.md` (checked 19 Nov 2026); Monday.com not checked yet.

```mermaid
flowchart TD
    subgraph FIRM["His tools (his accounts)"]
        OUT["Outlook (Microsoft 365)<br/>client and designer emails<br/>? subcontractor insurance, RAMS"]:::known
        DBX["Dropbox<br/>drawings<br/>? contracts, Excel quotes,<br/>old RAMS, handover docs"]:::known
        MON["Monday.com<br/>job plans and tasks"]:::known
        WA["WhatsApp<br/>client changes, crew chats"]:::known
        HS["H&S adviser<br/>writes RAMS<br/>? sends by email"]:::known
    end

    subgraph CLAUDE["Claude Team plan (his firm)"]
        PL["Builders plugin<br/>skills and checks"]
    end

    subgraph OURS["Our servers"]
        FS["Firm server<br/>job index, facts, dates"]
        RG["Regulations library<br/>same for every firm"]
    end

    OUT -- "Microsoft 365 connector<br/>read only, admin consent" --> PL
    DBX -- "Dropbox connector<br/>read and write" --> PL
    MON -. "? connector, not checked" .-> PL
    WA -. "no connector<br/>paste chat export" .-> PL
    HS -.-> OUT
    PL -- "BuildersMCP, his key" --> FS
    PL -- "BuildersRegulations" --> RG

    classDef known fill:#d9f2e3,stroke:#2e7d4f,color:#000
    classDef guess fill:#fff4d6,stroke:#b8860b,color:#000,stroke-dasharray: 5 5
```

## Open points

- His real documents stay in his tools. Our firm server keeps only the job index, facts and dates.
- Outlook: the connector looks read-only, so drafts would need our own Microsoft Graph server.
- Monday.com: check whether Claude has a connector for it.
- WhatsApp: no way to read existing chats; a pasted export for now.
