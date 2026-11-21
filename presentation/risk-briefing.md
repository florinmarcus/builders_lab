# AI risks for building firms: talking points

For the partner to present to builders. Most serious risk first. Each point: the risk, then what we do about it.
Sources: `research/market/trust-check.md` (checked 19 Nov 2026), `research/market/existing-solutions.md`,
`research/domain/asbestos.md`, `decisions/0012-language-and-voice.md`. Not legal advice.

## The risks

1. **AI says wrong things, confidently.** A missed pay less notice date, an out-of-date regulation, a guess about
   asbestos. It can cost money, a dispute or someone's health.
   - We: every fact is cited (email, sender, date; regulation, section, edition). Plain-code checks run on every
     answer before you hear it. Payment dates are worked out by code, not by the AI. If our library does not cover
     it, we say so and tell you who to ask.

2. **Free AI is public AI.** Free and personal ChatGPT or Claude can learn from your chats and give you no data
   agreement. Your clients' names, addresses and the council's papers end up there.
   - We: business plans only (Claude Team). A data processing agreement with every firm. Your data is stored
     in London and nobody trains a model on it.

3. **Your contract may forbid it.** Councils and main contractors treat you as handling their data. Many expect
   written consent before you put their papers into an outside tool (needs a legal check per contract).
   - We: tell you this on day one, list exactly where data goes (AWS London; regulation search re-ranked in
     Frankfurt, EU), and give you the paperwork to show them.

4. **The small print hands the risk back to you.** Most AI tools cap what they owe at about a year of fees. Words
   like "0% hallucination" or "fully compliant" have no test behind them. Nobody, big or small, publishes how often
   their AI is wrong.
   - We: we say "checked and cited", never "guaranteed". We publish our own test results, including what fails.

5. **Asbestos.** "No asbestos found" is only true for the rooms the survey covered. An AI that says "no asbestos"
   is dangerous.
   - We: the system is not allowed to say "no asbestos". It says what the survey covered and found; anything else
     is "treat as containing asbestos until checked".

6. **"Approved" that was not approved.** "Sounds nice, let's talk" is not a client approving a change.
   - We: a change counts as approved only when the client's own words approve it, and we quote those words.

7. **Translation mistakes.** Ordinary translation garbles building terms. A Romanian "deviz" is not a UK quote; one
   Romanian building permit is two UK regimes (planning and building regulations).
   - We: a building glossary checks the terms; official UK terms stay in English in brackets; quotes stay in the
     original English with a translation next to them.

8. **AI acting for you.** Emails and documents can contain hidden instructions. An AI that sends emails on its own
   can send the wrong thing.
   - We: emails, letters and invoices are always drafts. You check and send. Text from emails is treated as data,
     never as instructions.

9. **The person still signs.** If AI writes your RAMS, quote or notice, it is still yours.
   - We: we draft and check; a competent person in your firm signs.

## Five questions to ask any AI tool

1. Who is the company? (Look it up on Companies House.)
2. Which AI company sees my data, and where is it kept?
3. Do you train on my data?
4. Can I have your data agreement (DPA)?
5. How often is it wrong, and how do you show me the source?
