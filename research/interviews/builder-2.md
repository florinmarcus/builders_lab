# Builder 2: design-and-build firm, receives designs from others

Written questions from Florin, answered in writing by the owner before a site visit (answers received 27 Nov 2026). Anonymised: no names. Answers translated from Romanian; his own words in brackets.

## Tools today

| Area | What he uses | His words |
|---|---|---|
| Email | Microsoft 365 (Outlook), now bought directly from Microsoft. Was through GoDaddy before | "Ne-am mutat de la GoDaddy, suntem direct la microsoft" |
| Admin access to Microsoft 365 | Thinks he can get it. Not confirmed | "pot lua accesul la contul de administrator (cred)" |
| Files and documents | Dropbox | "Dropbox" |
| Accounts and invoices | No software | "nu folosim" |
| Quotes and project management | Excel, and recently Monday.com | "Excel si mai nou Monday.com" |
| Talking to crews and clients | Email and WhatsApp | "Email si Whats App" |
| Plans and drawings | Receives them, does no design in-house | "noi le primim, nu facem design" |
| Health and safety (RAMS, risk assessments) | Has an outside H&S adviser | "avem un H&S Advisor" |

## What this suggests (our inference, not his words)

- Our demo runs on Gmail. For him, email means Outlook. The Microsoft 365 connector in Claude looks read-only (`research/integrations/connector-map.md`), so drafting into Outlook would need our own Microsoft Graph server.
- The Xero invoice scenario does not fit him. Someone must still do invoices and payment applications: find out who and how.
- Dropbox has a built-in Claude connector that reads and writes.
- Monday.com is not yet in our connector map. Check how it connects to Claude.
- WhatsApp and email with clients fit the "client said yes on WhatsApp" variations scenario.
- H&S paperwork sits with an outside adviser, so RAMS checks may matter less to him in-house.

## Follow-up questions (for the visit)

- Who holds the Microsoft 365 admin account?
- Who does invoices and payment applications, and in what (Excel, Word, an accountant)?
- What does he track in Monday.com, and what still lives in Excel?
- What does the H&S adviser send him, and where does it end up (email, Dropbox)?
- Which job emails and documents take the most time to find or answer?
