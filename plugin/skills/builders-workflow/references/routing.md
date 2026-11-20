# Routing

| The builder asks about | kind | specialist | main tools |
|---|---|---|---|
| new emails, "what came in", filing | inbox | `inbox-clerk` | sync_inbox, save_facts |
| approved changes, variations, final account | variations | `variations` | get_job, search_job_documents |
| payment notices, pay less, applications, final date | payments | `payments` | get_payment_dates, search_regulations |
| what's missing, handover, subcontractor papers, insurance | paperwork | `paperwork` | list_missing_items, get_job |
| running late, extensions, damages, "what have I sent", who to tell | delays | `delays` | get_job_timeline, get_job, search_job_documents |
| building regulations, building control, asbestos rules, CDM, the law | regulations | `regulations` | search_regulations |
| "what's on this week", planned work | (none) | read the "Marcus Limited" calendar and `get_firm_profile` due list | Google Calendar |

Refuse plainly: ranking, scoring or monitoring workers or tenants.
Two kinds in one question (e.g. "I'm late, draft the email"): run the specialist for the first, then draft.
