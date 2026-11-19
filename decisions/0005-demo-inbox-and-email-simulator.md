# 0005: Demo uses the builder's own Gmail, a label, and a live email simulator

Date: 19 Nov 2026. Status: accepted for the demo. Replaces the "separate lab account" and "second sender account" parts of ADR 0002.

## Context

The demo on 21 Nov must be repeatable: reset, run again, same result. The audience must see emails arrive live, from a customer, an employee or the council. Florin does not want new email accounts.

## Decision

- The builder's inbox is Florin's own Gmail. A second address he owns sends the live emails.
- The persona is picked by plus-addressing: `<inbox>+council@gmail.com`, `+sarah`, `+mike` and so on. Gmail delivers these to the normal inbox.
- A simulator script picks up emails from allowed senders only, re-imports each with the persona as sender (Gmail API `messages.import`), and deletes the original.
- Past mock emails are loaded with `messages.import` too, which keeps their dates.
- Every mock or simulated email and every demo draft carries one label, `oakline-demo`. Reset deletes only that label's content, empties the database and reloads.
- Addresses live in `.env`, never in the repo.

## Options considered

- Separate lab Gmail account (ADR 0002): cleaner isolation, but Florin prefers his own inbox.
- Real sending from a second account with no rewrite: Gmail and Claude would show the real sender, not the persona.
- Subject tags like `[council]` instead of plus-addresses: works, but easier to forget on stage.

## Consequences

- Our code reads a personal inbox. It must only touch the label and the allowed senders. Scopes: `gmail.modify` (import, label, delete). Google OAuth stays in testing mode.
- The rewrite takes a few seconds; on stage, send, then ask.
- Claude's Gmail connector sees the whole inbox, not just the label. Fine for the demo; not acceptable for real use.
