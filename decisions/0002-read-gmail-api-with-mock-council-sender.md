# 0002: Read Gmail through the API, with a mock council sender

Date: 7 Nov 2026. Status: accepted for the pilot.

## Context

Builder 1 gets many council emails with attachments per property and wants to search them (`research/interviews/builder-1.md`). We need to test reading emails and attachments end to end, without real council data.

## Decision

- Read mail with the **Gmail API**, from a Google Cloud project whose OAuth app stays in **testing mode** with Florin as the only test user. No Google app review is needed in testing mode. (To check during set-up: test-mode logins may expire after 7 days.)
- Use a **separate lab Gmail account**, not Florin's personal inbox. If a personal inbox is ever used, read only one label (e.g. `council`).
- A **mock council sender** script sends emails with mock attachments (works orders, asbestos surveys in the HSG264 layout, certificates) for fake properties, from a second account playing the council.
- The system reads the emails, extracts attachments, links each to a property, extracts asbestos items and indexes everything for search.

## Options considered

- **Email forwarding to our own inbox:** no mailbox permissions needed, works with Gmail and Outlook. Kept as a fallback, and likely for real users.
- **Full Gmail access for real users:** needs Google's restricted-scope verification and a paid security assessment. Not for the pilot.
- **Microsoft 365 (Graph API):** if Builder 1 uses Outlook. Not checked yet.

## Consequences

- Only mock data in the lab account. No real council emails until the council's consent question is answered (`research/domain/council-contracting.md`, data protection).
- The mock sender doubles as a test fixture for `tests/` and `evals/`.
