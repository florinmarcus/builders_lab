# Routing

| The builder asks about | kind | task skill (do its steps yourself) | main tools |
|---|---|---|---|
| new emails, "what came in", filing | inbox | `check-my-emails` | sync_inbox, save_facts |
| approved changes, variations, final account | variations | `variation-log` | get_job, search_job_documents |
| payment notices, pay less, applications, final date | payments | `payment-notice-check` | get_payment_dates, search_regulations |
| what's missing, handover | paperwork | `handover-missing-items` | list_missing_items, get_job |
| subcontractor papers, insurance, RAMS | paperwork | `subcontractor-pack-check` | list_missing_items, get_job |
| running late, extensions, damages, "what have I sent", who to tell | delays | `delays-advice` | get_job_timeline, get_job, search_job_documents |
| building regulations, building control, asbestos rules, CDM, the law | regulations | `regs-question` | search_regulations |
| "what's on this week", planned work | (none) | read the "Marcus Limited" calendar and `get_firm_profile` due list | Google Calendar |

Every `search_regulations` call goes through the `regs-search-plan` skill first.
Refuse plainly: ranking, scoring or monitoring workers or tenants.
Two kinds in one question (e.g. "I'm late, draft the email"): do the first task skill, then draft.
Sub-agents (`../../../agents/`) only for big jobs: see step 4 of the workflow.
