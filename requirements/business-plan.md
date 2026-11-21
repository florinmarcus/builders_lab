# Business plan (pilot), 21 Nov 2026

Agreed with Florin in a grilling session on 21 Nov 2026. Decision record: `decisions/0014-pilot-business-model.md`.
Figures marked "guess" are not checked. Open checks are at the end and in `requirements/parking-lot.md` (Q6 to Q11).

## Goal

Test cheaply whether builders will pay. Not a full business yet.

- Budget: about **£100 a month for 6 months** (about £600), plus pilot fees.
- Florin stays in his full-time job: at most about **4 hours a week**.
- **Stop rule:** at month 6, switch everything off unless at least **3 firms pay the full monthly price and use it every week**.

## The pitch

Safe AI for builders. Anyone can plug connectors into Claude; we add accuracy and compliance.

- Every answer cites its source (email, document, regulation with section and date).
- Plain-code checks on every answer (`verify_answer`); we say when we don't know.
- We say "checked and cited", never "guaranteed". Competitors cap liability and disclaim accuracy (`research/`).
- Framed as AI awareness for builders, not "buy Claude".

## Product

- **Claude only** for now. ChatGPT Business can use our MCP tools (custom connectors, beta, admin only), but not our plugin (skills, agents, answer flow). Offer it later, as "tools only", when a paying firm asks.
- Firms must use **Claude Team** (or Enterprise), not personal plans: business terms and a data processing agreement. Price: about $25 per person per month monthly, $20 yearly ([claude.com/pricing](https://claude.com/pricing), checked 18 Nov 2026).
- **Email** comes through Claude's own connectors, not ours:
  - Gmail: Claude's Gmail connector. Florin already uses it.
  - Microsoft 365: Claude's connector. Needs the firm's admin to approve it, so book their IT person for the install call.
  - Own email server: not in Standard. Large firm level only, priced as custom work.
- Our demo Gmail tool gets replaced by Claude's connectors (parking lot N18).

## Customers and prices

| Level | Who | Price |
|---|---|---|
| Pilot | 3 firms, 3 months | £100 one-off per firm |
| Standard | Any firm on Gmail or Microsoft 365 | £250 setup (install, training call, 30 days help), then **£49 a month** from month 2 |
| Pilot firms that stay | The 3 pilot firms | £39 a month for the first year |
| Large firm | Own systems, accountant links, own email server | Priced after we see what they need. Not sold until the pilot has run (about 3 months); partner meets them and collects needs meanwhile |

Prices are a starting guess to test in the pilot. Price per firm, not per person.

## Pilot agreement must cover

- We may look at their data to set up, support and improve the product.
- Feedback: a short call about every two weeks; they share requirements. Ideas belong to us, so we can build them for everyone.
- Data processing agreement: firm is controller, we are processor. What we hold, where (AWS London; re-ranking in Frankfurt, EU), how long.
- At the end, if they leave: an **Excel export** of everything we hold, then **deletion within 30 days**, confirmed in writing (parking lot N19).
- Support replies within one working day.
- An end date, and what "worked" means (used every week).
- Real pilot data never goes into Git or `system/data/mock/`.

## Legal

- A **limited company** in the partner's name (about £50 to register, guess). Florin keeps the code and **licenses** it to the company.
- **Profit split 50/50** after costs, written down. Also write: who pays costs before there is income, and what happens to the licence if either stops.
- After the pilot, if it works (changed 21 Nov 2026; was "before the first paying firm"): **cyber insurance** (a leak) and **professional indemnity** (a wrong answer). Our liability is **capped at 12 months' fees** in our terms.
- Florin's task: check his employment contract for side work and code ownership.
- Anthropic's own liability is probably capped low; insurance is the real cover (Q7).

## Roles

- **Partner:** finds customers, sells, does setup with a help sheet, answers all first questions. Asks every firm early: "Where is your email?" and "Who manages your IT?"
- **Florin:** product and technical problems only, within one working day, at most about 4 hours a week.

## Costs per month (estimate)

**Cloud, now: about £20 to £30 a month.** Updated 21 Nov 2026 (Florin): company, accountant and insurance are decided after the pilot.

| Item | £ a month | Note |
|---|---|---|
| London server (EC2 t4g.small) | about 16 | $20.15 (`research/hosting-costs/`); about 27 on t4g.medium (4 GB), needed for the corpus (N17) |
| Regulations database | 0 extra | Moves from the Frankfurt lab RDS onto the London server (N17); the RDS costs until it is switched off |
| Bedrock embedding and re-ranking | under 1 | Demo volumes |
| Logs, secrets, backups | 2 to 3 | Guess |

**When the pilots start, it goes up:** real emails and documents, more questions, more backups. Guess: about £40 to £60 a month. Still under the £100 budget.

**Later, after the pilot (if it works):** limited company (about £50 once), accountant (£500 to £1,000 a year), cyber and PI insurance (£300 to £800 a year), ICO fee (about £52 a year). All guesses.

**Spent so far:** not known here; check AWS Billing. The server's budget alarm is set at $30 a month.

No API Gateway needed: Caddy and per-firm API keys already do that job (ADR 0007). No model on our server (ADR 0006).

**Income:** pilot £300. Three Standard firms at £49 roughly cover £100 a month; 5 to 10 firms give a small profit.

## Open checks

- Server memory for the corpus on the London server (N17).
- Anthropic's liability cap and data terms for Claude Team (Q7).
- ChatGPT Business and Enterprise prices from OpenAI's own page (Q8).
- Claude's Microsoft 365 connector covers Outlook mail (Q9).
- Companies House and ICO fees (Q10).
- Real insurance and accountant quotes (Q11).

Sources for ChatGPT figures (third party, not OpenAI): [Pareto Talent](https://paretotalent.com/guides/chatgpt-for-business/), [CloudZero](https://www.cloudzero.com/blog/chatgpt-enterprise-pricing/), [OpenAI help: MCP connectors](https://help.openai.com/en/articles/12584461-developer-mode-apps-and-full-mcp-connectors-in-chatgpt).
