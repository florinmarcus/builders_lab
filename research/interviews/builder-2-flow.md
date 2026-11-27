# Builder 2: how a job flows (first draft, 27 Nov 2026)

![Job flow](builder-2-flow.png)

Draft to check with the owner. Solid boxes: tools he named in writing (`builder-2.md`). Dashed boxes: our guesses, to confirm. The order of steps is a guess from typical design-and-build firms (`research/research_notes/Builder tools and integrations/design_and_build_firms.md`).

```mermaid
flowchart TD
    A["Enquiry from client<br/>Email / WhatsApp"]:::known --> B["Survey and brief<br/>? notes where"]:::guess
    B --> C["Drawings arrive from designer<br/>Email / Dropbox"]:::known
    C --> D["Quote<br/>Excel"]:::known
    D --> E["Contract signed<br/>? kept in Dropbox"]:::guess
    E --> F["Job planned<br/>Monday.com"]:::known
    F --> G["Subcontractors booked<br/>? their insurance and RAMS by email"]:::guess
    F --> H["RAMS written<br/>H&S adviser"]:::known
    H --> I["RAMS sent<br/>? to client or main contractor"]:::guess
    G --> J["Build on site<br/>WhatsApp with crews"]:::known
    I --> J
    J --> K["Client asks for changes<br/>WhatsApp / Email"]:::known
    K --> J
    J --> L["Invoices and payments<br/>? Excel or accountant"]:::guess
    J --> M["Handover documents<br/>? Dropbox"]:::guess

    classDef known fill:#d9f2e3,stroke:#2e7d4f,color:#000
    classDef guess fill:#fff4d6,stroke:#b8860b,color:#000,stroke-dasharray: 5 5
```

## Questions the diagram raises

1. Where do survey notes, contracts and old RAMS live: Dropbox?
2. Who asks him for RAMS, and who does he ask (subcontractors)?
3. Who does invoices and payment applications, and in what?
4. What goes in Monday.com, and what stays in Excel?
5. Who holds the Microsoft 365 admin account? (Needed to approve the Outlook connector for the firm.)
